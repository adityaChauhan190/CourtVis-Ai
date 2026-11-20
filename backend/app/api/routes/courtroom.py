"""
Court Vision AI — Virtual Courtroom Route

POST /api/cases/{case_id}/courtroom
  - Accepts a lawyer's statement + session history + judge temperament
  - AI simultaneously plays The Judge and Opposing Counsel
  - Both roles respond based on actual case documents
  - Returns { judge_response, opposing_response, phase, turn_number }

POST /api/cases/{case_id}/courtroom/verdict
  - Ends the session and requests a final judicial verdict + Junior Lawyer Performance Scorecard
  - Returns { verdict, outcome, reasoning, key_findings, scorecard }
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(tags=["Courtroom"])

COURTROOM_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]


# ── Groq client ──────────────────────────────────────────────────────────────

def _get_groq_client():
    try:
        from groq import Groq
        return Groq(api_key=settings.GROQ_API_KEY, timeout=35.0, max_retries=0)
    except TypeError as e:
        if "proxies" in str(e):
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
            return Groq(api_key=settings.GROQ_API_KEY, timeout=35.0, max_retries=0)
        raise


def _call_groq_resilient(client, messages: list[dict], max_tokens: int = 900, temperature: float = 0.4) -> str:
    """Call Groq with automatic model fallback sequence to prevent 502 / 429 rate limit issues."""
    models_to_try = []
    if settings.GROQ_MODEL and settings.GROQ_MODEL not in COURTROOM_MODELS:
        models_to_try.append(settings.GROQ_MODEL)
    models_to_try.extend(COURTROOM_MODELS)

    last_err = None
    for model in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            raw = (completion.choices[0].message.content or "").strip()
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            raw = re.sub(r'<think>.*$', '', raw, flags=re.DOTALL).strip()
            if raw:
                return raw
        except Exception as e:
            logger.warning(f"[Courtroom] Groq model '{model}' failed: {e}")
            last_err = e
            continue

    raise last_err or RuntimeError("All Groq fallback models failed.")


# ── Text extraction helper ───────────────────────────────────────────────────

def _extract_pdf_text(file_path: str, max_chars: int = 12000) -> tuple[str, int]:
    try:
        import fitz
        doc = fitz.open(file_path)
        pages = len(doc)
        parts = []
        total = 0
        for page in doc:
            t = page.get_text()
            if total + len(t) > max_chars:
                parts.append(t[:max_chars - total])
                total = max_chars
                break
            parts.append(t)
            total += len(t)
        doc.close()
        return "\n".join(parts).strip(), pages
    except Exception as e:
        logger.warning(f"PDF text extraction failed for {file_path}: {e}")
        return "", 0


def _load_case_context(case_id: str, db: Session, store: StorageService) -> list[dict]:
    docs = (
        db.query(Document)
        .filter(Document.case_id == case_id, Document.status == DocumentStatus.READY)
        .order_by(Document.uploaded_at.asc())
        .all()
    )
    if not docs:
        return []
    per_doc = max(3000, 12000 // max(len(docs), 1))
    ctx = []
    for doc in docs:
        local_path = store.get_local_path(doc.storage_path)
        if not Path(local_path).exists():
            continue
        text, pages = _extract_pdf_text(local_path, max_chars=per_doc)
        if text:
            ctx.append({"id": doc.id, "name": doc.original_name, "text": text, "pages": pages})
    return ctx


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class SessionTurn(BaseModel):
    speaker: str  # "lawyer", "judge", "opposing"
    content: str


class CourtroomRequest(BaseModel):
    statement: str = Field(..., min_length=1, max_length=4000,
                           description="The lawyer's statement, argument, or motion")
    session_history: list[SessionTurn] = []
    phase: str = Field(default="opening",
                       description="Trial phase: opening | examination | arguments | closing")
    judge_temperament: str = Field(default="balanced",
                                   description="strict | inquisitive | balanced")


class CourtroomResponse(BaseModel):
    judge_response: str
    opposing_response: str
    phase: str
    turn_number: int


class Scorecard(BaseModel):
    overall_score: int
    legal_reasoning_score: int
    evidence_grounding_score: int
    courtroom_decorum_score: int
    strengths: list[str]
    areas_for_improvement: list[str]
    mentor_notes: str


class VerdictRequest(BaseModel):
    session_history: list[SessionTurn] = []


class VerdictResponse(BaseModel):
    verdict: str        # "Guilty" | "Not Guilty" | "Dismissed" | "Settlement Recommended" | etc.
    outcome: str        # Short label
    reasoning: str      # Judicial reasoning paragraph
    key_findings: list[str]
    scorecard: Optional[Scorecard] = None


# ── System Prompts & Temperament ─────────────────────────────────────────────

TEMPERAMENT_MODIFIERS = {
    "strict": """
