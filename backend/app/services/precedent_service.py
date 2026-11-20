"""
Court Vision AI — Precedent knowledge base.

index_document(): every READY document is added to the `precedents` table with
AI-extracted metadata (title, citation, court, ratio, statutes, principles) and its
page-tagged text. Identical judgments uploaded to several cases are stored once.

search(): BM25 over every indexed page + metadata, best passage per precedent.
"""
import hashlib
import logging
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.precedent import Precedent
from app.services import llm
from app.services.retrieval import BM25, chunk_pages, pdf_pages, tokenize
from app.storage.local import StorageService

logger = logging.getLogger(__name__)

_CITATION = re.compile(r"\(\d{4}\)\s*\d+\s*SCC\s*\d+|AIR\s*\d{4}\s*SC\s*\d+|\[\d{4}\]\s*\d+\s*S\.?C\.?R\.?\s*\d+|\d{4}\s*SCC\s*OnLine\s*\w+\s*\d+")

METADATA_PROMPT = """You are indexing an Indian court document into a precedent library for advocates.
From the document text below, extract ONLY what the text states. Return JSON:
{{
  "case_title": "Full party names, e.g. 'Jacob Mathew v. State of Punjab & Anr.'",
  "citation": "Reported citation if printed in the text (e.g. '(2005) 6 SCC 1'), else null",
  "court": "Court that decided it",
  "decision_date": "Date of judgment as written, else null",
  "bench": "Judges / bench strength if stated, else null",
  "ratio_decidendi": "2-4 sentences: the legal rule the court laid down",
  "key_principles": ["3-8 short principles stated in the judgment"],
  "statutory_provisions": ["Sections/Acts discussed, e.g. 'Section 304A IPC'"],
  "keywords": ["8-15 legal topic keywords for search"],
  "outcome": "What the court finally ordered, if stated"
}}
Use null (not invented values) for anything the text does not state.

DOCUMENT: {name}
--- BEGINNING ---
{head}
--- END OF JUDGMENT ---
{tail}"""


def _hash(pages: list[str]) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", " ".join(pages)).strip().lower().encode()).hexdigest()


def _heuristic_metadata(name: str, pages: list[str]) -> dict:
    """Metadata read directly from the text when the AI is unavailable (nothing invented)."""
    text = "\n".join(pages)
    first = next((ln.strip() for ln in text.splitlines() if len(ln.strip()) > 8), "")
    title = Path(name).stem.replace("_", " ")
    m_vs = re.search(r"^(.{3,120}?\bv(?:s)?\.?\s+.{3,120}?)(?: on \d|\n|$)", text, re.I | re.M)
    if m_vs:
        title = m_vs.group(1).strip()
    cit = _CITATION.search(text)
    court = re.search(r"(Supreme Court of India|High Court of [A-Z][\w ]+|[A-Z][a-z]+ High Court)", text)
    return {"case_title": title, "citation": cit.group(0) if cit else None,
            "court": court.group(1) if court else (first if "court" in first.lower() else None),
            "decision_date": None, "bench": None, "ratio_decidendi": None, "key_principles": [],
            "statutory_provisions": sorted(set(re.findall(r"Section\s+\d+[A-Z]?\s+(?:of\s+the\s+)?(?:IPC|CrPC|BNS|BNSS|Indian Penal Code|Evidence Act)", text)))[:15],
            "keywords": [], "outcome": None}


