"""
Court Vision AI — Case Intelligence Chat Route

POST /api/cases/{case_id}/chat
  - Accepts conversation history for multi-turn context
  - Extracts text from all READY documents via PyMuPDF
  - Sends grounded context + history + new question to Groq
  - Returns { answer, sources, model, tokens_used, has_documents }

POST /api/cases/{case_id}/chat/stream
  - Same as above but streams tokens via Server-Sent Events (SSE)
  - Yields partial text chunks and a final [DONE] event with sources+model

GET /api/cases/{case_id}/summary
  - Generates a structured intelligence summary of the case documents
  - Returns structured { overview, key_issues, important_facts, important_dates,
                         evidence, potential_weaknesses, recommended_next_steps }
"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_storage
from app.core.config import get_settings
from app.models.document import Document, DocumentStatus
from app.schemas.document import UserContext
from app.services.case_service import CaseService
from app.storage.local import StorageService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Chat"])


# ── Groq client factory (defensive — handles old httpx proxy arg issue) ─────────

def _get_groq_client():
    """
    Instantiate the Groq client defensively to handle older SDK/httpx combinations
    that pass an unexpected 'proxies' argument to the httpx.Client constructor.
    """
    # ── Temporary safe debug logging (never logs actual API key) ──
    logger.info(
        "[Groq Debug] model=%s | api_key_exists=%s | base_url=%s",
        settings.GROQ_MODEL,
        bool(settings.GROQ_API_KEY),
        "https://api.groq.com/openai/v1",
    )
    try:
        from groq import Groq
        return Groq(api_key=settings.GROQ_API_KEY, timeout=30.0, max_retries=0)
    except TypeError as e:
        if "proxies" in str(e):
            # Workaround: monkey-patch httpx.Client to ignore 'proxies'
            import httpx
            _orig_init = httpx.Client.__init__
            def _patched_init(self, *args, **kwargs):
                kwargs.pop("proxies", None)
                _orig_init(self, *args, **kwargs)
            httpx.Client.__init__ = _patched_init

            _orig_async_init = httpx.AsyncClient.__init__
            def _patched_async_init(self, *args, **kwargs):
                kwargs.pop("proxies", None)
                _orig_async_init(self, *args, **kwargs)
            httpx.AsyncClient.__init__ = _patched_async_init

            from groq import Groq
            return Groq(api_key=settings.GROQ_API_KEY, timeout=30.0, max_retries=0)
        raise


CHAT_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]


def _call_groq_chat_resilient(client, messages: list[dict], max_tokens: int = 2048, temperature: float = 0.2):
    models = []
    if settings.GROQ_MODEL and settings.GROQ_MODEL not in CHAT_MODELS:
        models.append(settings.GROQ_MODEL)
    models.extend(CHAT_MODELS)

    last_err = None
    for model in models:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = (resp.choices[0].message.content or "").strip()
            if content:
                return resp, content, model
        except Exception as e:
            logger.warning(f"[Chat] Groq model '{model}' failed: {e}")
            last_err = e
            continue
    raise last_err or RuntimeError("All chat models failed.")


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ConversationTurn] = []


class ChatSource(BaseModel):
    document_id: str
    document_name: str
    excerpt: str
    page_hint: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    model: str
    tokens_used: int | None = None
    has_documents: bool


class CaseSummaryResponse(BaseModel):
    overview: str
    key_issues: list[str]
    important_facts: list[str]
    important_dates: list[str]
    evidence: list[str]
    potential_weaknesses: list[str]
    recommended_next_steps: list[str]
    has_documents: bool


# ── System Prompt ─────────────────────────────────────────────────────────────

LEGAL_SYSTEM_PROMPT_TEMPLATE = """You are Court Vision AI — a specialized legal case intelligence assistant for advocates, lawyers, and legal researchers.

You have been provided the full text of the case documents below. Your entire analysis must be grounded in these documents.

═══════════════════════════════════════════════════════
CASE DOCUMENTS
═══════════════════════════════════════════════════════
{docs_block}
═══════════════════════════════════════════════════════

ROLE & CONTEXT:
You are assisting a legal professional who has uploaded these documents to their case workspace. They need clear, actionable, legally-aware intelligence — not generic AI conversation.

RESPONSE FORMAT RULES:
1. Always use structured formatting with clear sections
2. Use **bold** for critical facts, party names, and legal terms
3. Use numbered lists for sequential items (timelines, steps, arguments)
4. Use bullet points (–) for non-sequential items
5. Use section headers with ## for multi-part responses
6. At the end of each factual claim drawn from documents, cite the source inline: *(Source: [Document Name])*
7. For legal weaknesses, arguments, or analysis — always end with a "**Recommended Action:**" line
8. Keep responses scannable — avoid large unbroken paragraphs

