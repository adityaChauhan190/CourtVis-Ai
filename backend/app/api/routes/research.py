"""
Court Vision AI - Legal Precedents & Indian Case Law Research API

POST /api/research/query
  1. Searches the precedent knowledge base (every judgment ever uploaded to Court Vision)
  2. Asks the LLM for further landmark Indian authorities, giving it the library matches
  3. Merges both, de-duplicated, each precedent labelled with its source
GET  /api/research/library          — list the knowledge base
POST /api/research/library/reindex  — index any READY document not yet in the library
"""
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_storage
from app.models.precedent import Precedent
from app.schemas.document import UserContext
from app.services import llm, precedent_service
from app.storage.local import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["research"])


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Legal issue, doctrine, or proposition")
    jurisdiction: Optional[str] = Field(default="Supreme Court of India", description="Court level or jurisdiction")
    statute: Optional[str] = Field(default=None, description="Optional statute filter e.g. IPC, CrPC, BNS, BNSS, PMLA")
    case_id: Optional[str] = Field(default=None, description="Optional: the case being prepared (excluded from library hits)")


class PrecedentItem(BaseModel):
    case_title: str
    citation: str
    court: str
    bench_size: Optional[str] = None
    ratio_decidendi: str
    key_quote: str = ""
    application_guidance: str = ""
    statutory_provisions: list[str] = []
    source: str = "ai"                  # "library" = from an uploaded judgment | "ai" = suggested by the model
    source_document: Optional[str] = None
    page: Optional[int] = None
    passage: Optional[str] = None       # matching passage from the uploaded judgment
    verify: bool = True                 # AI-suggested citations must be verified before filing


class ResearchResponse(BaseModel):
    query: str
    key_principles: list[str]
    statutory_provisions: list[str]
    precedents: list[PrecedentItem]
    argument_strategy: str
    library_count: int = 0
    ai_count: int = 0
    library_size: int = 0
    unverified_leads: list[PrecedentItem] = []   # AI suggestions not found in the library — check before use
    warnings: list[str] = []


RESEARCH_PROMPT = """You are an authority on Indian constitutional, criminal and civil jurisprudence, assisting an advocate.

RESEARCH QUESTION: {query}
JURISDICTION: {jurisdiction}
STATUTE FILTER: {statute}

JUDGMENTS ALREADY IN THE ADVOCATE'S LIBRARY (verified; use them where relevant, do not repeat them in "precedents"):
{library}

Return JSON only:
{{
  "key_principles": ["4-8 core legal principles on this question"],
  "statutory_provisions": ["Each relevant provision with its new-code equivalent, e.g. 'Section 304A IPC / Section 106 BNS — causing death by negligence'"],
  "precedents": [
    {{"case_title": "Full party names", "citation": "Reported citation (SCC / AIR / SCR)", "court": "Court",
      "bench_size": "e.g. 3-Judge Bench", "ratio_decidendi": "1-2 sentence holding",
      "key_quote": "A short, well-known line from the judgment, or empty string if unsure",
      "application_guidance": "How to use this authority in arguments on THIS question",
      "statutory_provisions": ["Sections involved"]}}
  ],
  "argument_strategy": "2-3 paragraphs: how to structure the argument, cautions, and how to meet the other side"
}}

RULES:
- Give up to 12 DIFFERENT real Indian precedents (Supreme Court first, then High Courts), most authoritative first.
- ACCURACY OVER QUANTITY: an advocate will cite these in court. Include a judgment only if you are certain it exists
  with exactly those parties. If unsure of the citation, write "citation to be verified". Return fewer rather than guess.
- Never invent quotations: leave "key_quote" empty rather than guess."""


def _norm_title(t: str) -> str:
    t = (t or "").lower()
    t = re.sub(r"\b(vs?|versus)\b\.?", " v ", t)
    t = re.sub(r"\b(and|&)\s*(anr|ors|others|another)\.?", " ", t)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return " ".join(w for w in t.split() if w not in {"the", "of", "dr", "shri", "smt", "m", "s"})


def _library_item(m: dict) -> PrecedentItem:
    principles = m.get("key_principles") or []
    return PrecedentItem(
        case_title=m["case_title"], citation=m.get("citation") or "Citation not printed in the uploaded document",
        court=m.get("court") or "—", bench_size=m.get("bench"),
        ratio_decidendi=m.get("ratio_decidendi") or (principles[0] if principles else (m.get("passage") or "")[:400]),
        key_quote="", application_guidance="; ".join(principles[:3]),
        statutory_provisions=m.get("statutory_provisions") or [], source="library",
        source_document=m.get("source_name"), page=m.get("page"), passage=m.get("passage"), verify=False)