JUDGE TEMPERAMENT: STRICT & RIGOROUS
- Enforce strict adherence to procedural law (CrPC/BNSS/CPC) and evidentiary admissibility (IEA/BSA).
- Sustained objections must be sharp, decisive, and uncompromising.
- Intervene sharply if counsel relies on speculation or misquotes document records.
- Demand specific page/exhibit citations.""",

    "inquisitive": """
JUDGE TEMPERAMENT: INQUISITIVE & SOCRATIC
- Rigorously test the counsel's legal theories, logic, and factual foundation.
- Interrupt with probing questions: 'Counsel, how do you reconcile that with the forensic report?'
- Force counsel to explain the practical implications of the relief they are seeking.""",

    "balanced": """
JUDGE TEMPERAMENT: BALANCED & IMPARTIAL
- Maintain calm, dignified judicial decorum.
- Allow counsel fair leeway to articulate their theory of the case.
- Intervene only when necessary to rule on objections or clarify an ambiguous submission.""",
}

JUDGE_SYSTEM_PROMPT = """You are The Honourable Judge presiding over this courtroom proceeding in an Indian Court trial simulation.

CASE DOCUMENTS:
======================================================
{docs_block}
======================================================

{temperament_instructions}

YOUR ROLE — THE JUDGE:
- You maintain order, uphold constitutional and statutory principles, and rule on admissibility.
- You rule on objections immediately and concisely.
- You ask clarifying questions when arguments lack grounding in the case record.
- Current trial phase: {phase}

FORMAT (STRICT — NON-NEGOTIABLE):
- Start with "THE COURT:"
- MAXIMUM 1-3 sentences. No exceptions. No long paragraphs.
- Be punchy, direct, and judicial.
- If no judicial intervention is needed at this exact moment, output EXACTLY "[SILENCE]".
- DO NOT use <think> tags. Just speak as the judge.

CONVERSATION SO FAR:
{history}

The lawyer just said: "{statement}"
Respond as The Judge ONLY. Do not write for opposing counsel."""


OPPOSING_SYSTEM_PROMPT = """You are Opposing Counsel in an Indian Court trial simulation — a sharp, battle-tested Senior Advocate.

CASE DOCUMENTS:
======================================================
{docs_block}
======================================================

YOUR ROLE — OPPOSING COUNSEL:
- You vigorously defend your client's interests and challenge every argument from the lawyer.
- You raise sharp objections when appropriate (hearsay, leading question, lack of foundation, beyond the charge sheet).
- You exploit contradictions between witness statements, medical evidence, or FIR timestamps.
- Current trial phase: {phase}

FORMAT (STRICT — NON-NEGOTIABLE):
- Start with "OPPOSING COUNSEL:"
- MAXIMUM 1-3 sentences. No exceptions. No long paragraphs.
- Deliver adversarial, punchy, and legally precise counter-arguments.
- Reference facts or exhibits from the documents when countering.
- DO NOT use <think> tags. Just speak as opposing counsel.