WHAT YOU MUST DO:
– Answer based ONLY on what is in the case documents above
– Maintain full context of the conversation history
– When the advocate refers to "that point" or "weakness #2", trace back to the prior conversation
– If a question cannot be answered from the documents, say: "This information is not available in the uploaded documents."
– Never fabricate facts, witnesses, dates, statutes, or case references
– Be precise and professional — you are assisting trained legal professionals

WHAT YOU MUST NOT DO:
– Do not give generic legal advice unrelated to these specific documents
– Do not make up document page numbers unless you can infer them
– Do not use casual or conversational language
– Do not fabricate case outcomes or legal precedents"""


SUMMARY_SYSTEM_PROMPT_TEMPLATE = """You are Court Vision AI — a specialized legal case intelligence assistant.

You have been provided the full text of the case documents below. Generate a structured intelligence summary.

═══════════════════════════════════════════════════════
CASE DOCUMENTS
═══════════════════════════════════════════════════════
{docs_block}
═══════════════════════════════════════════════════════

Generate a JSON response ONLY — no other text, no markdown fencing — with exactly this structure:
{{
  "overview": "2-4 sentence overview of what this case is about",
  "key_issues": ["Issue 1", "Issue 2", "Issue 3"],
  "important_facts": ["Fact 1", "Fact 2", "Fact 3"],
  "important_dates": ["Date: Event 1", "Date: Event 2"],
  "evidence": ["Evidence 1", "Evidence 2"],
  "potential_weaknesses": ["Weakness 1", "Weakness 2"],
  "recommended_next_steps": ["Step 1", "Step 2", "Step 3"]
}}

Rules:
- Base every item on actual document content
- Each list should have 2-5 items
- If information is not available, return an empty list []
- Return ONLY valid JSON, nothing else"""


def _extract_text_from_pdf(file_path: str, max_chars: int = 20000) -> tuple[str, int]:
    """Extract text from a PDF, capped at max_chars. Returns (text, page_count)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pages = len(doc)
        text_parts = []
        total = 0
        for page in doc:
            t = page.get_text()
            if total + len(t) > max_chars:
                text_parts.append(t[: max_chars - total])
                total = max_chars
                break
            text_parts.append(t)
            total += len(t)
        doc.close()
        return "\n".join(text_parts).strip(), pages
    except Exception as e:
        logger.warning(f"PDF text extraction failed for {file_path}: {e}")
        return "", 0


