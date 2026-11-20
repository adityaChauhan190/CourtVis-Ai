"""
Court Vision AI — shared LLM access (Groq).

One place for: client creation, the model fallback chain, waiting out 429 rate limits,
JSON mode, and parsing JSON that the model returned truncated or wrapped in prose.
"""
import json
import logging
import os
import re
import time

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FALLBACK_MODELS = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
MAX_RATE_LIMIT_WAIT_S = 45  # never block a request longer than this on one 429
# Groq counts prompt + max_tokens against the per-minute token limit (8,000 on the free tier);
# a request above it is refused outright (413), so max_tokens is clamped to fit.
TPM_BUDGET = int(os.getenv("GROQ_TPM_LIMIT", "8000"))


class LLMError(RuntimeError):
    """Every model in the chain failed."""


_client = None


def get_client():
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise LLMError("AI service not configured. Add GROQ_API_KEY to backend/.env")
        from groq import Groq
        _client = Groq(api_key=settings.GROQ_API_KEY, timeout=60.0, max_retries=0)
    return _client


def _models() -> list[str]:
    models = [settings.GROQ_MODEL] if settings.GROQ_MODEL else []
    return models + [m for m in FALLBACK_MODELS if m not in models]


def _retry_after(err: Exception) -> float | None:
    """Seconds Groq asks us to wait on a per-minute 429; None for daily limits / other errors."""
    msg = str(err)
    if "429" not in msg or "tokens per day" in msg or "requests per day" in msg:
        return None
    m = re.search(r"try again in (?:(\d+)m)?([\d.]+)(ms|s)", msg)
    if not m:
        return 5.0
    wait = int(m.group(1) or 0) * 60 + float(m.group(2)) / (1000 if m.group(3) == "ms" else 1)
    return wait + 0.5


def strip_think(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    return re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()


def chat(messages: list[dict], *, max_tokens: int = 2048, temperature: float = 0.2,
         json_mode: bool = False, reasoning: str = "low") -> tuple[str, str, str]:
    """Return (content, model, finish_reason). Tries each model; waits out short 429s."""
    client = get_client()
    est_prompt = sum(len(str(m.get("content", ""))) for m in messages) // 3 + 50
    if est_prompt + max_tokens > TPM_BUDGET - 200:
        max_tokens = max(600, TPM_BUDGET - 200 - est_prompt)
    last_err: Exception | None = None
    for model in _models():
        for _attempt in range(3):
            kwargs = dict(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            if model.startswith("openai/gpt-oss"):
                kwargs["extra_body"] = {"reasoning_effort": reasoning}  # "low" keeps the budget for the answer
            try:
                resp = client.chat.completions.create(**kwargs)
                choice = resp.choices[0]
                content = strip_think(choice.message.content or "")
                if content:
                    return content, model, choice.finish_reason or ""
                last_err = LLMError(f"{model} returned empty content")
                break
            except Exception as e:  # noqa: BLE001 — try the next model
                # JSON mode rejected an answer over a small syntax slip: keep the model's own text and repair it
                body = getattr(e, "body", None)
                err = body.get("error", body) if isinstance(body, dict) else {}
                if isinstance(err, dict) and err.get("code") == "json_validate_failed" and err.get("failed_generation"):
                    logger.info(f"[LLM] {model} JSON had a syntax slip; repairing its output")
                    return str(err["failed_generation"]), model, "json_repaired"
                last_err = e
                wait = _retry_after(e)
                if wait is not None and wait <= MAX_RATE_LIMIT_WAIT_S:
                    logger.info(f"[LLM] {model} rate-limited, waiting {wait:.1f}s")
                    time.sleep(wait)
                    continue
                logger.warning(f"[LLM] {model} failed: {e}")
                break
    raise LLMError(f"All AI models failed: {last_err}")


def parse_json(text: str):
    """Parse model JSON: direct, fenced, wrapped in prose, or truncated mid-object.

    For truncated output every complete {...} object at any nesting depth is salvaged
    and returned as {"_salvaged": [objects]} so callers can classify them.
    """
    text = strip_think(text)
    text = re.sub(r'"\s*::\s*', '": ', text)            # "key":: value
    text = re.sub(r",\s*([}\]])", r"\1", text)       # trailing commas
    text = re.sub(r"^```(?:json|JSON)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        i, j = text.find(open_c), text.rfind(close_c)
        if i != -1 and j > i:
            try:
                return json.loads(text[i:j + 1])
            except Exception:
                pass
    # Truncated: salvage complete objects at any depth (brace stack, string-aware)
    stack, in_str, esc, found = [], False, False, []
    for i, ch in enumerate(text):
        if esc:
            esc = False
            continue
        if ch == "\\" and in_str:
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            stack.append(i)
        elif ch == "}" and stack:
            start = stack.pop()
            try:
                obj = json.loads(text[start:i + 1])
            except Exception:
                continue
            if isinstance(obj, dict):
                found.append(obj)
    if found:
        return {"_salvaged": found}
    raise ValueError("No JSON found in model output")


def chat_json(messages: list[dict], *, max_tokens: int = 3000, temperature: float = 0.2, reasoning: str = "low"):
    """chat() in JSON mode + parse_json(). Returns (data, model, finish_reason)."""
    try:
        content, model, finish = chat(messages, max_tokens=max_tokens, temperature=temperature, json_mode=True, reasoning=reasoning)
    except LLMError:
        # Some fallback models reject response_format; retry the chain without it.
        content, model, finish = chat(messages, max_tokens=max_tokens, temperature=temperature, json_mode=False, reasoning=reasoning)
    if finish == "length":
        logger.warning(f"[LLM] {model} hit max_tokens={max_tokens}; output may be truncated")
    return parse_json(content), model, finish
