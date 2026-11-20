"""Redraw the evaluation charts with the terminology used in the blackbook text."""
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent / "eval"
sys.path.insert(0, str(EVAL))

src = (EVAL / "analyze.py").read_text(encoding="utf-8")
REPLACE = [
    ('"S1_CV_Trunc": "CV-Trunc\\n(production)"', '"S1_CV_Trunc": "Original\\ndesign"'),
    ('"S2_CV_RAG": "CV-RAG\\n(proposed)"', '"S2_CV_RAG": "CV-RAG\\n(proposed)"'),
    ('"S3_ClosedBook": "Closed-book\\nLLM"', '"S3_ClosedBook": "AI without\\ndocuments"'),
    ('"S4_BM25_Extract": "BM25\\nextractive"', '"S4_BM25_Extract": "Keyword\\nsearch only"'),
    ('"S1_CV_Trunc": "CV-Trunc (production)"', '"S1_CV_Trunc": "Original design"'),
    ('"S3_ClosedBook": "Closed-book LLM"', '"S3_ClosedBook": "AI without documents"'),
    ('"S4_BM25_Extract": "BM25 extractive"', '"S4_BM25_Extract": "Keyword search only"'),
    ('"Answerable\\n(inside 18k window)"', '"Group A: answerable from\\nthe beginning of the file"'),
    ('"Answerable\\n(beyond 18k window)"', '"Group B: answerable only\\nfrom later pages"'),
    ('"Unanswerable\\n(correct refusal)"', '"Group C: unanswerable\\n(correctly declined)"'),
    ('"Overall task\\naccuracy (42 Qs)"', '"All 42 questions\\n(handled correctly)"'),
    ('"Accuracy vs. method (error bars: 95% Wilson CI)"', '"Accuracy by question group (error bars: 95% confidence intervals)"'),
    ('"Percentage (%)"', '"Questions handled correctly (%)"'),
    ('["Answered", "Abstained"]', '["Answered", "Declined"]'),
    ('"Answerable\\n(n=30)", "Unanswerable\\n(n=12)"', '"Answerable\\n(30 questions)", "Unanswerable\\n(12 questions)"'),
    ('"End-to-end LLM latency (s)"', '"Response time (seconds)"'),
    ('"Execution time vs. method (n = 42 queries each)"', '"Response time of each approach (42 questions each)"'),
    ('("Correct answer",', '("Correct answer",'),
    ('("Wrong answer",', '("Wrong answer",'),
    ('("Wrongly abstained",', '("Wrongly declined",'),
    ('("Correctly refused",', '("Correctly declined",'),
    ('("Hallucinated on unanswerable",', '("Invented answer",'),
    ('"Number of questions (of 42)"', '"Number of questions (out of 42)"'),
    ('"Outcome decomposition per method"', '"Outcome of the 42 questions for each approach"'),
    ('label="P0–P3 existing parsers (identical)"', 'label="Previous reading methods (all four identical)"'),
    ('label="P4 nested salvage (proposed)"', 'label="Proposed recovery method"'),
    ('"Point at which the LLM response was truncated (% of full JSON)"', '"Point at which the AI reply was cut off (% of its full length)"'),
    ('"Graph nodes recovered (%)"', '"Graph entities recovered (%)"'),
    ('"Evidence-graph recovery from truncated LLM output"', '"Recovery of graph entities from cut-off AI replies"'),
]
missing = []
for a, b in REPLACE:
    if a not in src:
        missing.append(a)
    src = src.replace(a, b)
src = src.replace('FIG = HERE.parent / "figures"', f'FIG = Path(r"{HERE / "fig"}")')
mod = types.ModuleType("analyze_bb")
mod.__file__ = str(EVAL / "analyze.py")
exec(compile(src, str(EVAL / "analyze.py"), "exec"), mod.__dict__)
latest = mod.load()
s = mod.analyse(latest)
j = mod.json_robustness()
mod.figures(s, j)
print("redrawn into", HERE / "fig", "| unmatched replacements:", missing)
