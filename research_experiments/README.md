# Court Vision AI — Research Methodology & IPR Lab (Experiments 1–10)

`docs/` holds the ten filled lab write-ups, built from the VESIT templates in `Downloads`.
Every number in Experiments 4–7 and 10 is read from `eval/results/summary.json`,
which is computed from the logged experiment runs. Nothing is typed in by hand.

## Reproduce

```bash
# 1. QA experiment (needs GROQ_API_KEY in backend/.env; ~1 h on the 8k-TPM free tier, resumable)
cd backend && ./venv/Scripts/python.exe ../research_experiments/eval/run_qa_eval.py

# 2. JSON-parser robustness experiment (offline, uses the graphs cached in court_vision.db)
cd backend && ./venv/Scripts/python.exe ../research_experiments/eval/run_json_robustness.py

# 3. Statistics + figures
cd research_experiments/eval && python analyze.py

# 4. Diagrams, then the ten .docx files
cd research_experiments && python figures_static.py && python build_docs.py
```

## Files

| Path | Purpose |
|---|---|
| `eval/qa_set.py` | CV-LegalQA-42 ground truth (A: inside 18k window, B: beyond, C: unanswerable) and abstention patterns |
| `eval/run_qa_eval.py` | S1 CV-Trunc (production prompt + truncation), S2 CV-RAG (proposed), S3 closed-book, S4 BM25 extractive |
| `eval/run_json_robustness.py` | Parsers P0–P3 from the code base vs. the P4 nested-object salvage parser on 66 corrupted LLM outputs |
| `eval/analyze.py` | Scoring, Wilson CIs, McNemar, Wilcoxon, Cochran's Q, citation accuracy, figures |
| `eval/results/` | Raw `qa_results.jsonl`, `json_robustness.json`, `summary.json`, run log |
| `docgen.py`, `content_a.py`, `content_b.py`, `build_docs.py` | Fill the lab templates (python-docx) |
| `render_check.py` | Word → PDF → PNG page previews for visual QA |

Note: the free-tier daily token limit (200k TPD) ran out with 12 S1 questions left. Those 12 and the
module smoke test ran on a second Groq key with the same model and parameters.

## Things to fill in by hand

- The group table (group no., roll no., division, names) in each document.
- Author names in the Exp 6 paper, the applicant/author fields in Exp 9, and the faculty-review rows in Exp 7.
- The similarity percentage from the official plagiarism tool (Exp 7).
- Confirming the InPASS / IP India searches directly on the portals (Exp 8, 9).

## Bug found in the app during the experiments

`backend/app/api/routes/graph.py::_extract_json` claims to recover truncated JSON, but its
fallback only collects objects that close at nesting depth 0. When max_tokens cuts off a
response, the outer `{` never closes, so nothing is recovered (0/48 truncated inputs).
`P4` in `eval/run_json_robustness.py` is a drop-in fix.
