"""
Experiment 4b — Robustness of LLM-output JSON parsing (Evidence Graph module).

Base data: the three evidence graphs that Groq actually generated for the
three cases stored in backend/court_vision.db (case.evidence_graph column).
Each is re-serialised as the raw LLM output and then corrupted in the ways
LLM responses really fail: markdown fences, <think> blocks, prose wrappers,
trailing notes, and truncation at the max_tokens limit.

Parsers compared (all taken from the Court Vision code base):
  P0 Naive        : json.loads(raw)
  P1 Fence-strip  : chat.py summary route  (strip <think> + ``` then json.loads)
  P2 Safe-JSON    : reports.py/_safe_json   (fence regex, first/last bracket slice)
  P3 Robust (ours): graph.py/_extract_json  (brace-depth scan + partial-object recovery)

Run from backend/:  ./venv/Scripts/python.exe ../research_experiments/eval/run_json_robustness.py
"""
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

import logging  # noqa: E402
logging.disable(logging.CRITICAL)

from app.api.routes.graph import _extract_json  # noqa: E402
from app.api.routes.reports import _safe_json   # noqa: E402


def p0_naive(raw):
    return json.loads(raw)


def p1_fence_strip(raw):  # verbatim logic from chat.py get_case_summary
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
    raw = re.sub(r'^```(?:json|JSON)?\s*\n?', '', raw)
    raw = re.sub(r'\n?```\s*$', '', raw)
    return json.loads(raw.strip())


def p2_safe_json(raw):
    r = _safe_json(raw)
    if r is None:
        raise ValueError("unparsed")
    return r


def p3_robust(raw):
    return _extract_json(raw)


def p4_nested_salvage(raw):
    """Proposed fix: P3 first; on failure salvage complete objects at ANY depth.

    graph.py's partial recovery only records objects that close at depth 0, so on a
    truncated response (outer object never closes) it recovers nothing. Here a stack
    of open-brace positions lets every complete inner {...} be parsed and classified.
    """
    try:
        return _extract_json(raw)
    except Exception:
        pass
    text = re.sub(r'<think>.*?(</think>|$)', '', raw, flags=re.DOTALL)
    stack, in_str, esc, nodes, edges = [], False, False, [], []
    for i, ch in enumerate(text):
        if esc:
            esc = False
            continue
        if ch == '\\' and in_str:
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            stack.append(i)
        elif ch == '}' and stack:
            start = stack.pop()
            try:
                obj = json.loads(text[start:i + 1])
            except Exception:
                continue
            if isinstance(obj, dict):
                if {'source', 'target'} <= obj.keys():
                    edges.append(obj)
                elif {'id', 'label', 'type'} <= obj.keys():
                    nodes.append(obj)
    if not nodes:
        raise ValueError("nothing salvageable")
    return {"nodes": nodes, "edges": edges}


PARSERS = {"P0_Naive": p0_naive, "P1_FenceStrip": p1_fence_strip,
           "P2_SafeJSON": p2_safe_json, "P3_Robust": p3_robust,
           "P4_NestedSalvage": p4_nested_salvage}

THINK = "<think>The user wants a graph. I should list persons such as {Jacob Mathew} and facts first.</think>\n"
PROSE = "Here is the extracted legal knowledge graph for the case:\n\n"
NOTE = "\n\nNote: node ids use snake_case, e.g. {\"id\": \"x\"}; edges reference node ids."


def variants(raw: str):
    fenced = f"```json\n{raw}\n```"
    yield "clean", raw
    yield "md_fence", fenced
    yield "think_block", THINK + raw
    yield "prose_wrapper", PROSE + raw + "\n\nLet me know if you need more detail."
    yield "trailing_note", raw + NOTE
    yield "think+prose+fence", THINK + PROSE + fenced
    for f in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
        cut = raw[: int(len(raw) * f)]
        yield f"trunc_{int(f * 100)}", cut
        yield f"fence+trunc_{int(f * 100)}", "```json\n" + cut


def valid_nodes(obj, ref_ids):
    if not isinstance(obj, dict):
        return 0, 0
    nodes = [n for n in obj.get("nodes", []) if isinstance(n, dict) and n.get("id") in ref_ids]
    node_ids = {n["id"] for n in nodes}
    edges = [e for e in obj.get("edges", []) if isinstance(e, dict)
             and e.get("source") in node_ids and e.get("target") in node_ids]
    return len(nodes), len(edges)


def main():
    con = sqlite3.connect(BACKEND / "court_vision.db")
    graphs = [json.loads(g) for (g,) in con.execute("select evidence_graph from cases where evidence_graph is not null")]
    rows = []
    for gi, g in enumerate(graphs):
        base = {"nodes": g["nodes"], "edges": g["edges"]}
        raw = json.dumps(base, indent=2, ensure_ascii=False)
        ref_ids = {n["id"] for n in g["nodes"]}
        n_total, e_total = len(g["nodes"]), len(g["edges"])
        for vname, text in variants(raw):
            for pname, fn in PARSERS.items():
                t0 = time.perf_counter()
                try:
                    obj = fn(text)
                    ok = True
                except Exception:
                    obj, ok = None, False
                ms = (time.perf_counter() - t0) * 1000
                nn, ne = valid_nodes(obj, ref_ids) if ok else (0, 0)
                rows.append(dict(graph=gi, variant=vname, parser=pname, parsed=ok and nn > 0,
                                 node_recovery=nn / n_total, edge_recovery=ne / e_total if e_total else 0,
                                 nodes_total=n_total, edges_total=e_total, ms=round(ms, 4)))
    out = HERE / "results" / "json_robustness.json"
    out.write_text(json.dumps(rows, indent=1))
    print(f"{len(graphs)} graphs, {len(rows)} parser runs -> {out}")
    for p in PARSERS:
        sub = [r for r in rows if r["parser"] == p]
        print(f"{p:14s} success={sum(r['parsed'] for r in sub) / len(sub):.3f} "
              f"node_rec={sum(r['node_recovery'] for r in sub) / len(sub):.3f} "
              f"edge_rec={sum(r['edge_recovery'] for r in sub) / len(sub):.3f} "
              f"mean_ms={sum(r['ms'] for r in sub) / len(sub):.4f}")


if __name__ == "__main__":
    main()
