"""
Court Vision AI — Evidence Graph Route

GET /api/cases/{case_id}/graph[?force_refresh=true]
  - Extracts an advocate-oriented entity/relationship graph from the WHOLE case record:
    opening + closing pages and the passages about parties, witnesses, evidence and law
    (page-tagged BM25 retrieval), so later pages are not ignored.
  - The LLM is asked for canonical entities with aliases, page-cited descriptions and a
    stated legal significance for every relationship.
  - A deterministic merge pass then removes duplicates ("Dr. Jacob Mathew" = "Jacob Mathew"
    = "the appellant"), self-links and repeated edges, and drops dangling edges.
  - Result cached in case.evidence_graph (cleared whenever the case's documents change).

Node types: person, organization, date, location, fact, evidence
Edge types: involved_in, related_to, occurred_at, supports, contradicts, filed_by, testified_by, linked_to
"""
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_storage
from app.schemas.document import UserContext
from app.services import llm
from app.services.case_service import CaseService
from app.services.retrieval import budgeted, case_chunks, format_excerpts, top_chunks
from app.storage.local import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Graph"])

NODE_TYPES = {"person", "organization", "date", "location", "fact", "evidence"}
EDGE_TYPES = {"involved_in", "related_to", "occurred_at", "supports", "contradicts", "filed_by", "testified_by", "linked_to"}
MAX_NODES = 28
CONTEXT_CHARS = 10000


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    description: Optional[str] = None
    document_sources: list[str] = []


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    label: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    has_documents: bool
    document_count: int
    merged_duplicates: int = 0


GRAPH_PROMPT = """You are building an EVIDENCE MAP that an advocate will use to prepare for trial.
CASE: {title}

Excerpts from the case record (tagged with document and page):
{excerpts}

Return JSON:
{{"nodes": [{{"id": "snake_case_id", "label": "Canonical short name (1-5 words)",
   "type": "person|organization|date|location|fact|evidence",
   "aliases": ["every other way the record refers to this same entity, e.g. 'the appellant', 'Dr. Mathew', 'accused no. 1'"],
   "description": "Its role in the case in one sentence, with page, e.g. 'Treating doctor; accused under s.304A IPC (p. 1)'",
   "document_sources": ["<document name>"]}}],
 "edges": [{{"id": "e1", "source": "node_id", "target": "node_id",
   "type": "involved_in|related_to|occurred_at|supports|contradicts|filed_by|testified_by|linked_to",
   "label": "the legal significance in 2-6 words, e.g. 'filed FIR against', 'shows delay in treatment'"}}]}}

WHAT TO INCLUDE (12-{max_nodes} nodes, only what matters at trial):
- person: parties, accused, complainant, each witness, judges only if relevant to the outcome
- organization: courts, police station, hospital/company, investigating agency
- evidence: FIR, charge-sheet, medical/forensic reports, exhibits, key statutory provisions (e.g. 'Section 304A IPC')
- fact: disputed or decisive facts (e.g. 'Oxygen cylinder empty', 'No doctor for 20-25 minutes')
- date: only dates on which something legally important happened
- location: only places that matter to the facts

STRICT RULES:
- ONE node per real-world entity. Never create a second node for an alias, title or role of an entity already listed — put it in "aliases".
- No generic nodes ("the Court", "evidence", "the case", "law"), no nodes that appear only in passing.
- Every node takes part in at least one edge. Prefer 'supports' / 'contradicts' between facts and evidence wherever the record shows it.
- Use only what the excerpts state. Output valid JSON only."""

GRAPH_Q = ("accused appellant complainant informant witness doctor police officer FIR report evidence exhibit statement "
           "deposed charge section offence hospital date contradiction delay held found")

_TITLES = re.compile(r"\b(dr|mr|mrs|ms|miss|shri|sri|smt|sh|late|kumari|prof|hon'?ble|justice|adv|advocate|the|m/s)\b\.?", re.I)