def index_document(db: Session, doc: Document, store: StorageService) -> Precedent | None:
    path = store.get_local_path(doc.storage_path)
    if not Path(path).exists():
        return None
    pages = pdf_pages(path)
    if not any(p.strip() for p in pages):
        return None
    h = _hash(pages)
    existing = db.query(Precedent).filter(Precedent.content_hash == h).first()
    if existing:
        return existing
    full = "\n\n".join(pages)
    meta, extraction = None, "ai"
    try:
        data, _, _ = llm.chat_json([
            {"role": "system", "content": "You extract structured legal metadata. Output valid JSON only."},
            {"role": "user", "content": METADATA_PROMPT.format(name=doc.original_name, head=full[:6000], tail=full[-4000:] if len(full) > 6000 else "")},
        ], max_tokens=1500, temperature=0.0)
        if isinstance(data, dict) and data.get("case_title"):
            meta = data
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Precedents] AI metadata failed for {doc.original_name}: {e}")
    if meta is None:
        meta, extraction = _heuristic_metadata(doc.original_name, pages), "heuristic"

    def lst(key):
        v = meta.get(key) or []
        return [str(x) for x in v if x][:20] if isinstance(v, list) else [str(v)]

    p = Precedent(
        content_hash=h, source_case_id=doc.case_id, source_document_id=doc.id, source_name=doc.original_name,
        case_title=str(meta.get("case_title"))[:500], citation=(meta.get("citation") or None),
        court=meta.get("court") or None, decision_date=meta.get("decision_date") or None, bench=meta.get("bench") or None,
        ratio_decidendi=meta.get("ratio_decidendi") or None, key_principles=lst("key_principles"),
        statutory_provisions=lst("statutory_provisions"), keywords=lst("keywords"), outcome=meta.get("outcome") or None,
        pages=[{"page": i + 1, "text": t} for i, t in enumerate(pages)], extraction=extraction,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    logger.info(f"[Precedents] Indexed '{p.case_title}' ({len(pages)} pages, {extraction})")
    try:
        extract_cited_authorities(db, p)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning(f"[Precedents] Cited-authority extraction failed for '{p.case_title}': {e}")
    return p


# Reported citations as printed in Indian / English judgments
_REPORTED = re.compile(
    r"\(\d{4}\)\s*\d+\s*(?:SCC|SCR|Bom\.?\s*L\.?R\.?)\s*\d+"
    r"|\[\d{4}\]\s*\d*\s*(?:A\.?C\.?|All\s*ER|W\.?L\.?R\.?|P\.?N\.?L\.?R\.?|Q\.?B\.?|K\.?B\.?|New\s*LJ|Con\.?\s*L\.?R\.?|S\.?C\.?R\.?)\s*\d+"
    r"|\d{4}\s*\(\d+\)\s*(?:All\s*ER|SCC)\s*\d+"
    r"|AIR\s*\d{4}\s*(?:SC|PC|[A-Z][a-z]+)\s*\d+"
    r"|\d{4}\s*SCC\s*OnLine\s*\w+\s*\d+"
    r"|\d{4}\s*(?:SLT|Mh\.?\s*L\.?J\.?|Cri\.?\s*L\.?J\.?)\s*\d+"
    r"|\d+\s*Bom\s*LR\s*\d+"
    r"|\(\d{4}\)\s*\d+\s*All\.?\s*\d+", re.I)

CITED_PROMPT = """Below are numbered passages from the judgment "{parent}". Each contains a citation of an earlier case.
For EACH passage return the cited case exactly as the passage names it. Return JSON:
{{"authorities": [{{"n": 1, "case_title": "party names as written, e.g. 'Dr. Suresh Gupta v. Govt. of NCT of Delhi'",
  "citation": "the citation as printed", "court": "court that decided the cited case, inferred from the reporter
  (SCC/SCR/AIR SC = Supreme Court of India, PC = Privy Council, All ER/AC/WLR/QB = English courts, Bom LR = Bombay High Court)",
  "proposition": "what the judgment cites it for, in one sentence, from the passage"}}]}}
Skip a passage whose case name is not in the passage. Never invent names or citations.

{passages}"""


def _court_from_reporter(citation: str) -> str | None:
    c = citation.upper().replace(".", "").replace(" ", "")
    if "AIR" in c and "PC" in c:
        return "Privy Council"
    if any(r in c for r in ("SCC", "SCR")) or ("AIR" in c and "SC" in c):
        return "Supreme Court of India"
    if "BOMLR" in c or "MHLJ" in c:
        return "Bombay High Court"
    if re.search(r"\)\d+ALL\d", c):
        return "Allahabad High Court"
    if "SLT" in c:
        return "Court of Session (Scotland)"
    if any(r in c for r in ("ALLER", "AC", "WLR", "QB", "KB", "PNLR", "NEWLJ", "CONLR")):
        return "English courts"
    return None


def extract_cited_authorities(db: Session, parent: Precedent) -> int:
    """Add every case the judgment cites (with its printed citation) to the library."""
    flat_pages = [(pg["page"], re.sub(r"\s+", " ", pg["text"])) for pg in parent.pages]
    windows, seen_cits = [], set()
    for page, text in flat_pages:
        for m in _REPORTED.finditer(text):
            cit = re.sub(r"\s+", " ", m.group(0)).strip()
            if cit.lower() in seen_cits:
                continue
            seen_cits.add(cit.lower())
            windows.append((page, cit, text[max(0, m.start() - 260): m.end() + 260]))
    added = 0
    batch_hashes: set[str] = set()
    for start in range(0, len(windows), 12):
        batch = windows[start:start + 12]
        passages = "\n\n".join(f"[{i + 1}] (p. {pg}) …{w}…" for i, (pg, _, w) in enumerate(batch))
        data, _, _ = llm.chat_json([
            {"role": "system", "content": "You extract case citations from judgments. Output valid JSON only."},
            {"role": "user", "content": CITED_PROMPT.format(parent=parent.case_title, passages=passages)},
        ], max_tokens=3000, temperature=0.0)
        items = data.get("authorities") if isinstance(data, dict) else None
        if isinstance(data, dict) and "_salvaged" in data:
            items = data["_salvaged"]
        for it in items or []:
            if not isinstance(it, dict) or not it.get("case_title") or not it.get("citation"):
                continue
            # Accept the pairing only if the citation really is printed in a passage that names the case
            cit_key = re.sub(r"\W", "", str(it["citation"]).lower())
            title_word = next((w for w in re.findall(r"[A-Za-z]{4,}", str(it["case_title"])) if w.lower() not in {"state", "union", "india"}), "")
            hit = next(((pg, printed, w) for pg, printed, w in batch
                        if re.sub(r"\W", "", printed.lower()) == cit_key and title_word.lower() in w.lower()), None)
            if not hit:
                continue
            page, printed, window = hit
            h = hashlib.sha256(cit_key.encode()).hexdigest()
            if h in batch_hashes or db.query(Precedent).filter(Precedent.content_hash == h).first():
                continue
            batch_hashes.add(h)
            db.add(Precedent(
                content_hash=h, source_name=f"Cited in {parent.case_title}", case_title=str(it["case_title"])[:500],
                citation=printed, court=_court_from_reporter(printed), ratio_decidendi=it.get("proposition") or None,
                key_principles=[], statutory_provisions=[], keywords=[], pages=[{"page": page, "text": window}],
                extraction="cited", cited_in_id=parent.id, cited_in=parent.case_title))
            added += 1
        db.commit()
    logger.info(f"[Precedents] {added} cited authorities added from '{parent.case_title}'")
    return added


def backfill(db: Session, store: StorageService) -> int:
    """Index every READY document not yet in the library."""
    added = 0
    for doc in db.query(Document).filter(Document.status == DocumentStatus.READY).all():
        before = db.query(Precedent).count()
        try:
            index_document(db, doc, store)
        except Exception as e:  # noqa: BLE001
            db.rollback()
            logger.warning(f"[Precedents] Backfill failed for {doc.id}: {e}")
        added += db.query(Precedent).count() - before
    # Judgments indexed before cited-authority extraction existed
    for parent in db.query(Precedent).filter(Precedent.extraction.in_(["ai", "heuristic"])).all():
        if not db.query(Precedent).filter(Precedent.cited_in_id == parent.id).first():
            try:
                added += extract_cited_authorities(db, parent)
            except Exception as e:  # noqa: BLE001
                db.rollback()
                logger.warning(f"[Precedents] Cited extraction failed for {parent.case_title}: {e}")
    return added


def search(db: Session, query: str, k: int = 8, exclude_case_id: str | None = None) -> list[dict]:
    """Best-matching library precedents with their most relevant passage and page."""
    rows = db.query(Precedent).all()
    if exclude_case_id:
        rows = [r for r in rows if r.source_case_id != exclude_case_id]
    if not rows:
        return []
    units, owner = [], []
    for r in rows:
        meta = " ".join(filter(None, [r.case_title, r.citation, r.court, r.ratio_decidendi,
                                      " ".join(r.key_principles or []), " ".join(r.statutory_provisions or []),
                                      " ".join(r.keywords or [])]))
        units.append(("meta", 0, meta)); owner.append(r)
        for c in chunk_pages(r.id, r.source_name, [pg["text"] for pg in r.pages]):
            units.append(("page", c.page, c.text)); owner.append(r)
    sc = BM25([tokenize(u[2]) for u in units]).scores(tokenize(query))
    meta_score: dict[str, float] = {}
    best_page: dict[str, tuple[float, int, str]] = {}
    for (kind, page, text), r, s in zip(units, owner, sc):
        if s <= 0:
            continue
        if kind == "meta":
            meta_score[r.id] = 1.3 * s  # summary fields are denser evidence of relevance
        elif s > best_page.get(r.id, (0, 0, ""))[0]:
            best_page[r.id] = (s, page, text)
    total = {pid: meta_score.get(pid, 0) + best_page.get(pid, (0, 0, ""))[0] for pid in set(meta_score) | set(best_page)}
    byid = {r.id: r for r in rows}
    out = []
    for pid in sorted(total, key=lambda p: -total[p])[:k]:
        r = byid[pid]
        _, page, text = best_page.get(pid, (0, 0, ""))
        out.append(dict(id=r.id, case_title=r.case_title, citation=r.citation, court=r.court,
                        decision_date=r.decision_date, bench=r.bench, ratio_decidendi=r.ratio_decidendi,
                        key_principles=r.key_principles or [], statutory_provisions=r.statutory_provisions or [],
                        outcome=r.outcome, source_name=r.source_name, source_case_id=r.source_case_id,
                        passage=text, page=page or None, score=round(total[pid], 3)))
    return out