CONVERSATION SO FAR:
{history}

The lawyer just said: "{statement}"
Respond as Opposing Counsel ONLY. Do not write for the judge."""


VERDICT_SYSTEM_PROMPT = """You are The Honourable Judge delivering a final verdict and a Junior Lawyer Performance Scorecard in an Indian Court trial simulation.

CASE DOCUMENTS:
======================================================
{docs_block}
======================================================

COMPLETE TRIAL TRANSCRIPT:
{history}

Based on the trial transcript and the original case documents, deliver a comprehensive judicial verdict AND evaluate the lawyer's oral advocacy performance.

Return ONLY valid JSON with no markdown wrapping or preamble:
{{
  "verdict": "one of: Guilty | Not Guilty | Civil Liability Found | No Liability | Case Dismissed | Settlement Recommended | Mistrial",
  "outcome": "2-5 word summary (e.g. Acquitted on Benefit of Doubt)",
  "reasoning": "2-3 paragraph judicial reasoning based on evidentiary standards and Indian jurisprudence",
  "key_findings": [
    "Key judicial finding 1",
    "Key judicial finding 2",
    "Key judicial finding 3"
  ],
  "scorecard": {{
    "overall_score": <integer 0-100 from your own assessment>,
    "legal_reasoning_score": <integer 0-100 from your own assessment>,
    "evidence_grounding_score": <integer 0-100 from your own assessment>,
    "courtroom_decorum_score": <integer 0-100 from your own assessment>,
    "strengths": ["<specific strength shown in THIS transcript>"],
    "areas_for_improvement": ["<specific improvement for THIS lawyer>"],
    "mentor_notes": "Constructive 2-3 sentence mentorship advice from a Senior Advocate perspective on how the junior lawyer can elevate their courtroom impact."
  }}
}}"""


# ── Helper: format session history ──────────────────────────────────────────

def _format_history(turns: list[SessionTurn]) -> str:
    if not turns:
        return "(Trial just commenced — no prior exchanges.)"
    lines = []
    for t in turns[-12:]:  # Last 12 turns to stay within context
        speaker_label = {
            "lawyer": "LAWYER",
            "judge": "THE COURT",
            "opposing": "OPPOSING COUNSEL",
        }.get(t.speaker, t.speaker.upper())
        lines.append(f"{speaker_label}: {t.content}")
    return "\n\n".join(lines)


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post(
    "/cases/{case_id}/courtroom",
    response_model=CourtroomResponse,
    summary="Submit a courtroom statement — AI responds as Judge + Opposing Counsel",
)
def courtroom_turn(
    case_id: str,
    body: CourtroomRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    store: StorageService = Depends(get_storage),
):
    """
    The lawyer submits a statement/argument. The AI generates:
    1. A judicial response (The Judge), tuned to the selected temperament.
    2. An adversarial response (Opposing Counsel).
    Both are grounded in actual case documents.
    """
    if not body.statement.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Statement cannot be empty.",
        )

    CaseService(db).get_case(case_id=case_id, user_id=current_user.id)
    case_context = _load_case_context(case_id, db, store)

    if not case_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents are ready for this case. Upload and process documents before starting a courtroom session.",
        )

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

    history_text = _format_history(body.session_history)
    phase = body.phase or "arguments"
    temperament = body.judge_temperament.lower() if body.judge_temperament else "balanced"
    temperament_instr = TEMPERAMENT_MODIFIERS.get(temperament, TEMPERAMENT_MODIFIERS["balanced"])
    statement = body.statement.strip()
    turn_number = len([t for t in body.session_history if t.speaker == "lawyer"]) + 1

    client = _get_groq_client()

    try:
        judge_prompt = JUDGE_SYSTEM_PROMPT.format(
            docs_block=docs_block,
            phase=phase,
            temperament_instructions=temperament_instr,
            history=history_text,
            statement=statement,
        )
        opposing_prompt = OPPOSING_SYSTEM_PROMPT.format(
            docs_block=docs_block,
            phase=phase,
            history=history_text,
            statement=statement,
        )

        judge_response = _call_groq_resilient(
            client,
            [
                {"role": "system", "content": judge_prompt},
                {"role": "user", "content": f"Respond now. The lawyer said: \"{statement}\""},
            ],
            max_tokens=850,
            temperature=0.35,
        )

        opposing_response = _call_groq_resilient(
            client,
            [
                {"role": "system", "content": opposing_prompt},
                {"role": "user", "content": f"Respond now. The lawyer said: \"{statement}\""},
            ],
            max_tokens=850,
            temperature=0.45,
        )

        # Handle silence / formatting
        if judge_response.strip() == "[SILENCE]":
            judge_response = "[SILENCE]"
        elif not judge_response.startswith("THE COURT"):
            judge_response = "THE COURT: " + judge_response

        if not opposing_response.startswith("OPPOSING"):
            opposing_response = "OPPOSING COUNSEL: " + opposing_response

        return CourtroomResponse(
            judge_response=judge_response,
            opposing_response=opposing_response,
            phase=phase,
            turn_number=turn_number,
        )

    except Exception as e:
        logger.error(f"[Courtroom] Error generating responses: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {str(e)}",
        )


@router.post(
    "/cases/{case_id}/courtroom/verdict",
    response_model=VerdictResponse,
    summary="Request a final judicial verdict + Junior Lawyer Performance Scorecard",
)
def get_verdict(
    case_id: str,
    body: VerdictRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    store: StorageService = Depends(get_storage),
):
    """
    Ends the courtroom session and returns the Judge's final verdict
    along with an objective junior lawyer scorecard.
    """
    CaseService(db).get_case(case_id=case_id, user_id=current_user.id)
    case_context = _load_case_context(case_id, db, store)

    if not case_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents available for this case.",
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

    history_text = _format_history(body.session_history)

    system_prompt = VERDICT_SYSTEM_PROMPT.format(
        docs_block=docs_block,
        history=history_text,
    )

    try:
        client = _get_groq_client()
        raw = _call_groq_resilient(
            client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Deliver the final verdict and performance scorecard now as JSON."},
            ],
            max_tokens=2500,
            temperature=0.2,
        )

        # Clean JSON fences
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        raw = re.sub(r'^```(?:json|JSON)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()

        # Try to find { ... } block
        m = re.search(r'(\{[\s\S]*\})', raw)
        if m:
            raw = m.group(1)

        data = json.loads(raw)

        scorecard_data = data.get("scorecard")
        scorecard = None
        if scorecard_data and isinstance(scorecard_data, dict):
            try:  # only the model's own assessment; a partial scorecard is dropped, never padded
                scorecard = Scorecard(
                    overall_score=int(scorecard_data["overall_score"]),
                    legal_reasoning_score=int(scorecard_data["legal_reasoning_score"]),
                    evidence_grounding_score=int(scorecard_data["evidence_grounding_score"]),
                    courtroom_decorum_score=int(scorecard_data["courtroom_decorum_score"]),
                    strengths=list(scorecard_data.get("strengths") or []),
                    areas_for_improvement=list(scorecard_data.get("areas_for_improvement") or []),
                    mentor_notes=str(scorecard_data.get("mentor_notes") or ""),
                )
            except (KeyError, TypeError, ValueError):
                scorecard = None
        return VerdictResponse(
            verdict=str(data["verdict"]),
            outcome=str(data.get("outcome") or ""),
            reasoning=str(data.get("reasoning") or ""),
            key_findings=list(data.get("key_findings") or []),
            scorecard=scorecard,
        )

    except Exception as e:
        logger.error(f"[Verdict] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The verdict could not be generated: {str(e)[:200]}",
        )
