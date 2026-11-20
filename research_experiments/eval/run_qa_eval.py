"""
Experiment 4 — Grounded legal QA evaluation of Court Vision AI.

Systems compared (same LLM, same temperature, model pinned — no fallback):
  S1  CV-Trunc      : production Court Vision pipeline. Uses the real
                      LEGAL_SYSTEM_PROMPT_TEMPLATE and _load_case_context()
                      logic (text truncated at MAX_CONTEXT_CHARS = 18,000).
  S2  CV-RAG        : proposed method. Full document is split into
                      page-tagged chunks, BM25 retrieves top-k chunks, which
                      are placed in the same legal system prompt.
  S3  Closed-book   : same LLM, no documents (parametric knowledge only).
  S4  BM25-Extract  : no LLM. Returns the single best BM25 chunk as the answer.

Run from backend/ so app settings (.env) resolve:
    cd backend && ./venv/Scripts/python.exe ../research_experiments/eval/run_qa_eval.py
Results are appended to results/qa_results.jsonl (resumable).
"""
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[1] / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(HERE))

from app.core.config import get_settings                      # noqa: E402
from app.api.routes.chat import (                              # noqa: E402
    LEGAL_SYSTEM_PROMPT_TEMPLATE,
    _extract_text_from_pdf,
    _get_groq_client,
)
from qa_set import QA                                          # noqa: E402

settings = get_settings()
MODEL = "openai/gpt-oss-120b"
TEMPERATURE = 0.2
MAX_TOKENS = settings.GROQ_MAX_TOKENS
PDF = BACKEND / "storage/documents/7205352d-9ee1-45c8-8ce5-ba96a597f9d7/fb8c9db7-b262-42b7-8e59-dfe0a8754491.pdf"
DOC_NAME = "Jacob_Mathew_vs_State_Of_Punjab_&_Anr_on_5_August,_2005.pdf"
OUT = HERE / "results" / "qa_results.jsonl"
OUT.parent.mkdir(exist_ok=True)

CHUNK_CHARS = 1000
CHUNK_OVERLAP = 200
TOP_K = 6

client = _get_groq_client()


# ── Document preparation ──────────────────────────────────────────────────────

def production_context() -> tuple[str, int]:
    """Exactly what chat.py builds for a single-document case."""
    limit = max(4000, settings.MAX_CONTEXT_CHARS // 1)
    text, pages = _extract_text_from_pdf(str(PDF), max_chars=limit)
    docs_block = f"\n--- DOCUMENT 1: {DOC_NAME} ({pages} pages) ---\n{text}\n"
    return docs_block, len(text)


_BOILERPLATE = re.compile(r"^(Jacob Mathew vs State Of Punjab & Anr on 5 August, 2005|Indian Kanoon - http\S+|\d{1,2})\s*$")


def page_chunks() -> list[dict]:
    import fitz
    doc = fitz.open(str(PDF))
    chunks = []
    for pno, page in enumerate(doc, start=1):
        lines = [ln for ln in page.get_text().splitlines() if not _BOILERPLATE.match(ln.strip())]
        text = re.sub(r"\s+", " ", " ".join(lines)).strip()
        start = 0
        while start < len(text):
            chunks.append({"page": pno, "text": text[start:start + CHUNK_CHARS]})
            if start + CHUNK_CHARS >= len(text):
                break
            start += CHUNK_CHARS - CHUNK_OVERLAP
    doc.close()
    return chunks


_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = set("""a an the of to in on for and or is are was were be by with as at from that this which
what who whom whose when where how did does do it its into than then there their they he she his her
under according should must can could would per""".split())


def tokenize(s: str) -> list[str]:
    return [t for t in _TOKEN.findall(s.lower()) if t not in _STOP]


class BM25:
    """Okapi BM25 (k1=1.5, b=0.75)."""

    def __init__(self, docs: list[list[str]], k1=1.5, b=0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.avgdl = sum(map(len, docs)) / len(docs)
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in docs]

    def scores(self, q: list[str]) -> list[float]:
        out = []
        for d, tf in zip(self.docs, self.tf):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avgdl))
            out.append(s)
        return out


CHUNKS = page_chunks()
INDEX = BM25([tokenize(c["text"]) for c in CHUNKS])


def retrieve(q: str, k: int) -> list[dict]:
    sc = INDEX.scores(tokenize(q))
    top = sorted(range(len(CHUNKS)), key=lambda i: -sc[i])[:k]
    return [dict(CHUNKS[i], score=round(sc[i], 3), idx=i) for i in sorted(top)]  # keep document order


# ── LLM call with rate-limit handling (model pinned) ─────────────────────────

