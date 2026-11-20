"""
Court Vision AI - Trial Prep & Reports API

GET /api/cases/{case_id}/trial-brief
Builds the brief from the case's own documents in three grounded LLM calls, each given
the parts of the WHOLE record that matter for it (page-tagged BM25 retrieval):
  1. Date-wise chronology            — passages that contain dates
  2. Witness cross-examination bank  — passages about witnesses, statements and evidence
  3. Executive legal synopsis        — opening + closing of the record and the key issues
plus related precedents from the knowledge base. Nothing is hard-coded: a section the
AI could not produce is reported in `errors`, never replaced by template text.
"""
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_storage
from app.schemas.document import UserContext
from app.services import llm, precedent_service
from app.services.case_service import CaseService
from app.services.retrieval import Chunk, budgeted, case_chunks, format_excerpts, top_chunks
from app.storage.local import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])

CONTEXT_CHARS = 8000  # per call; prompt + output must fit an 8k tokens-per-minute quota

_DATE = re.compile(
    r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b", re.I)

ROLE_VIEW = {
    "defence": "You act for the DEFENCE / accused / respondent.",
    "prosecution": "You act for the PROSECUTION / complainant / petitioner.",
    "researcher": "You are a neutral legal researcher; present both sides fairly.",
    "student": "You are preparing a law student for a moot court; present both sides and explain why.",
}

COMMON_RULES = """RULES:
- Use ONLY facts in the excerpts. Every item cites its source as "<document name>, p. N" taken from the excerpt tags.
- If the excerpts do not support an item, leave it out. Never invent names, dates, numbers or events.
- Keep every section number exactly as the record states it. Add the new-code equivalent in brackets only when
  you are certain of it (e.g. "Section 304A IPC (s. 106 BNS)", "Section 482 CrPC (s. 528 BNSS)"); never renumber.
- Output valid JSON only."""

CHRONOLOGY_PROMPT = """Build a DATE-WISE CHRONOLOGY of the case for trial preparation.
CASE: {title} ({ctype}). {role}

EXCERPTS (tagged with document and page):
{excerpts}

Return JSON: {{"chronology": [{{"date": "date exactly as in the record (DD.MM.YYYY or as written)",
  "event": "what happened, one or two sentences",
  "significance": "why it matters at trial (limitation, delay, procedure, evidence)",
  "source": "<document name>, p. N"}}]}}
Order strictly by date, earliest first. Include every dated event in the excerpts (procedural steps too).
{rules}"""

CROSS_PROMPT = """Prepare a WITNESS CROSS-EXAMINATION BANK for trial.
CASE: {title} ({ctype}). {role}

EXCERPTS (tagged with document and page):
{excerpts}

Return JSON: {{"cross_examination": [{{"witness": "name or role exactly as in the record",
  "role": "e.g. Complainant / Investigating Officer / Medical expert / Accused",
  "questions": [{{"question": "a precise, leading cross-examination question",
     "objective": "what the question is meant to establish",
     "contradiction": "the gap, delay or inconsistency in the record it targets",
     "source": "<document name>, p. N"}}]}}]}}
Cover every witness or deponent named in the excerpts, 3-6 questions each, sharpest first.
{rules}"""

SYNOPSIS_PROMPT = """Write an EXECUTIVE TRIAL SYNOPSIS for the advocate.
CASE: {title} ({ctype}). {role}
USER'S NOTE ON THE CASE (may be incomplete or wrong — the record prevails; state nothing from it that the excerpts do not support): {description}

EXCERPTS (tagged with document and page):
{excerpts}

Return JSON: {{"synopsis": "Markdown with exactly these sections, each 1-3 short paragraphs or bullets, citing pages in brackets like (p. 4):\\n# Executive Trial Synopsis\\n## 1. Case Overview & Procedural History\\n## 2. Applicable Statutory Framework\\n## 3. Case of the Other Side\\n## 4. Our Theory of the Case & Contradictions in the Record\\n## 5. Strengths\\n## 6. Risks & Weaknesses\\n## 7. Recommended Courtroom Strategy"}}
Paragraphs are separated by a blank line; bullets start with "- ".
{rules}"""

CHRONO_Q = "date dated filed lodged registered admitted died order hearing judgment notice appeal petition FIR complaint charge"
CROSS_Q = ("witness statement deposed deposition examined testified stated complainant informant investigating officer "
           "doctor nurse report evidence exhibit cross-examination affidavit opinion")
SYNOPSIS_Q = "held issue question contention submitted argued section offence negligence liability conclusion appeal result"


def _dated_chunks(chunks: list[Chunk]) -> list[Chunk]:
    dated = [c for c in chunks if _DATE.search(c.text)]
    ranked = top_chunks(dated, CHRONO_Q, k=len(dated)) if dated else []
    # keep the date-densest passages, then put them back in record order
    ranked = sorted(ranked, key=lambda c: -len(_DATE.findall(c.text)))
    keep = {id(c) for c in budgeted(ranked, CONTEXT_CHARS)}
    return [c for c in chunks if id(c) in keep]


def _synopsis_chunks(chunks: list[Chunk]) -> list[Chunk]:
    head = budgeted(chunks, 3000)
    tail = budgeted(list(reversed(chunks)), 3000)[::-1]
    picked = {id(c) for c in head + tail}
    middle = [c for c in top_chunks(chunks, SYNOPSIS_Q, k=12) if id(c) not in picked]
    keep = picked | {id(c) for c in budgeted(middle, CONTEXT_CHARS - 6000)}
    return [c for c in chunks if id(c) in keep]


def _section(prompt: str, key: str, excerpts: list[Chunk], max_tokens: int, **fmt):
    data, model, finish = llm.chat_json([
        {"role": "system", "content": "You are a Senior Advocate and trial strategist under Indian law. Output valid JSON only."},
        {"role": "user", "content": prompt.format(excerpts=format_excerpts(excerpts), rules=COMMON_RULES, **fmt)},
    ], max_tokens=max_tokens, temperature=0.2)
    note = None
    if isinstance(data, dict) and "_salvaged" in data:
        note = f"The {key.replace('_', ' ')} was cut short by the AI's length limit; showing the complete items."
        data = {key: data["_salvaged"]}
    value = data.get(key) if isinstance(data, dict) else None
    return value, model, note


@router.get("/cases/{case_id}/trial-brief")
def get_trial_brief(
    case_id: str,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    store: StorageService = Depends(get_storage),
):
    case = CaseService(db).get_case(case_id=case_id, user_id=current_user.id)
    chunks = case_chunks(case_id, db, store)
    if not chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No processed documents in this case yet. Upload the case PDFs and wait until they show Ready.")

    ctype = case.case_type.value if hasattr(case.case_type, "value") else str(case.case_type)
    role_key = case.user_role.value if hasattr(case.user_role, "value") else str(case.user_role)
    fmt = dict(title=case.name, ctype=ctype, role=ROLE_VIEW.get(role_key, ROLE_VIEW["researcher"]))
    errors: list[str] = []
    models: set[str] = set()

    def run(name, fn):
        try:
            value, model, note = fn()
            models.add(model)
            if note:
                errors.append(note)
            return value
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[Reports] {name} failed: {e}")
            errors.append(f"{name} could not be generated: {str(e)[:160]}")
            return None

    chronology = run("Chronology", lambda: _section(CHRONOLOGY_PROMPT, "chronology", _dated_chunks(chunks), 3500, **fmt)) or []
    cross = run("Cross-examination bank", lambda: _section(
        CROSS_PROMPT, "cross_examination", budgeted(top_chunks(chunks, CROSS_Q, k=14), CONTEXT_CHARS), 4000, **fmt)) or []
    synopsis = run("Synopsis", lambda: _section(
        SYNOPSIS_PROMPT, "synopsis", _synopsis_chunks(chunks), 3500, description=case.description or "—", **fmt)) or ""

    # Salvaged objects can mix shapes: keep only well-formed items
    chronology = [c for c in chronology if isinstance(c, dict) and c.get("date") and c.get("event")]
    cross = [w for w in cross if isinstance(w, dict) and w.get("witness") and isinstance(w.get("questions"), list)]
    if not isinstance(synopsis, str):
        synopsis = ""
    if not chronology and not cross and not synopsis:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="The trial brief could not be generated. " + " ".join(errors))

    issues = " ".join([case.name, case.description or ""] + [c.get("event", "") for c in chronology[:8]])
    related = precedent_service.search(db, issues, k=5, exclude_case_id=case_id)

    return {
        "case_id": case_id,
        "case_title": case.name,
        "chronology": chronology,
        "cross_examination": cross,
        "synopsis": synopsis,
        "related_precedents": [dict(case_title=r["case_title"], citation=r.get("citation"), court=r.get("court"),
                                    ratio_decidendi=r.get("ratio_decidendi"), source_document=r["source_name"],
                                    page=r.get("page")) for r in related],
        "doc_count": len({c.doc_id for c in chunks}),
        "pages_indexed": len({(c.doc_id, c.page) for c in chunks}),
        "model": ", ".join(sorted(models)),
        "errors": errors,
    }
