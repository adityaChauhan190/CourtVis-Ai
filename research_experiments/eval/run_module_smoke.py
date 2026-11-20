"""
Experiment 4C — module-level functional validation of the live Court Vision API.

Calls every AI module once on the stored Jacob Mathew case through FastAPI's TestClient
(dev auth) and records HTTP status, latency and a short shape check of each response.
Run from backend/:  ./venv/Scripts/python.exe ../research_experiments/eval/run_module_smoke.py
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

import logging  # noqa: E402
logging.disable(logging.WARNING)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

CASE = "7205352d-9ee1-45c8-8ce5-ba96a597f9d7"
client = TestClient(app)


def call(name, method, url, check, **kw):
    t0 = time.perf_counter()
    r = getattr(client, method)(url, **kw)
    dt = time.perf_counter() - t0
    try:
        body = r.json()
    except Exception:
        body = r.text
    ok = r.status_code == 200 and check(body)
    print(f"{name:28s} {r.status_code} {dt:6.2f}s ok={ok}", flush=True)
    time.sleep(8)  # stay under the 8k TPM limit between modules
    return dict(module=name, status=r.status_code, latency_s=round(dt, 2), ok=ok,
                detail=check.__doc__ or "", sample=(json.dumps(body)[:300] if not isinstance(body, str) else body[:300]))


def main():
    rows = [
        call("Health", "get", "/health", lambda b: b.get("database") == "connected"),
        call("Case documents", "get", f"/api/cases/{CASE}/documents",
             lambda b: b["total"] >= 1 and b["documents"][0]["status"] == "ready" and b["documents"][0]["page_count"] == 20),
        call("Structured summary", "get", f"/api/cases/{CASE}/summary", lambda b: b["has_documents"] and len(b["key_issues"]) > 0 and not b["overview"].startswith("Landmark criminal medical negligence proceedings")),  # not the hardcoded fallback
        call("Grounded chat", "post", f"/api/cases/{CASE}/chat",
             lambda b: b["has_documents"] and "ludhiana" in b["answer"].lower(),
             json={"message": "In which hospital and city was the patient admitted?", "conversation_history": []}),
        call("Evidence graph (cached)", "get", f"/api/cases/{CASE}/graph", lambda b: len(b["nodes"]) > 0 and len(b["edges"]) > 0),
        call("Virtual courtroom turn", "post", f"/api/cases/{CASE}/courtroom",
             lambda b: b["judge_response"] and b["opposing_response"].startswith("OPPOSING"),
             json={"statement": "My Lord, the empty oxygen cylinder was a hospital failure, not the appellant's negligence.",
                   "phase": "arguments", "judge_temperament": "strict", "session_history": []}),
        call("Courtroom verdict", "post", f"/api/cases/{CASE}/courtroom/verdict",
             lambda b: b["scorecard"] is not None and b["verdict"] != "Matter Adjourned / Inconclusive",  # not the fallback
             json={"session_history": [{"speaker": "lawyer", "content": "No expert medical opinion was obtained before prosecution, contrary to Bolam."}]}),
        call("Trial brief", "get", f"/api/cases/{CASE}/trial-brief", lambda b: len(b["chronology"]) > 0 and bool(b["synopsis"]) and "02 Jul 1995" not in json.dumps(b)),  # not the fallback
        call("Precedent research", "post", "/api/research/query", lambda b: len(b["precedents"]) > 0,
             json={"query": "criminal medical negligence Section 304A gross negligence", "jurisdiction": "Supreme Court of India"}),
    ]
    out = HERE / "results" / "module_smoke.json"
    out.write_text(json.dumps(rows, indent=1))
    print(f"{sum(r['ok'] for r in rows)}/{len(rows)} modules passed -> {out}")


if __name__ == "__main__":
    main()