@router.post("/research/query", response_model=ResearchResponse)
def query_precedents(
    body: ResearchRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Landmark precedents, ratios, statutes and argument strategy — library + AI, merged."""
    warnings: list[str] = []
    search_text = " ".join(filter(None, [body.query, body.statute if body.statute and "All" not in body.statute else None]))
    library = precedent_service.search(db, search_text, k=10, exclude_case_id=body.case_id)
    library_items = [_library_item(m) for m in library]

    lib_block = "\n".join(f"- {m['case_title']} ({m.get('citation') or 'citation not printed'}): "
                          f"{(m.get('ratio_decidendi') or '')[:300]}" for m in library) or "(none match this question)"
    data: dict = {}
    try:
        parsed, model, finish = llm.chat_json([
            {"role": "system", "content": "You are a precise Indian legal research assistant. Output valid JSON only."},
            {"role": "user", "content": RESEARCH_PROMPT.format(
                query=body.query, jurisdiction=body.jurisdiction or "Supreme Court of India",
                statute=body.statute or "Any relevant Indian statute", library=lib_block)},
        ], max_tokens=6000, temperature=0.1, reasoning="medium")
        data = parsed if isinstance(parsed, dict) else {}
        if "_salvaged" in data:  # truncated output: keep every complete precedent object
            data = {"precedents": [o for o in data["_salvaged"] if o.get("case_title") and o.get("ratio_decidendi")]}
            warnings.append("The AI response was cut short; showing the precedents it completed.")
        elif finish == "length":
            warnings.append("The AI response reached its length limit.")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Research] AI research failed: {e}")
        warnings.append(f"AI research is unavailable right now ({str(e)[:120]}). Showing matches from your case library only.")

    if not library_items and not data:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="AI research is unavailable and no uploaded judgment in your library matches this question.")

    seen = {_norm_title(p.case_title) for p in library_items}
    # Everything the library knows (uploaded judgments + authorities they cite) verifies an AI suggestion
    all_rows = db.query(Precedent).all()
    known = {_norm_title(r.case_title): r for r in all_rows}
    # Same first party as a library case (e.g. "Laxman Balkrishna Joshi v. <wrong party>") → the library's record wins
    by_first = {_norm_title(r.case_title).split(" v ")[0]: r for r in all_rows if " v " in _norm_title(r.case_title)}
    ai_items: list[PrecedentItem] = []
    unsure = 0
    for p in data.get("precedents", []) or []:
        if not isinstance(p, dict) or not p.get("case_title"):
            continue
        key = _norm_title(p["case_title"])
        cit = str(p.get("citation") or "")
        first = key.split(" v ")[0]
        if key not in known and " v " in key and first in by_first and len(first.split()) >= 2:
            lib = by_first[first]
            key = _norm_title(lib.case_title)
            if key in seen:
                continue
            p = dict(p, case_title=lib.case_title)
        if key not in known and (not re.search(r"\d{4}", cit) or "verif" in cit.lower()):
            unsure += 1  # the model itself could not give a citation → not shown to an advocate
            continue
        if key in seen:
            continue
        seen.add(key)
        match = known.get(key)
        ai_items.append(PrecedentItem(
            case_title=str(p["case_title"]),
            citation=(match.citation if match and match.citation else str(p.get("citation") or "citation to be verified")),
            court=str(p.get("court") or body.jurisdiction or ""), bench_size=p.get("bench_size"),
            ratio_decidendi=str(p.get("ratio_decidendi") or ""), key_quote=str(p.get("key_quote") or ""),
            application_guidance=str(p.get("application_guidance") or ""),
            statutory_provisions=[str(s) for s in (p.get("statutory_provisions") or [])], source="ai",
            source_document=(match.source_name if match else None), verify=match is None))

    if unsure:
        warnings.append(f"{unsure} AI suggestion(s) were left out because the AI could not give a reliable citation.")
    principles = data.get("key_principles") or [pr for m in library for pr in (m.get("key_principles") or [])][:8]
    provisions = data.get("statutory_provisions") or sorted({s for m in library for s in (m.get("statutory_provisions") or [])})[:12]
    return ResearchResponse(
        query=body.query, key_principles=[str(x) for x in principles], statutory_provisions=[str(x) for x in provisions],
        precedents=library_items + [p for p in ai_items if not p.verify],
        unverified_leads=[p for p in ai_items if p.verify],
        argument_strategy=str(data.get("argument_strategy") or ""),
        library_count=len(library_items), ai_count=len([p for p in ai_items if not p.verify]),
        library_size=db.query(Precedent).count(), warnings=warnings)


@router.get("/research/library")
def list_library(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Precedent).order_by(Precedent.created_at.desc()).all()
    return {"total": len(rows), "precedents": [
        dict(id=r.id, case_title=r.case_title, citation=r.citation, court=r.court, decision_date=r.decision_date,
             statutory_provisions=r.statutory_provisions or [], source_name=r.source_name,
             pages=len(r.pages or []), extraction=r.extraction, created_at=r.created_at) for r in rows]}


@router.post("/research/library/reindex")
def reindex_library(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db),
                    store: StorageService = Depends(get_storage)):
    added = precedent_service.backfill(db, store)
    return {"added": added, "total": db.query(Precedent).count()}