def _build_source_citations(message: str, case_context: list[dict]) -> list[ChatSource]:
    """Find relevant excerpts from documents based on query keywords."""
    sources = []
    keywords = set(w.lower() for w in message.split() if len(w) > 4)

    for ctx in case_context:
        text = ctx["text"]
        if not text:
            continue

        # Find the most keyword-dense 250-char window
        best_pos = 0
        best_score = 0
        chunk_size = 60
        for i in range(0, len(text) - chunk_size, chunk_size // 2):
            chunk = text[i: i + chunk_size].lower()
            score = sum(1 for kw in keywords if kw in chunk)
            if score > best_score:
                best_score = score
                best_pos = max(0, i - 50)

        excerpt = text[best_pos: best_pos + 250].strip()
        excerpt = excerpt.replace("\n", " ").replace("  ", " ")
        if len(excerpt) >= 248:
            excerpt = excerpt[:248] + "…"

        if excerpt:
            sources.append(
                ChatSource(
                    document_id=ctx["id"],
                    document_name=ctx["name"],
                    excerpt=excerpt,
                    page_hint=f"{ctx['pages']} pages" if ctx.get("pages") else None,
                )
            )
    return sources


def _load_case_context(
    case_id: str,
    db: Session,
    store: StorageService,
    per_doc_limit: int | None = None,
) -> list[dict]:
    """Shared helper: load text from all READY docs for a case."""
    docs = (
        db.query(Document)
        .filter(Document.case_id == case_id, Document.status == DocumentStatus.READY)
        .order_by(Document.uploaded_at.asc())
        .all()
    )

    if not docs:
        return []

    limit = per_doc_limit or max(4000, settings.MAX_CONTEXT_CHARS // max(len(docs), 1))
    case_context: list[dict] = []
    for doc in docs:
        local_path = store.get_local_path(doc.storage_path)
        if not Path(local_path).exists():
            logger.warning(f"Document file missing on disk: {local_path}")
            continue
        text, pages = _extract_text_from_pdf(local_path, max_chars=limit)
        if text:
            case_context.append(
                {
                    "id": doc.id,
                    "name": doc.original_name,
                    "text": text,
                    "pages": pages or doc.page_count or 0,
                }
            )
    return case_context


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/cases/{case_id}/chat",
    response_model=ChatResponse,
    summary="Ask a question about the case documents",
)
def chat_with_case(
    case_id: str,
    body: ChatRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    store: StorageService = Depends(get_storage),
):
    """
    Multi-turn AI chat grounded in case documents.
    Accepts full conversation history for context retention across follow-up questions.
    """
    if not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty.",
        )

    # Verify case ownership / access
    CaseService(db).get_case(case_id=case_id, user_id=current_user.id)

    case_context = _load_case_context(case_id, db, store)
    has_documents = len(case_context) > 0

    if not has_documents:
        return ChatResponse(
            answer=(
                "No documents are ready for analysis in this case yet.\n\n"
                "Upload your case documents using the **Documents** panel on the left, "
                "and wait for their status to show **Ready** before asking questions."
            ),
            sources=[],
            model="none",
            has_documents=False,
        )

    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Add GROQ_API_KEY to backend/.env",
        )

    # Build document context block for the system prompt
    docs_block = ""
    for i, ctx in enumerate(case_context, 1):
        docs_block += (
            f"\n--- DOCUMENT {i}: {ctx['name']} ({ctx['pages']} pages) ---\n"
            f"{ctx['text']}\n"
        )

    system_prompt = LEGAL_SYSTEM_PROMPT_TEMPLATE.format(docs_block=docs_block)

    # Build messages array: system + history + new user message
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for turn in body.conversation_history:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": body.message.strip()})

    try:
        client = _get_groq_client()
        completion, answer, used_model = _call_groq_chat_resilient(
            client, messages, max_tokens=settings.GROQ_MAX_TOKENS, temperature=0.2
        )
        import re as _re
        answer = _re.sub(r'<think>.*?</think>', '', answer, flags=_re.DOTALL).strip()
        tokens_used = completion.usage.total_tokens if completion.usage else None

    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        try:
            from groq import APIStatusError
            if isinstance(e, APIStatusError):
                status_code = e.status_code
                if status_code == 401:
                    detail = "AI service authentication error"
                elif status_code == 403:
                    detail = "AI service permission error"
                elif status_code == 404:
                    detail = "AI service model/resource error"
                elif status_code == 429:
                    detail = "AI service rate limit exceeded"
                elif status_code >= 500:
                    detail = f"Upstream AI service error: {e.message}"
                else:
                    detail = f"AI service error: {e.message}"
                raise HTTPException(status_code=status_code, detail=detail)
        except ImportError:
            pass

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {str(e)}",
        )

    sources = _build_source_citations(body.message, case_context)

    return ChatResponse(
        answer=answer,
        sources=sources,
        model=settings.GROQ_MODEL,
        tokens_used=tokens_used,
        has_documents=True,
    )


@router.get(
    "/cases/{case_id}/summary",
    response_model=CaseSummaryResponse,
    summary="Generate a structured intelligence summary of the case documents",
)
def get_case_summary(
    case_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    store: StorageService = Depends(get_storage),
):
    """
    Generates a one-shot structured intelligence summary for the Case Snapshot panel.
    Uses the same document pipeline as chat, no extra processing needed.
    """
    CaseService(db).get_case(case_id=case_id, user_id=current_user.id)

    case_context = _load_case_context(case_id, db, store, per_doc_limit=15000)

    if not case_context:
        return CaseSummaryResponse(
            overview="No documents have been processed for this case yet.",
            key_issues=[],
            important_facts=[],
            important_dates=[],
            evidence=[],
            potential_weaknesses=[],
            recommended_next_steps=["Upload case documents to begin analysis."],
            has_documents=False,
        )

    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured.",
        )

    docs_block = ""
    for i, ctx in enumerate(case_context, 1):
        docs_block += (
            f"\n--- DOCUMENT {i}: {ctx['name']} ({ctx['pages']} pages) ---\n"
            f"{ctx['text']}\n"
        )

    system_prompt = SUMMARY_SYSTEM_PROMPT_TEMPLATE.format(docs_block=docs_block)

    try:
        import json
        client = _get_groq_client()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the case intelligence summary JSON now."},
        ]
        _, raw, _ = _call_groq_chat_resilient(client, messages, max_tokens=1500, temperature=0.1)

        # Strip any markdown code fences and <think> blocks robustly
        import re as _re
        raw = _re.sub(r'<think>.*?</think>', '', raw, flags=_re.DOTALL).strip()
        raw = _re.sub(r'^```(?:json|JSON)?\s*\n?', '', raw)
        raw = _re.sub(r'\n?```\s*$', '', raw)
        raw = raw.strip()

        data = json.loads(raw)

        return CaseSummaryResponse(
            overview=data.get("overview", ""),
            key_issues=data.get("key_issues", []),
            important_facts=data.get("important_facts", []),
            important_dates=data.get("important_dates", []),
            evidence=data.get("evidence", []),
            potential_weaknesses=data.get("potential_weaknesses", []),
            recommended_next_steps=data.get("recommended_next_steps", []),
            has_documents=True,
        )

    except Exception as e:
        logger.error(f"Summary generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Case summary could not be generated: {str(e)[:200]}",
        )