def _norm(label: str) -> str:
    s = _TITLES.sub(" ", (label or "").lower())
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def _slug(label: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", _norm(label))).strip("_")[:48] or "node"


def _merge(raw_nodes: list[dict], raw_edges: list[dict]) -> tuple[list[dict], list[dict], int]:
    """Collapse duplicate entities and edges. Returns (nodes, edges, merged_count)."""
    canon: list[dict] = []
    id_map: dict[str, str] = {}
    keys: dict[str, str] = {}           # normalised name/alias → canonical id
    merged = 0
    for n in raw_nodes:
        if not isinstance(n, dict) or not n.get("label"):
            continue
        ntype = str(n.get("type", "fact")).lower().strip()
        ntype = ntype if ntype in NODE_TYPES else "fact"
        label = str(n["label"]).strip()[:60]
        names = [label] + [str(a) for a in (n.get("aliases") or []) if a]
        norms = [x for x in {_norm(x) for x in names} if x]
        hit = next((keys[k] for k in norms if k in keys), None)
        if hit is None and ntype == "person":
            # "Jacob Mathew" vs "Jacob Mathew Kurian": same person if one name's words contain the other's (≥ 2 words)
            mine = set(_norm(label).split())
            for c in canon:
                if c["type"] == "person":
                    theirs = set(_norm(c["label"]).split())
                    small = min(mine, theirs, key=len)
                    if len(small) >= 2 and small <= (mine | theirs) and (mine <= theirs or theirs <= mine):
                        hit = c["id"]
                        break
        orig_id = str(n.get("id") or _slug(label))
        if hit:
            merged += 1
            target = next(c for c in canon if c["id"] == hit)
            if len(n.get("description") or "") > len(target["description"] or ""):
                target["description"] = n.get("description")
            target["document_sources"] = sorted(set(target["document_sources"]) | set(n.get("document_sources") or []))
            id_map[orig_id] = hit
        else:
            nid = _slug(label)
            while any(c["id"] == nid for c in canon):
                nid += "_2"
            canon.append(dict(id=nid, label=label, type=ntype, description=n.get("description"),
                              document_sources=[str(s) for s in (n.get("document_sources") or [])][:5]))
            id_map[orig_id] = nid
            hit = nid
        for k in norms:
            keys.setdefault(k, hit)
        id_map.setdefault(_slug(label), hit)

    edges, seen = [], set()
    for i, e in enumerate(raw_edges):
        if not isinstance(e, dict):
            continue
        s = id_map.get(str(e.get("source", "")).strip()) or keys.get(_norm(str(e.get("source", ""))))
        t = id_map.get(str(e.get("target", "")).strip()) or keys.get(_norm(str(e.get("target", ""))))
        if not s or not t or s == t:
            continue
        etype = str(e.get("type", "related_to")).lower().strip()
        etype = etype if etype in EDGE_TYPES else "related_to"
        key = (s, t, etype)
        if key in seen or (t, s, etype) in seen:
            continue
        seen.add(key)
        edges.append(dict(id=f"e{len(edges) + 1}", source=s, target=t, type=etype,
                          label=str(e.get("label") or etype.replace("_", " "))[:60]))

    # Keep connected, most-linked nodes first (an isolated node is rarely useful to an advocate)
    degree = {c["id"]: 0 for c in canon}
    for e in edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1
    nodes = [c for c in canon if degree[c["id"]] > 0] or canon
    if len(nodes) > MAX_NODES:
        nodes = sorted(nodes, key=lambda c: -degree[c["id"]])[:MAX_NODES]
    keep = {c["id"] for c in nodes}
    edges = [e for e in edges if e["source"] in keep and e["target"] in keep]
    return nodes, edges, merged


def _response(cached: dict) -> GraphResponse:
    return GraphResponse(nodes=[GraphNode(**n) for n in cached["nodes"]], edges=[GraphEdge(**e) for e in cached["edges"]],
                         has_documents=True, document_count=cached.get("document_count", 0),
                         merged_duplicates=cached.get("merged_duplicates", 0))


@router.get("/cases/{case_id}/graph", response_model=GraphResponse)
def get_evidence_graph(
    case_id: str,
    force_refresh: bool = Query(default=False, description="Bypass cache and re-extract graph from documents"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    store: StorageService = Depends(get_storage),
):
    case = CaseService(db).get_case(case_id=case_id, user_id=current_user.id)

    if not force_refresh and case.evidence_graph and case.evidence_graph.get("version") == 2:
        try:
            return _response(case.evidence_graph)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[Graph] Bad cache for {case_id}: {e}; re-extracting")

    chunks = case_chunks(case_id, db, store)
    if not chunks:
        return GraphResponse(nodes=[], edges=[], has_documents=False, document_count=0)

    head = budgeted(chunks, 2500)
    tail = budgeted(list(reversed(chunks)), 2500)[::-1]
    picked = {id(c) for c in head + tail}
    middle = [c for c in top_chunks(chunks, GRAPH_Q, k=20) if id(c) not in picked]
    keep = picked | {id(c) for c in budgeted(middle, CONTEXT_CHARS - 5000)}
    excerpts = [c for c in chunks if id(c) in keep]

    try:
        data, model, finish = llm.chat_json([
            {"role": "system", "content": "You are a precise legal knowledge-graph extractor. Output valid JSON only."},
            {"role": "user", "content": GRAPH_PROMPT.format(title=case.name, excerpts=format_excerpts(excerpts), max_nodes=MAX_NODES)},
        ], max_tokens=4000, temperature=0.1)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Evidence graph could not be generated: {e}")

    if isinstance(data, dict) and "_salvaged" in data:  # truncated: classify the complete objects
        objs = data["_salvaged"]
        data = {"nodes": [o for o in objs if {"id", "label", "type"} <= o.keys()],
                "edges": [o for o in objs if {"source", "target"} <= o.keys()]}
    raw_nodes = data.get("nodes", []) if isinstance(data, dict) else []
    raw_edges = data.get("edges", []) if isinstance(data, dict) else []
    nodes, edges, merged = _merge(raw_nodes, raw_edges)
    if not nodes:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The AI returned no usable entities for this case. Try Refresh.")

    doc_count = len({c.doc_id for c in chunks})
    case.evidence_graph = {"version": 2, "nodes": nodes, "edges": edges, "document_count": doc_count,
                           "merged_duplicates": merged, "model": model}
    db.commit()
    logger.info(f"[Graph] {case_id}: {len(nodes)} nodes, {len(edges)} edges, {merged} duplicates merged ({model})")
    return _response(case.evidence_graph)