def call_llm(messages: list[dict]) -> dict:
    for attempt in range(12):
        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
            )
            latency = time.perf_counter() - t0
            content = (resp.choices[0].message.content or "").strip()
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            u = resp.usage
            return dict(answer=content, latency_s=round(latency, 3),
                        prompt_tokens=getattr(u, "prompt_tokens", None),
                        completion_tokens=getattr(u, "completion_tokens", None),
                        attempts=attempt + 1)
        except Exception as e:  # 429 / transient
            msg = str(e)
            wait = 20
            m = re.search(r"try again in ((?:\d+h)?(?:\d+m(?!s))?(?:[\d.]+(?:ms|s))?)", msg)
            if m and m.group(1):
                t = m.group(1)
                h = re.search(r"(\d+)h", t); mi = re.search(r"(\d+)m(?!s)", t)
                s = re.search(r"([\d.]+)s", t); ms = re.search(r"([\d.]+)ms", t)
                wait = (int(h.group(1)) * 3600 if h else 0) + (int(mi.group(1)) * 60 if mi else 0) \
                    + (float(ms.group(1)) / 1000 if ms else float(s.group(1)) if s else 0) + 1.5
            print(f"    retry {attempt + 1} after {wait:.1f}s: {msg[:120]}", flush=True)
            time.sleep(wait)
    return dict(answer="", error="exhausted retries", latency_s=None)


# ── Systems ───────────────────────────────────────────────────────────────────

PROD_BLOCK, PROD_CHARS = production_context()


def s1_cv_trunc(q: str) -> dict:
    sys_prompt = LEGAL_SYSTEM_PROMPT_TEMPLATE.format(docs_block=PROD_BLOCK)
    r = call_llm([{"role": "system", "content": sys_prompt}, {"role": "user", "content": q}])
    r["context_chars"] = PROD_CHARS
    return r


def s2_cv_rag(q: str) -> dict:
    hits = retrieve(q, TOP_K)
    block = f"\n--- DOCUMENT 1: {DOC_NAME} (20 pages) — retrieved excerpts ---\n"
    block += "\n".join(f"[Page {h['page']}] {h['text']}" for h in hits) + "\n"
    sys_prompt = LEGAL_SYSTEM_PROMPT_TEMPLATE.format(docs_block=block) + (
        "\n\nCITATION RULE: the excerpts are tagged [Page N]. Cite the page for every factual claim, "
        "e.g. *(Source: [Document Name], p. N)*. If the excerpts do not contain the answer, reply exactly: "
        "\"This information is not available in the uploaded documents.\""
    )
    r = call_llm([{"role": "system", "content": sys_prompt}, {"role": "user", "content": q}])
    r["context_chars"] = sum(len(h["text"]) for h in hits)
    r["retrieved_pages"] = [h["page"] for h in hits]
    return r


CLOSED_PROMPT = (
    "You are a legal research assistant specialised in Indian law. The user is asking about the "
    "Supreme Court of India judgment Jacob Mathew v. State of Punjab & Anr. (decided 5 August 2005). "
    "Answer precisely and concisely. If you do not know the answer, say that the information is not available."
)


def s3_closed_book(q: str) -> dict:
    r = call_llm([{"role": "system", "content": CLOSED_PROMPT}, {"role": "user", "content": q}])
    r["context_chars"] = 0
    return r


def s4_bm25_extract(q: str) -> dict:
    t0 = time.perf_counter()
    sc = INDEX.scores(tokenize(q))
    best = max(range(len(CHUNKS)), key=lambda i: sc[i])
    return dict(answer=CHUNKS[best]["text"], latency_s=round(time.perf_counter() - t0, 4),
                retrieved_pages=[CHUNKS[best]["page"]], context_chars=len(CHUNKS[best]["text"]),
                prompt_tokens=0, completion_tokens=0)


SYSTEMS = {"S1_CV_Trunc": s1_cv_trunc, "S2_CV_RAG": s2_cv_rag,
           "S3_ClosedBook": s3_closed_book, "S4_BM25_Extract": s4_bm25_extract}


def main():
    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("answer") or r["system"] == "S4_BM25_Extract":
                done.add((r["system"], r["qid"]))
    print(f"Production context: {PROD_CHARS} chars | chunks: {len(CHUNKS)} | model: {MODEL} | max_tokens: {MAX_TOKENS}")
    order = ["S4_BM25_Extract", "S3_ClosedBook", "S2_CV_RAG", "S1_CV_Trunc"]
    with OUT.open("a", encoding="utf-8") as f:
        for name in order:
            for item in QA:
                if (name, item["id"]) in done:
                    continue
                print(f"[{name}] {item['id']} {item['q'][:70]}", flush=True)
                r = SYSTEMS[name](item["q"])
                r.update(system=name, qid=item["id"], question=item["q"])
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
    print("DONE")


if __name__ == "__main__":
    main()