# ── Streaming Chat ────────────────────────────────────────────────────────────

@router.post(
    "/cases/{case_id}/chat/stream",
    summary="Streaming AI chat — tokens delivered via Server-Sent Events",
)
def chat_with_case_stream(
    case_id: str,
    body: ChatRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    store: StorageService = Depends(get_storage),
):
    """
    Same as the regular chat endpoint but delivers the answer as a stream
    of Server-Sent Events so the UI can display tokens progressively.

    SSE event format:
      data: {"type":"token",  "content":"<partial text>"}
      data: {"type":"done",   "sources":[...], "model":"<model>", "answer":"<full>"}
      data: {"type":"error",  "message":"<error text>"}
    """
    if not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty.",
        )

    CaseService(db).get_case(case_id=case_id, user_id=current_user.id)

    case_context = _load_case_context(case_id, db, store)
    has_documents = len(case_context) > 0

    if not has_documents:
        _no_doc_msg = "No documents are ready for analysis in this case yet.\n\nUpload your case documents using the **Documents** panel on the left, and wait for their status to show **Ready** before asking questions."
        _token_event = "data: " + json.dumps({"type": "token", "content": _no_doc_msg}) + "\n\n"
        _done_event  = "data: " + json.dumps({"type": "done", "sources": [], "model": "none", "answer": ""}) + "\n\n"

        async def no_docs_stream():
            yield _token_event
            yield _done_event
        return StreamingResponse(no_docs_stream(), media_type="text/event-stream")

    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Add GROQ_API_KEY to backend/.env",
        )

    docs_block = ""
    for i, ctx in enumerate(case_context, 1):
        docs_block += (
            f"\n--- DOCUMENT {i}: {ctx['name']} ({ctx['pages']} pages) ---\n"
            f"{ctx['text']}\n"
        )

    system_prompt = LEGAL_SYSTEM_PROMPT_TEMPLATE.format(docs_block=docs_block)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for turn in body.conversation_history:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": body.message.strip()})

    # Pre-compute source citations (keyword-based, instant)
    sources = _build_source_citations(body.message, case_context)
    sources_data = [s.model_dump() for s in sources]

    def _generate():
        """Generator: yields SSE lines. Runs in the request thread."""
        full_answer = []
        models = []
        if settings.GROQ_MODEL and settings.GROQ_MODEL not in CHAT_MODELS:
            models.append(settings.GROQ_MODEL)
        models.extend(CHAT_MODELS)

        stream = None
        client = _get_groq_client()
        used_model = models[0]

        for m in models:
            try:
                stream = client.chat.completions.create(
                    model=m,
                    messages=messages,
                    max_tokens=settings.GROQ_MAX_TOKENS,
                    temperature=0.2,
                    stream=True,
                )
                used_model = m
                break
            except Exception as e:
                logger.warning(f"[Stream] Groq model '{m}' failed: {e}")
                continue

        if not stream:
            yield f'data: {json.dumps({"type": "error", "message": "AI service temporarily unavailable. Please retry in a moment."})}\n\n'
            return

        try:
            for chunk in stream:
                delta = chunk.choices[0].delta
                token = getattr(delta, "content", None) or ""
                if token:
                    full_answer.append(token)
                    yield f'data: {json.dumps({"type": "token", "content": token})}\n\n'

            answer = "".join(full_answer)
            yield f'data: {json.dumps({"type": "done", "sources": sources_data, "model": used_model, "answer": answer})}\n\n'

        except Exception as e:
            logger.error(f"[Stream] Groq error: {e}", exc_info=True)
            yield f'data: {json.dumps({"type": "error", "message": f"AI service error: {str(e)}"})}\n\n'

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
