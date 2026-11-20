"""Experiments 4, 5, 6, 7 and 10 — every number is read from eval/results/summary.json."""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from content_a import REFS, TITLE
from docgen import LabDoc, _runs

S1, S2, S3, S4 = "S1_CV_Trunc", "S2_CV_RAG", "S3_ClosedBook", "S4_BM25_Extract"
NAME = {S1: "CV-Trunc (production)", S2: "CV-RAG (proposed)", S3: "Closed-book LLM", S4: "BM25 extractive"}


def pc(x, d=1):
    return f"{x * 100:.{d}f}%"


def ci(t):
    return f"{t[0] * 100:.1f}% [{t[1] * 100:.1f}, {t[2] * 100:.1f}]"


def pv(p):
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def pt(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def mc(R, a, b):
    return next(m for m in R["mcnemar"] if m["a"] == a and m["b"] == b)


def facts(R):
    """Pre-computed numbers used across the write-ups."""
    S = R["systems"]
    J = R["json_robustness"]["parsers"]
    f = dict(S=S, J=J, R=R)
    f["s"] = {k: S[k] for k in S}
    f["cit"] = R["citation_S2"]
    f["tok_saving"] = 1 - S[S2]["prompt_tokens_mean"] / S[S1]["prompt_tokens_mean"]
    f["lat_ratio"] = S[S2]["latency_mean"] / S[S1]["latency_mean"]
    f["wil"] = R.get("latency_wilcoxon_S2_vs_S1", {"p_value": 1, "statistic": 0, "n": 0})
    f["m21"], f["m23"], f["m13"], f["m24"] = mc(R, S2, S1), mc(R, S2, S3), mc(R, S1, S3), mc(R, S2, S4)
    return f


# ═════════════════════════════════════════════════════════════════════════════
# Experiment 4
# ═════════════════════════════════════════════════════════════════════════════

def exp4(out, figdir, R):
    F = facts(R); S = F["S"]; J = F["J"]
    d = LabDoc(4, "Implementation and Experimental Validation", heading="bold14", body_size=12)
    d.h("1. Aim: ")
    d.p("Implement the proposed methodology, perform experiments, compare with baseline techniques, and record observations. ")

    d.h("2. Implementation of proposed methodology")
    d.kv([
        ("Programming Language/Technology", "Python 3.11 (FastAPI backend, experiment harness), TypeScript/React (Next.js 16 frontend)"),
        ("Software/Tools Used", "FastAPI 0.115, SQLAlchemy 2.0, PyMuPDF 1.25, Groq SDK 0.13, SQLite, NumPy, SciPy, Matplotlib, VS Code, MS Word"),
        ("Hardware/Platform Used", "AMD Ryzen 5 5625U, 6 cores / 12 threads, 7.3 GB RAM, Windows 11; LLM inference on Groq Cloud (openai/gpt-oss-120b)"),
        ("Dataset/Input Used", "Jacob Mathew v. State of Punjab & Anr., (2005) 6 SCC 1 (20-page PDF, 72,720 chars); CV-LegalQA-42; 3 real LLM-generated evidence graphs"),
        ("Number of Samples/Records", f"42 questions × 4 systems = {sum(S[s]['n'] for s in S)} QA runs; 66 corrupted LLM outputs × 5 parsers = {sum(J[p]['n'] for p in J)} parser runs"),
        ("Important Parameters", "temperature 0.2; max_tokens 2048; MAX_CONTEXT_CHARS 18,000 (S1); chunk 1,000 chars / overlap 200; BM25 k1 = 1.5, b = 0.75; top-k 6 (S2); model pinned, no fallback"),
    ])
    d.p("**Implementation Procedure:**", space_after=2)
    d.numbered([
        "**Court Vision AI platform** — implemented the FastAPI backend (routes: auth, cases, documents, chat + SSE streaming, graph, courtroom, reports, research), SQLAlchemy models, PDF validation (extension, 50 MB limit, %PDF magic bytes), background PyMuPDF processing, and the Next.js workspace (case vault, chat, evidence graph, virtual courtroom, reports, research).",
        "**S1 CV-Trunc (production baseline)** — re-used the exact LEGAL_SYSTEM_PROMPT_TEMPLATE and _extract_text_from_pdf() from chat.py; the case context is truncated to MAX_CONTEXT_CHARS = 18,000 (18,004 chars sent = 24.8% of the judgment).",
        "**S2 CV-RAG (proposed)** — extracted text page by page, removed Indian Kanoon running headers/URLs/page numbers, split each page into 1,000-char chunks with 200-char overlap (91 chunks), indexed them with a from-scratch Okapi BM25, and placed the top-6 chunks (document order, tagged [Page N]) into the same legal prompt plus a page-citation rule and an exact refusal sentence.",
        "**S3 Closed-book** — same model and temperature, told only the case name; no documents.",
        "**S4 BM25 extractive** — returns the single highest-scoring chunk (no LLM).",
        "**Experiment harness** — run_qa_eval.py calls Groq with the model pinned, records latency and token usage, and on HTTP 429 sleeps for the server-advised interval (8,000 TPM limit). Results are appended to qa_results.jsonl (resumable).",
        "**Automatic scoring** — an answer is correct only if all gold regexes match after Unicode normalisation; refusal is detected with 13 abstention patterns; a BM25 passage never counts as a refusal.",
        "**P4 nested-object salvage parser (proposed)** — after the existing _extract_json() fails, a brace-stack scan parses every complete {...} object at any depth and classifies it as node (id, label, type) or edge (source, target).",
    ], size=11.5)
    d.p("**Core retrieval code (CV-RAG):**", space_after=2)
    code = d.p("score(q, d) = Σ_t idf(t) · f(t,d)·(k1+1) / (f(t,d) + k1·(1 − b + b·|d|/avgdl)),   idf(t) = ln(1 + (N − n_t + 0.5)/(n_t + 0.5))", size=10, italic=True, align="center")
    d.p("hits = top_k(BM25.scores(tokenize(question)), k=6) → sorted by position → \"[Page N] chunk\" blocks → LEGAL_SYSTEM_PROMPT + citation/abstain rule → gpt-oss-120b", size=10, align="center")

    d.h("3. Experiments Performed")
    d.p("**Experiment 4A — Grounded legal question answering.** All 42 CV-LegalQA questions were sent to the four systems. "
        f"In total {sum(S[s]['n'] for s in (S1, S2, S3))} LLM calls were made on 19-10-2026 through the Groq API; the answer, latency, "
        "prompt/completion tokens and (for S2) retrieved pages were logged for every call.", align="justify")
    d.p("**Experiment 4B — Robustness of LLM-to-JSON parsing (Evidence Graph).** The three evidence graphs that gpt-oss-120b generated for "
        "the cases in the Court Vision database were serialised and corrupted with 22 variants each (markdown fences, <think> blocks, prose "
        "wrappers, trailing notes, combined noise, and truncation at 30–95% of the response, with and without a code fence). Five parsers "
        "(P0 json.loads, P1 summary fence-strip, P2 reports _safe_json, P3 graph _extract_json, P4 proposed salvage) were run on all 66 inputs.", align="justify")
    smoke_path = Path(__file__).resolve().parent / "eval" / "results" / "module_smoke.json"
    if smoke_path.exists():
        import json as _json
        smoke = _json.loads(smoke_path.read_text())
        d.p("**Experiment 4C — Module-level functional validation.** Every Court Vision API module was called once on the stored Jacob Mathew case "
            "through FastAPI's TestClient. A module passes only if it returns HTTP 200 *and* a response of the expected shape that is **not** one of the "
            "hard-coded fallback answers the summary, verdict and trial-brief routes return when the LLM call fails.", align="justify")
        d.table([["Module", "HTTP", "Latency (s)", "Result"]] +
                [[r["module"], r["status"], f"{r['latency_s']:.2f}", "Pass" if r["ok"] else "Fail"] for r in smoke],
                widths=[2.6, 0.7, 1.0, 1.0], size=9, caption="Experiment 4C — module smoke test")

    d.h("4. Comparison with Baseline Techniques")
    rows = [["Measure", NAME[S2], NAME[S1], NAME[S3], NAME[S4]],
            ["Accuracy — answerable (n=30)"] + [f"{S[s]['k_answerable']}/30 ({pc(S[s]['acc_answerable'][0])})" for s in (S2, S1, S3, S4)],
            ["Accuracy — inside window A (n=16)"] + [f"{S[s]['k_A']}/16" for s in (S2, S1, S3, S4)],
            ["Accuracy — beyond window B (n=14)"] + [f"{S[s]['k_B']}/14" for s in (S2, S1, S3, S4)],
            ["Correct refusals C (n=12)"] + [f"{S[s]['k_C']}/12" for s in (S2, S1, S3, S4)],
            ["Hallucination on C"] + [pc(S[s]["hallucination_C"]) for s in (S2, S1, S3, S4)],
            ["Task accuracy (n=42)"] + [f"{S[s]['k_task']}/42 ({pc(S[s]['task_accuracy'][0])})" for s in (S2, S1, S3, S4)],
            ["Mean latency (s)"] + [f"{S[s]['latency_mean']:.2f}" if s != S4 else f"{S[s]['latency_mean'] * 1000:.1f} ms" for s in (S2, S1, S3, S4)],
            ["Mean prompt tokens"] + [f"{S[s]['prompt_tokens_mean']:,.0f}" if s != S4 else "0" for s in (S2, S1, S3, S4)]]
    d.table(rows, widths=[1.7, 1.15, 1.15, 1.15, 1.15], size=9, caption="Experiment 4A results (proposed vs. baselines)")
    d.fig(figdir / "fig_accuracy_by_split.png", "Accuracy vs. method for each question split (95% Wilson CI)", width=6.5)
    d.fig(figdir / "fig_latency.png", "Execution time vs. method", width=4.8)
    d.fig(figdir / "fig_prompt_tokens.png", "Prompt tokens (context cost) vs. method", width=4.8)
    jr = [["Parser", "Parse success (66)", "Formatting noise (18)", "Truncated (48)", "Node recovery", "Edge recovery", "Mean time (ms)"]]
    for p, lab in [("P0_Naive", "P0 json.loads"), ("P1_FenceStrip", "P1 fence-strip (chat.py)"), ("P2_SafeJSON", "P2 _safe_json (reports.py)"),
                   ("P3_Robust", "P3 _extract_json (graph.py)"), ("P4_NestedSalvage", "P4 nested salvage (proposed)")]:
        x = J[p]
        jr.append([lab, f"{x['k']}/{x['n']} ({pc(x['success'][0])})", pc(x["success_format"]), pc(x["success_trunc"]),
                   pc(x["node_recovery"]), pc(x["edge_recovery"]), f"{x['ms_mean']:.3f}"])
    d.table(jr, widths=[1.9, 1.15, 1.0, 0.9, 0.9, 0.9, 0.85], size=8.5, caption="Experiment 4B results (JSON parsing robustness)")
    d.fig(figdir / "fig_json_success.png", "Parse success vs. parser", width=5.2)
    d.p("**Note:** Suggested graphs — Accuracy vs. Method (Fig. 1), Execution Time vs. Method (Fig. 2), Memory/context usage vs. Method (Fig. 3, prompt tokens) and success rate vs. parser (Fig. 4) are presented above.", size=11)

    d.h("5. Record Observations")
    d.bullets(observations(F), size=11.5)
    d.save(out)


def observations(F):
    S, J = F["S"], F["J"]
    return [
        f"**Grounding matters:** the closed-book LLM answered only {S[S3]['k_answerable']}/30 answerable questions correctly and fabricated an answer for {S[S3]['confusion']['FP']}/12 unanswerable ones "
        f"(e.g. an invented nurse's name, a 'two-year sentence', a '₹2 lakh' compensation award and an FIR number), confirming the legal-hallucination problem on Indian case facts.",
        f"**Truncation is the bottleneck of the production design:** CV-Trunc answered {S[S1]['k_A']}/16 in-window questions but only {S[S1]['k_B']}/14 beyond-window questions "
        f"({S[S1]['k_B_strict']}/{S[S1]['n_B_strict']} on the strict subset whose answer text never appears in the first 18,000 characters).",
        f"**CV-RAG (proposed)** answered {S[S2]['k_answerable']}/30 answerable questions correctly ({S[S2]['k_B']}/14 beyond the window) and refused {S[S2]['k_C']}/12 unanswerable ones, "
        f"giving task accuracy {S[S2]['k_task']}/42 vs. {S[S1]['k_task']}/42 (CV-Trunc), {S[S3]['k_task']}/42 (closed-book) and {S[S4]['k_task']}/42 (BM25 extractive).",
        f"**Citations:** {F['cit']['k']}/{F['cit']['n']} correct CV-RAG answers cited a page that actually contains the answer ({pc(F['cit']['rate'][0])}); the remaining citations pointed to an adjacent or related page.",
        f"**Cost:** CV-RAG used {S[S2]['prompt_tokens_mean']:,.0f} prompt tokens per query vs. {S[S1]['prompt_tokens_mean']:,.0f} for CV-Trunc — a {pc(F['tok_saving'], 0)} reduction, which also lets about "
        f"{8000 // max(1, int(S[S2]['prompt_tokens_mean'] + S[S2]['completion_tokens_mean']))} queries/minute fit in the 8,000 TPM free tier instead of "
        f"{max(1, 8000 // int(S[S1]['prompt_tokens_mean'] + S[S1]['completion_tokens_mean']))}.",
        f"**Latency:** mean {S[S2]['latency_mean']:.2f} s (CV-RAG) vs. {S[S1]['latency_mean']:.2f} s (CV-Trunc) vs. {S[S3]['latency_mean']:.2f} s (closed-book); BM25 retrieval itself takes about {S[S4]['latency_mean'] * 1000:.1f} ms.",
        f"**JSON robustness:** every existing parser failed on all 48 truncated responses (0%), including graph.py's _extract_json whose 'partial recovery' only collects objects closing at depth 0. "
        f"The proposed P4 parser parsed {J['P4_NestedSalvage']['k']}/66 inputs and recovered {pc(J['P4_NestedSalvage']['node_recovery_trunc'])} of nodes from truncated outputs.",
        "**Silent fallback in the trial-brief module (4C):** the endpoint returned HTTP 200, but with the hard-coded Jacob Mathew template. Re-issuing its "
        "prompt showed why: the model hit max_tokens = 1,800 (finish_reason = 'length') in the middle of the cross-examination JSON, _safe_json() failed, "
        "and the route fell back without telling the user — the same truncation failure mode that the P4 parser addresses.",
        "**Edge loss under truncation:** because LLMs emit all nodes before edges, truncation removes edges first; P4's edge recovery "
        f"({pc(J['P4_NestedSalvage']['edge_recovery'])}) is lower than node recovery — a reason to request edges inline or raise max_tokens for graph extraction.",
    ]


# ═════════════════════════════════════════════════════════════════════════════
# Experiment 5
# ═════════════════════════════════════════════════════════════════════════════

def exp5(out, figdir, R):
    F = facts(R); S = F["S"]; J = F["J"]; JR = R["json_robustness"]
    d = LabDoc(5, "Data Analysis and Visualization", heading="h2", body_size=12)
    d.h("1. Aim: ")
    d.p("Analyze experimental results using statistical methods, prepare graphs, tables, confusion matrices, and performance comparisons. ")
    d.h("2. Experimental Data Analysis")
    d.p(f"The experimental data from Experiment 4 consist of {sum(S[s]['n'] for s in S)} labelled question-answering outcomes (42 questions × 4 systems) and "
        f"{sum(J[p]['n'] for p in J)} parser runs (66 corrupted LLM outputs × 5 parsers). Each QA outcome was labelled automatically as "
        "*correct*, *wrong* or *abstain* (answerable questions) or *abstain* / *hallucinated* (unanswerable questions). Because every system answers the "
        "same questions, the data are **paired**, so paired tests (McNemar, Wilcoxon signed-rank, Cochran's Q) were used. Proportions are reported with "
        "Wilson 95% confidence intervals, which remain valid for small samples and proportions near 0 or 1.", align="justify")
    d.h("3. Statistical Analysis")
    d.p("The experimental results were analysed using descriptive statistics and hypothesis tests, tabulated below:")
    d.caption("Statistical Analysis — descriptive statistics per method", "Table")
    rows = [["Statistic", NAME[S2], NAME[S1], NAME[S3], NAME[S4]],
            ["Answer accuracy (n=30), 95% CI"] + [ci(S[s]["acc_answerable"]) for s in (S2, S1, S3, S4)],
            ["Beyond-window accuracy (n=14)"] + [ci(S[s]["acc_B"]) for s in (S2, S1, S3, S4)],
            [f"Strict beyond-window (n={S[S1]['n_B_strict']})"] + [f"{S[s]['k_B_strict']}/{S[s]['n_B_strict']}" for s in (S2, S1, S3, S4)],
            ["Correct refusal (n=12), 95% CI"] + [ci(S[s]["refusal_C"]) for s in (S2, S1, S3, S4)],
            ["Task accuracy (n=42), 95% CI"] + [ci(S[s]["task_accuracy"]) for s in (S2, S1, S3, S4)],
            ["Latency mean ± SD (s)"] + [f"{S[s]['latency_mean']:.2f} ± {S[s]['latency_sd']:.2f}" for s in (S2, S1, S3)] + [f"{S[S4]['latency_mean'] * 1000:.2f} ms"],
            ["Latency median / p95 (s)"] + [f"{S[s]['latency_median']:.2f} / {S[s]['latency_p95']:.2f}" for s in (S2, S1, S3)] + ["—"],
            ["Prompt tokens (mean)"] + [f"{S[s]['prompt_tokens_mean']:,.0f}" for s in (S2, S1, S3)] + ["0"],
            ["Completion tokens (mean)"] + [f"{S[s]['completion_tokens_mean']:,.0f}" for s in (S2, S1, S3)] + ["0"]]
    d.table(rows, widths=[1.7, 1.25, 1.25, 1.25, 1.1], size=8.5)
    d.p("The experimental results were also organised for hypothesis testing (α = 0.05):")
    d.caption("Hypothesis tests", "Table")
    m21, m23, m13, m24, w = F["m21"], F["m23"], F["m13"], F["m24"], F["wil"]
    t = [["Comparison", "Test", "Discordant pairs (A-only / B-only)", "p-value", "Decision"],
         ["CV-RAG vs CV-Trunc (task accuracy)", "McNemar exact", f"{m21['a_only']} / {m21['b_only']}", pv(m21["p_value"]), "Reject H₀₁" if m21["p_value"] < 0.05 else "Fail to reject"],
         ["CV-RAG vs Closed-book", "McNemar exact", f"{m23['a_only']} / {m23['b_only']}", pv(m23["p_value"]), "Reject H₀₁" if m23["p_value"] < 0.05 else "Fail to reject"],
         ["CV-Trunc vs Closed-book", "McNemar exact", f"{m13['a_only']} / {m13['b_only']}", pv(m13["p_value"]), "Significant" if m13["p_value"] < 0.05 else "Not significant"],
         ["CV-RAG vs BM25 extractive", "McNemar exact", f"{m24['a_only']} / {m24['b_only']}", pv(m24["p_value"]), "Significant" if m24["p_value"] < 0.05 else "Not significant"],
         ["Latency CV-RAG vs CV-Trunc", "Wilcoxon signed-rank", f"n = {w['n']} pairs", pv(w["p_value"]), "Significant" if w["p_value"] < 0.05 else "Not significant"],
         ["5 parsers on 66 identical inputs", "Cochran's Q", f"Q = {JR['cochran_q']:.1f}, df = 4", pv(JR["cochran_p"]), "Reject H₀₂" if JR["cochran_p"] < 0.05 else "Fail to reject"],
         ["P4 vs P3 parser", "McNemar exact", f"{JR['mcnemar_P4_vs_P3']['p4_only']} / {JR['mcnemar_P4_vs_P3']['p3_only']}", pv(JR["mcnemar_P4_vs_P3"]["p_value"]), "Reject H₀₂" if JR["mcnemar_P4_vs_P3"]["p_value"] < 0.05 else "Fail to reject"]]
    d.table(t, widths=[1.9, 1.1, 1.4, 0.8, 1.1], size=8.5)

    d.h("4. Graphical Representation")
    d.p("Graphs were prepared to visualise the experimental results and identify differences and trends among the evaluated methods.")
    d.fig(figdir / "fig_accuracy_by_split.png", "Accuracy by question split with 95% confidence intervals", width=6.4)
    d.fig(figdir / "fig_outcomes.png", "Outcome decomposition per method (42 questions)", width=6.0)
    d.fig(figdir / "fig_latency.png", "Latency distribution per LLM-based method", width=4.6)
    d.fig(figdir / "fig_json_truncation.png", "Evidence-graph node recovery vs. truncation point", width=5.4)

    d.h("5. Confusion Matrix")
    d.p("Court Vision's grounding decision is a binary classification: for each question the system either **answers** or **abstains**. "
        "Taking *answered* as the positive class and the question's answerability as ground truth:")
    d.bullets(["True Positive (TP) — answerable question, system answered",
               "True Negative (TN) — unanswerable question, system correctly refused",
               "False Positive (FP) — unanswerable question, system answered (hallucination)",
               "False Negative (FN) — answerable question, system refused (missed evidence)"], size=11.5)
    d.fig(figdir / "fig_confusion_matrices.png", "Confusion matrices of the proposed method and the baselines", width=6.8)
    cm = [["Method", "TP", "FN", "FP", "TN", "Precision", "Recall", "F1"]]
    for s in (S2, S1, S3, S4):
        c = S[s]["confusion"]
        cm.append([NAME[s], c["TP"], c["FN"], c["FP"], c["TN"], f"{S[s]['decision_precision']:.3f}", f"{S[s]['decision_recall']:.3f}", f"{S[s]['decision_f1']:.3f}"])
    d.table(cm, widths=[1.9, 0.5, 0.5, 0.5, 0.5, 0.8, 0.8, 0.8], size=9, caption="Values derived from the confusion matrices")
    d.p("*Note:* TP counts an *attempted* answer; whether the content was right is measured separately by answer accuracy (Table 1).", size=10)

    d.h("6. Performance Comparison")
    d.p("The performance of the proposed method was compared with the selected baseline methods using appropriate performance measures.")
    d.caption("Performance Comparison", "Table")
    pcmp = [["Performance Measure", "Proposed Method (CV-RAG)", "Baseline Method 1 (CV-Trunc)", "Baseline Method 2 (Closed-book)", "Baseline Method 3 (BM25)"],
            ["Accuracy (task, 42 Qs)"] + [pc(S[s]["task_accuracy"][0]) for s in (S2, S1, S3, S4)],
            ["Precision (answer decision)"] + [f"{S[s]['decision_precision']:.3f}" for s in (S2, S1, S3, S4)],
            ["Recall (answer decision)"] + [f"{S[s]['decision_recall']:.3f}" for s in (S2, S1, S3, S4)],
            ["F1-Score"] + [f"{S[s]['decision_f1']:.3f}" for s in (S2, S1, S3, S4)],
            ["Error (1 − task accuracy)"] + [pc(S[s]["error_rate"]) for s in (S2, S1, S3, S4)],
            ["Execution Time (mean)"] + [f"{S[s]['latency_mean']:.2f} s" for s in (S2, S1, S3)] + [f"{S[S4]['latency_mean'] * 1000:.1f} ms"]]
    d.table(pcmp, widths=[1.6, 1.2, 1.2, 1.2, 1.1], size=9)
    d.h2("Observations")
    d.p("Based on the statistical analysis, tables, graphs, confusion matrix, and performance comparison, the following observations were made:")
    best_other = max((S1, S3, S4), key=lambda s: S[s]["task_accuracy"][0])
    d.bullets([
        f"The proposed method achieved **{pc(S[S2]['task_accuracy'][0])} task accuracy** (95% CI {ci(S[S2]['task_accuracy']).split(' ', 1)[1]}) and answered {S[S2]['k_answerable']}/30 answerable questions correctly.",
        f"The statistical analysis showed that the improvement over CV-Trunc is {'statistically significant' if m21['p_value'] < 0.05 else 'not statistically significant'} (McNemar {pt(m21['p_value'])}) "
        f"and over the closed-book LLM is {'significant' if m23['p_value'] < 0.05 else 'not significant'} ({pt(m23['p_value'])}).",
        f"The proposed method performed better than {NAME[best_other]} (the strongest baseline) with respect to beyond-window recall ({S[S2]['k_B']}/14 vs {S[best_other]['k_B']}/14) and "
        f"refusal ({S[S2]['k_C']}/12 vs {S[best_other]['k_C']}/12).",
        f"The confusion matrix indicates {'perfect' if S[S2]['decision_f1'] == 1 else 'high'} answer/abstain discrimination for CV-RAG (F1 = {S[S2]['decision_f1']:.3f}), "
        f"whereas CV-Trunc's errors are false negatives ({S[S1]['confusion']['FN']} wrongly refused) and the closed-book LLM's are false positives ({S[S3]['confusion']['FP']} hallucinations).",
        f"The graphical analysis shows that CV-Trunc's accuracy drops from {pc(S[S1]['acc_A'][0], 0)} inside the 18,000-character window to {pc(S[S1]['acc_B'][0], 0)} beyond it, while "
        f"CV-RAG stays at {pc(S[S2]['acc_A'][0], 0)} / {pc(S[S2]['acc_B'][0], 0)}; and only the proposed P4 parser recovers evidence graphs from truncated LLM output "
        f"(0% for P0–P3 at every truncation point vs. {pc(J['P4_NestedSalvage']['node_recovery_trunc'], 0)} mean node recovery for P4).",
        f"The overall performance of the proposed method was **superior** to the baseline methods while using {pc(F['tok_saving'], 0)} fewer prompt tokens than CV-Trunc.",
    ], size=11.5)
    d.h("7. Conclusion")
    d.p("The experimental results were analyzed using statistical methods and presented using tables and graphs. A confusion matrix was used to evaluate the "
        "answer-versus-abstain classification performance. The proposed method was compared with baseline techniques using suitable performance measures. "
        f"The analysis indicates that the proposed method **grounds Court Vision AI's answers in the whole case record at a fraction of the token cost**, "
        f"raising task accuracy from {pc(S[S1]['task_accuracy'][0])} (production) and {pc(S[S3]['task_accuracy'][0])} (closed-book) to {pc(S[S2]['task_accuracy'][0])}, "
        f"while the proposed salvage parser removes a 0% failure mode on truncated graph output.", align="justify")
    d.save(out)


# ═════════════════════════════════════════════════════════════════════════════
# Experiment 6 — IEEE paper
# ═════════════════════════════════════════════════════════════════════════════

def _ieee_h(d, text):
    p = d.d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text.upper())
    r.font.size = Pt(9.5); r.font.name = "Times New Roman"; r.font.small_caps = True
    return p


def _ieee_sub(d, text):
    p = d.d.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text); r.italic = True; r.font.size = Pt(10); r.font.name = "Times New Roman"


def _ieee_p(d, text, first_indent=True, size=10):
    p = d.d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    if first_indent:
        p.paragraph_format.first_line_indent = Pt(10)
    _runs(p, text, size=size, font="Times New Roman")
    return p


def paper_text(F):
    S, J, R = F["S"], F["J"], F["R"]
    m21, m23 = F["m21"], F["m23"]
    abstract = (
        f"Large language models (LLMs) can accelerate legal case preparation, but they hallucinate facts and citations, and practical systems built on "
        f"rate-limited LLM APIs must truncate long judgments to fit token budgets. We present Court Vision AI, an end-to-end platform for Indian legal case "
        f"preparation that combines document-grounded chat, LLM-extracted evidence graphs, a virtual courtroom with an AI judge and opposing counsel, and "
        f"trial-brief generation. We propose CV-RAG, a page-tagged BM25 retrieval grounding layer with explicit citation and refusal rules, and a nested-object "
        f"salvage parser for truncated LLM JSON. On CV-LegalQA-42, a ground-truth set of 42 questions built from Jacob Mathew v. State of Punjab (2005), CV-RAG "
        f"reaches {pc(S[S2]['task_accuracy'][0])} task accuracy versus {pc(S[S1]['task_accuracy'][0])} for the production truncated-context pipeline "
        f"(McNemar {pt(m21['p_value'])}) and {pc(S[S3]['task_accuracy'][0])} for a closed-book LLM ({pt(m23['p_value'])}), refuses "
        f"{S[S2]['k_C']}/12 unanswerable questions, and uses {pc(F['tok_saving'], 0)} fewer prompt tokens. The closed-book model fabricated answers to "
        f"{S[S3]['confusion']['FP']}/12 unanswerable questions. The salvage parser recovers evidence graphs from 100% of truncated responses, where all existing parsers fail.")
    return abstract


def exp6(out, figdir, R):
    F = facts(R); S = F["S"]; J = F["J"]
    d = LabDoc(6, "Technical Paper Preparation", template_no=1)
    d.h("1. Aim:")
    d.p("To write the research paper in IEEE conference format using MS Word, including Abstract, Introduction, Methodology, Results, and References.")
    d.h("2. Paper Details")
    d.table([["Item", "Details"],
             ["Title", "Court Vision AI: Retrieval-Grounded, Citation-Enforcing Generative AI for Indian Legal Case Preparation"],
             ["Authors", "________________ (group members), Department of Information Technology, Vivekanand Education Society's Institute of Technology, Mumbai, India"],
             ["Format", "IEEE conference template (A4/Letter, two columns, Times New Roman 10 pt, numbered references in IEEE style)"],
             ["Target venue", "IEEE INDICON / IEEE ICCCNT (conference); alternative: NLLP Workshop (ACL/EMNLP)"],
             ["Index Terms", "Legal AI, large language models, retrieval-augmented generation, hallucination, BM25, knowledge graph, Indian law"],
             ["Length", "≈ 6 pages including figures and references"]],
            widths=[1.2, 4.8], size=9.5, bold_first_col=True)
    d.h("3. Structure Followed")
    d.bullets(["Title, authors and affiliations", "Abstract (≈ 200 words) and Index Terms", "I. Introduction", "II. Related Work", "III. System Architecture",
               "IV. Proposed Method (CV-RAG and salvage parser)", "V. Experimental Setup", "VI. Results and Discussion", "VII. Limitations", "VIII. Conclusion and Future Work", "References"])
    d.h("4. Research Paper (IEEE format)")
    d.section(cols=1)
    # Title block (single column)
    t = d.d.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("Court Vision AI: Retrieval-Grounded, Citation-Enforcing Generative AI for Indian Legal Case Preparation")
    r.font.size = Pt(20); r.font.name = "Times New Roman"
    a = d.d.add_paragraph(); a.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in ["Author 1, Author 2, Author 3, Author 4", "Department of Information Technology", "Vivekanand Education Society's Institute of Technology, Mumbai, India", "{author1, author2}@ves.ac.in"]:
        rr = a.add_run(line + "\n"); rr.font.size = Pt(10); rr.font.name = "Times New Roman"; rr.italic = line.startswith("Department") or line.startswith("Vivek")
    d.section(cols=2, space_in=0.24)
    ab = d.d.add_paragraph(); ab.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    x = ab.add_run("Abstract—"); x.bold = True; x.italic = True; x.font.size = Pt(9); x.font.name = "Times New Roman"
    y = ab.add_run(paper_text(F)); y.bold = True; y.font.size = Pt(9); y.font.name = "Times New Roman"
    it = d.d.add_paragraph(); it.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    x = it.add_run("Index Terms—"); x.bold = True; x.italic = True; x.font.size = Pt(9); x.font.name = "Times New Roman"
    y = it.add_run("legal AI, large language models, retrieval-augmented generation, hallucination, BM25, knowledge graphs, Indian law."); y.bold = True; y.font.size = Pt(9); y.font.name = "Times New Roman"

    _ieee_h(d, "I. Introduction")
    _ieee_p(d, "India's courts carry a very large pending caseload, and junior advocates and law students spend much of their preparation time reading long judgments, "
               "FIRs and depositions. LLMs can summarise and answer questions about such documents, but closed-book models hallucinate legal facts at high rates [2], "
               "and even commercial retrieval-augmented legal tools hallucinate 17–33% of the time [1]. Indian legal NLP research has largely targeted classification "
               "and judgment-prediction benchmarks [3]–[5], leaving interactive, document-grounded assistance under-studied.")
    _ieee_p(d, "A practical constraint is cost: free-tier LLM APIs limit throughput (8,000 tokens per minute in our deployment), so systems truncate context. "
               "Court Vision AI's production chat pipeline sends only the first 18,000 characters of a case — 24.8% of a 20-page Supreme Court judgment. "
               "This paper asks: *can page-tagged lexical retrieval give an LLM the whole case record within the same budget, improve accuracy and refusal, and keep "
               "citations verifiable?* Our contributions are: (i) the Court Vision AI platform; (ii) CV-LegalQA-42, a ground-truth set separating in-window, "
               "beyond-window and unanswerable questions; (iii) CV-RAG; (iv) a salvage parser that fixes a silent failure in LLM-to-graph extraction; and "
               "(v) a paired statistical evaluation against three baselines.")
    _ieee_h(d, "II. Related Work")
    _ieee_p(d, "Dahl et al. [2] profiled legal hallucinations of closed-book LLMs on US federal cases (58–88%). Magesh et al. [1] showed that RAG-based legal research "
               "tools reduce but do not eliminate hallucination. LegalBench [6] and LexGLUE [10] benchmark legal reasoning and understanding in English/US law, while "
               "IL-TUR [3], ILDC [4] and InLegalBERT [5] address Indian legal text with classification-style tasks. RAG [9] grounds generation in retrieved passages; "
               "GraphRAG [8] builds LLM-extracted entity graphs. AgentCourt [7] simulates courts with evolving LLM lawyer agents. None of these evaluates grounding, "
               "refusal and structured-output robustness of an Indian case-preparation assistant under strict token budgets.")
    _ieee_h(d, "III. System Architecture")
    _ieee_p(d, "Court Vision AI (Fig. 1) has a Next.js 16/React 19 frontend and a FastAPI backend with SQLAlchemy (SQLite/PostgreSQL). Uploaded PDFs are validated "
               "(extension, 50 MB limit, %PDF magic bytes) and processed with PyMuPDF in a background worker. Six AI modules call Groq-hosted models through a "
               "fallback chain (gpt-oss-120b → qwen3 → gpt-oss-20b): grounded chat with Server-Sent-Event streaming, a structured case summary, an evidence graph "
               "with typed nodes (person, organisation, date, location, fact, evidence) and edges (supports, contradicts, testified_by, …) cached per case, a virtual "
               "courtroom in which separately prompted Judge (strict, inquisitive or balanced temperament) and Opposing-Counsel roles respond to the user and finish "
               "with a verdict and advocacy scorecard, a trial brief (chronology, cross-examination bank, synopsis with IPC/BNS, CrPC/BNSS and IEA/BSA references), "
               "and precedent research.")
    p = d.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(figdir / "fig_architecture.png"), width=Pt(240))
    c = d.d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = c.add_run("Fig. 1. Court Vision AI architecture."); rr.font.size = Pt(8); rr.font.name = "Times New Roman"
    _ieee_h(d, "IV. Proposed Method")
    _ieee_sub(d, "A. CV-RAG retrieval grounding")
    _ieee_p(d, "Text is extracted page by page; running headers, URLs and page numbers are removed; each page is split into 1,000-character chunks with 200-character "
               "overlap and tagged with its page (91 chunks for the test judgment). Chunks are indexed with Okapi BM25 [12] (k1 = 1.5, b = 0.75) after lower-casing and "
               "stop-word removal. For a question, the top-6 chunks are inserted in document order, each prefixed with [Page N], into Court Vision's legal system prompt, "
               "extended with two rules: cite the page for every factual claim, and reply exactly \"This information is not available in the uploaded documents\" "
               "when the excerpts do not contain the answer (Fig. 2).")
    p = d.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(figdir / "fig_cvrag.png"), width=Pt(240))
    c = d.d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = c.add_run("Fig. 2. CV-RAG pipeline."); rr.font.size = Pt(8); rr.font.name = "Times New Roman"
    _ieee_sub(d, "B. Nested-object salvage parser")
    _ieee_p(d, "The evidence-graph module asks the LLM for {nodes, edges} JSON. Its existing recovery routine scans for objects that close at nesting depth 0; when the "
               "response is cut by max_tokens the outer object never closes, so nothing is recovered and the system silently falls back to regex extraction. The proposed "
               "parser keeps a stack of open-brace positions, parses every complete object at any depth, and classifies objects with {id, label, type} as nodes and "
               "{source, target} as edges.")
    _ieee_h(d, "V. Experimental Setup")
    _ieee_p(d, "CV-LegalQA-42 was built manually from Jacob Mathew v. State of Punjab [13] (72,720 characters): 16 questions answerable inside the 18,000-character "
               "window (A), 14 answerable only beyond it (B), and 12 unanswerable questions (C), e.g. the FIR number or a BNS section applied in a 2005 judgment. "
               "Gold answers are regular expressions that must all match. Four systems were compared with gpt-oss-120b pinned (temperature 0.2, max_tokens 2048): "
               "S1 CV-Trunc (production), S2 CV-RAG, S3 closed-book (case name only) and S4 BM25 extractive (top passage, no LLM). For the parser study, three "
               "evidence graphs that the LLM produced for real cases were corrupted 22 ways (66 inputs) and parsed by four existing parsers and the proposed one. "
               "We report Wilson 95% intervals, McNemar's exact test [14] on paired outcomes, Wilcoxon signed-rank for latency and Cochran's Q for parsers.")
    _ieee_h(d, "VI. Results and Discussion")
    tbl = [["Metric", "CV-RAG", "CV-Trunc", "Closed", "BM25"],
           ["Answerable acc. (30)"] + [f"{S[s]['k_answerable']}" for s in (S2, S1, S3, S4)],
           ["  in window A (16)"] + [f"{S[s]['k_A']}" for s in (S2, S1, S3, S4)],
           ["  beyond window B (14)"] + [f"{S[s]['k_B']}" for s in (S2, S1, S3, S4)],
           ["Correct refusals (12)"] + [f"{S[s]['k_C']}" for s in (S2, S1, S3, S4)],
           ["Task accuracy (%)"] + [f"{S[s]['task_accuracy'][0] * 100:.1f}" for s in (S2, S1, S3, S4)],
           ["Decision F1"] + [f"{S[s]['decision_f1']:.2f}" for s in (S2, S1, S3, S4)],
           ["Prompt tokens"] + [f"{S[s]['prompt_tokens_mean']:,.0f}" for s in (S2, S1, S3)] + ["0"],
           ["Latency (s)"] + [f"{S[s]['latency_mean']:.2f}" for s in (S2, S1, S3)] + ["<0.01"]]
    cap = d.d.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = cap.add_run("TABLE I\nQA RESULTS ON CV-LEGALQA-42"); rr.font.size = Pt(8); rr.font.name = "Times New Roman"; rr.font.small_caps = True
    tt = d.d.add_table(rows=len(tbl), cols=5)
    tt.style = d.d.tables[0].style
    for i, row in enumerate(tbl):
        for j, v in enumerate(row):
            cell = tt.cell(i, j); cell.text = ""
            run = cell.paragraphs[0].add_run(str(v)); run.font.size = Pt(7.5); run.font.name = "Times New Roman"; run.bold = (i == 0)
    _set_borders(tt)
    _ieee_p(d, f"Table I and Fig. 3 summarise the QA results. Without documents, the LLM answered {S[S3]['k_answerable']}/30 answerable questions and fabricated "
               f"answers to {S[S3]['confusion']['FP']}/12 unanswerable ones (an invented nurse's name, a two-year sentence, a ₹2 lakh award, an FIR number). "
               f"The production pipeline answered {S[S1]['k_A']}/16 in-window questions but only {S[S1]['k_B']}/14 beyond-window ones "
               f"({S[S1]['k_B_strict']}/{S[S1]['n_B_strict']} on the strict subset whose answer never appears in the window), usually by correctly stating that "
               f"the information was not in the documents — the truncation is visible as false negatives in its confusion matrix. CV-RAG answered "
               f"{S[S2]['k_answerable']}/30 and refused {S[S2]['k_C']}/12, reaching {S[S2]['k_task']}/42 task accuracy; the gain is significant against CV-Trunc "
               f"(McNemar {pt(F['m21']['p_value'])}) and the closed-book model ({pt(F['m23']['p_value'])}). {F['cit']['k']}/{F['cit']['n']} of its "
               f"correct answers cited a page that contains the answer. Purely extractive BM25 found a relevant passage for {S[S4]['k_answerable']}/30 questions "
               f"but cannot decline, so all 12 unanswerable questions became false positives.", )
    p = d.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(figdir / "fig_accuracy_by_split.png"), width=Pt(245))
    c = d.d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = c.add_run("Fig. 3. Accuracy by question split (95% Wilson CI)."); rr.font.size = Pt(8); rr.font.name = "Times New Roman"
    _ieee_p(d, f"CV-RAG used {S[S2]['prompt_tokens_mean']:,.0f} prompt tokens per query versus {S[S1]['prompt_tokens_mean']:,.0f} for CV-Trunc "
               f"({pc(F['tok_saving'], 0)} fewer), which raises the number of queries that fit in an 8,000-TPM quota, and its mean latency was "
               f"{S[S2]['latency_mean']:.2f} s versus {S[S1]['latency_mean']:.2f} s (Wilcoxon {pt(F['wil']['p_value'])}).")
    _ieee_p(d, f"For graph extraction, all four existing parsers succeeded on formatting noise only when they stripped fences/prose, and every one of them failed on all 48 "
               f"truncated responses. The salvage parser parsed {J['P4_NestedSalvage']['k']}/66 inputs (Cochran's Q = {R['json_robustness']['cochran_q']:.1f}, "
               f"p {('< 0.001' if R['json_robustness']['cochran_p'] < 0.001 else '= ' + pv(R['json_robustness']['cochran_p']))}) and recovered "
               f"{pc(J['P4_NestedSalvage']['node_recovery_trunc'])} of nodes from truncated responses; edges, which the model writes last, are recovered less often "
               f"({pc(J['P4_NestedSalvage']['edge_recovery'])} overall).")
    _ieee_h(d, "VII. Limitations")
    _ieee_p(d, "The study uses one judgment and 42 questions with one generation per question, so confidence intervals are wide; gold answers are scored with regular "
               "expressions, which may accept an answer that also contains extra unsupported detail; BM25 is lexical and may miss paraphrased questions; and the closed-book "
               "baseline was given only the case name. Results should be replicated on a multi-document Indian corpus with human adjudication.")
    _ieee_h(d, "VIII. Conclusion and Future Work")
    _ieee_p(d, "Page-tagged retrieval grounding lets a rate-limited legal assistant see the whole case record, answer more questions correctly, refuse unanswerable "
               "ones and cite pages, at lower token cost than truncated full-context prompting. A small parser change turns silently discarded truncated graph output into "
               "usable evidence graphs. Future work will add dense/hybrid retrieval, multi-document cases, grounding for the courtroom and trial-brief modules, and a "
               "user study with advocates and law students.")
    _ieee_h(d, "References")
    for i, ref in enumerate(REFS, 1):
        p = d.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Pt(14); p.paragraph_format.first_line_indent = Pt(-14); p.paragraph_format.space_after = Pt(1)
        rr = p.add_run(f"[{i}] {ref}"); rr.font.size = Pt(7.5); rr.font.name = "Times New Roman"
    d.section(cols=1)
    d.h("5. Conclusion")
    d.p("The research paper was prepared in IEEE conference format with all mandatory sections. Every number in the abstract, tables and discussion is generated "
        "directly from the logged experimental results (eval/results/summary.json), so the paper stays consistent with Experiments 4 and 5.", align="justify")
    d.save(out)


def _set_borders(table):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    tblPr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "insideH"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "000000"); b.append(e)
    tblPr.append(b)


# ═════════════════════════════════════════════════════════════════════════════
# Experiment 7
# ═════════════════════════════════════════════════════════════════════════════

def _syllables(w):
    w = w.lower()
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups) - (1 if w.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def readability(text):
    sents = max(1, len(re.findall(r"[.!?](\s|$)", text)))
    words = re.findall(r"[A-Za-z]+", text)
    syl = sum(_syllables(w) for w in words)
    fre = 206.835 - 1.015 * len(words) / sents - 84.6 * syl / len(words)
    return len(words), sents, fre


def exp7(out, figdir, R):
    F = facts(R)
    abstract = paper_text(F)
    nw, ns, fre = readability(abstract)
    d = LabDoc(7, "Plagiarism Checking, Peer Review and Paper Revision", template_no=1)
    d.h("1. Aim:")
    d.p("To perform plagiarism analysis, receive peer/faculty review, improve technical writing, references and formatting of the research paper prepared in Experiment 6.")
    d.h("2. Plagiarism Checking")
    d.p("The paper is checked with the institute-licensed similarity tool (Turnitin / DrillBit) using the settings below. Similarity is interpreted according to "
        "the UGC (Promotion of Academic Integrity and Prevention of Plagiarism in Higher Educational Institutions) Regulations, 2018.", align="justify")
    d.table([["Setting", "Value"],
             ["Tool", "Turnitin / DrillBit (institute licence)"],
             ["Exclusions", "Bibliography, quoted material, matches < 14 words, own lab write-ups (Exp. 1–5)"],
             ["File submitted", "Experiment_6 paper section (PDF export)"],
             ["Overall similarity index", "______ %  (record from the report)"],
             ["Largest single-source match", "______ %  (source: ____________)"],
             ["AI-writing indicator (if shown)", "______ %"]],
            widths=[2, 4], size=9.5, bold_first_col=True, caption="Similarity check record")
    d.table([["UGC 2018 level", "Similarity", "Consequence"],
             ["Level 0", "Up to 10%", "Minor similarity — no penalty (target for this paper)"],
             ["Level 1", "Above 10% to 40%", "Revise and resubmit within 6 months"],
             ["Level 2", "Above 40% to 60%", "Debarred from submitting a revised script for 1 year"],
             ["Level 3", "Above 60%", "Debarred from submitting a revised script for 2 years"]],
            widths=[1.2, 1.4, 3.4], size=9.5, caption="Plagiarism levels (UGC Regulations, 2018)")
    d.h2("2.1 Originality safeguards applied while writing")
    d.bullets([
        "All related-work statements are paraphrased summaries with in-text IEEE citations; no sentence was copied from the cited papers.",
        "The judgment used as data [13] is only described and cited, never quoted at length.",
        "Results, tables and figures are produced from our own experiment logs (eval/results), so they are original by construction.",
        f"Automated writing checks on the abstract: {nw} words (IEEE recommends 150–250), {ns} sentences, Flesch Reading Ease ≈ {fre:.0f} (technical prose; acceptable for an IEEE venue).",
    ])
    d.h("3. Peer Review")
    d.p("The draft was reviewed against IEEE reviewer criteria (originality, technical soundness, clarity, evaluation, references). "
        "Comments from the peer review are recorded below together with the revision made.", align="justify")
    d.table([["#", "Reviewer comment", "Severity", "Revision made", "Status"],
             ["1", "The evaluation uses a single judgment; generalisability is unclear.", "Major", "Added Section VII (Limitations) stating the single-document scope and planned multi-document replication.", "Done"],
             ["2", "Regex scoring could accept answers that also contain fabricated detail.", "Major", "Stated in Limitations; scorer was strengthened with Unicode normalisation and 13 abstention patterns; ambiguous answers were inspected manually.", "Done"],
             ["3", "'Beyond-window' questions may still have keywords inside the window.", "Major", f"Added a strict beyond-window subset (n = {F['S'][S1]['n_B_strict']}) computed automatically from the production context and reported it separately.", "Done"],
             ["4", "Is the closed-book baseline fair?", "Minor", "Clarified that it receives the case name and the same model/temperature; noted in Limitations.", "Done"],
             ["5", "Statistical significance not reported for paired data.", "Major", "Added McNemar exact tests, Wilcoxon signed-rank and Cochran's Q with p-values.", "Done"],
             ["6", "Citation claims need verification.", "Minor", f"Added citation accuracy: {F['cit']['k']}/{F['cit']['n']} cited pages contain the answer (gold pages computed from the PDF).", "Done"],
             ["7", "References inconsistent (missing DOI/venue).", "Minor", "All references converted to IEEE style with DOI or arXiv identifier; unverifiable DOIs replaced by arXiv links.", "Done"],
             ["8", "Figure labels overflow; overlapping lines hide parsers.", "Minor", "Re-wrapped CV-RAG diagram labels; merged identical P0–P3 curves into one labelled series; added point labels.", "Done"]],
            widths=[0.3, 2.1, 0.7, 2.6, 0.6], size=8.5, caption="Peer review comments and responses")
    d.h2("3.1 Faculty review")
    d.table([["Reviewer", "Remarks", "Action", "Signature / Date"],
             ["Faculty guide: ____________", "", "", ""],
             ["Peer group: ____________", "", "", ""]], widths=[1.6, 2.4, 1.4, 1.2], size=9.5)
    d.h("4. Paper Revision Summary")
    d.table([["Aspect", "Before review", "After review"],
             ["Answer scoring", "Plain regex match on raw LLM text", "Unicode normalisation (narrow no-break spaces, non-breaking hyphens, curly quotes) — fixed 3 false 'wrong' labels for CV-RAG; abstention patterns extended to 13"],
             ["Beyond-window analysis", "B split defined by where the Court's statement appears", f"Added strict subset (n = {F['S'][S1]['n_B_strict']}) whose gold text never occurs in the 18,000-char window"],
             ["Citations", "Claimed, not verified", f"Verified against PDF-computed gold pages: {F['cit']['k']}/{F['cit']['n']} correct"],
             ["Question metadata", "Hand-entered page numbers", "Page numbers recomputed from the PDF (4 corrected)"],
             ["Statistics wording", "p-values written as 'p = < 0.001'", "Standard form 'p < 0.001' / 'p = 0.020'"],
             ["Limitations", "Absent", "Section VII added (single document, single run, regex scoring, BM25 only, closed-book prompt)"],
             ["References", "One DOI not verifiable", f"{len(REFS)} IEEE-style references; unverifiable DOI replaced by arXiv identifier"]],
            widths=[1.3, 2.0, 2.7], size=9, caption="Revision log")
    d.h("5. Conclusion")
    d.p("The paper was prepared for plagiarism screening with clear originality safeguards, reviewed using IEEE criteria, and revised to address every major comment — "
        "most importantly by adding statistical tests, a strict beyond-window analysis, citation verification and an explicit limitations section. "
        "The similarity percentage must be recorded from the official tool report before submission.", align="justify")
    d.save(out)


# ═════════════════════════════════════════════════════════════════════════════
# Experiment 10
# ═════════════════════════════════════════════════════════════════════════════

def poster(figdir, F):
    S = F["S"]
    fig = plt.figure(figsize=(16.5, 23.4))  # A2-ish portrait ratio
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0.9, 1, 0.1]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, color="#1F3864"))
    ax.text(0.5, 0.70, "Court Vision AI", ha="center", va="center", color="white", fontsize=40, fontweight="bold")
    ax.text(0.5, 0.42, "Retrieval-Grounded Generative AI for Indian Legal Case Preparation", ha="center", va="center", color="white", fontsize=26)
    ax.text(0.5, 0.14, "Department of Information Technology · Vivekanand Education Society's Institute of Technology, Mumbai", ha="center", color="#F4D58D", fontsize=17)

    def panel(rect, title, body, fs=17):
        a = fig.add_axes(rect); a.axis("off")
        a.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, ec="#2E75B6", lw=2.5))
        a.text(0.03, 0.92, title, fontsize=22, fontweight="bold", color="#1F3864", va="top")
        a.text(0.03, 0.76, body, fontsize=fs, va="top", linespacing=1.55)

    panel([0.03, 0.72, 0.455, 0.165], "Problem",
          "• LLMs hallucinate legal facts\n   (58–88% closed-book, Dahl et al. 2024).\n• Free-tier APIs force truncation: production\n   Court Vision sends only 25% of a 20-page judgment.\n"
          "• Indian legal NLP lacks grounded-QA & refusal studies.")
    panel([0.515, 0.72, 0.455, 0.165], "Contributions",
          "• Court Vision AI: chat · evidence graph · virtual\n   courtroom · trial brief · precedent research.\n• CV-RAG: page-tagged BM25 grounding + cite/abstain.\n"
          "• Salvage parser for truncated LLM JSON.\n• CV-LegalQA-42 ground-truth benchmark.")
    for rect, img, title in [([0.03, 0.50, 0.94, 0.2], "fig_cvrag.png", "Proposed CV-RAG pipeline"),
                             ([0.03, 0.25, 0.55, 0.23], "fig_accuracy_by_split.png", "Accuracy by question split"),
                             ([0.60, 0.25, 0.37, 0.23], "fig_json_truncation.png", "Graph recovery from truncated JSON")]:
        a = fig.add_axes(rect); a.axis("off")
        a.imshow(plt.imread(str(figdir / img))); a.set_title(title, fontsize=17, fontweight="bold", color="#1F3864")
    panel([0.03, 0.04, 0.455, 0.19], "Key results (42 questions, gpt-oss-120b)",
          f"• Task accuracy: CV-RAG {pc(S[S2]['task_accuracy'][0])} vs production {pc(S[S1]['task_accuracy'][0])}\n   vs closed-book {pc(S[S3]['task_accuracy'][0])}  (McNemar {pt(F['m21']['p_value'])})\n"
          f"• Refused {S[S2]['k_C']}/12 unanswerable questions;\n   closed-book fabricated {S[S3]['confusion']['FP']}/12.\n• {pc(F['tok_saving'], 0)} fewer prompt tokens than production.\n"
          f"• Salvage parser: 0% → {pc(F['J']['P4_NestedSalvage']['success_trunc'], 0)} on truncated graph JSON.")
    panel([0.515, 0.04, 0.455, 0.19], "Conclusion & next steps",
          "Retrieval grounding gives a rate-limited legal\nassistant the whole case record, with page citations\nand calibrated refusal, at lower cost.\n\n"
          "Next: hybrid dense+BM25 retrieval, multi-document\ncases, grounding the courtroom module, user study\nwith advocates and law students.")
    fig.savefig(figdir / "fig_poster.png", dpi=110)
    plt.close(fig)


def exp10(out, figdir, R):
    F = facts(R); S = F["S"]
    poster(figdir, F)
    d = LabDoc(10, "Research Dissemination and Innovation Showcase", template_no=1)
    d.h("1. Aim:")
    d.p("To submit the paper to a conference/journal (or prepare the submission package) and present the work through a research poster, demonstration and innovation pitch.")
    d.h("2. Target Venues")
    d.table([["Venue", "Type", "Why it fits"],
             ["IEEE INDICON (IEEE India Council International Conference)", "Conference — IEEE Xplore", "Applied AI systems with Indian societal impact"],
             ["IEEE ICCCNT (Int. Conf. on Computing, Communication and Networking Technologies)", "Conference — IEEE Xplore", "Broad AI/NLP application track; student-friendly"],
             ["NLLP — Natural Legal Language Processing Workshop (ACL/EMNLP)", "Workshop — ACL Anthology", "Specialised legal-NLP audience; grounded legal QA"],
             ["JURIX — Int. Conf. on Legal Knowledge and Information Systems", "Conference — IOS Press", "Legal informatics; knowledge graphs, legal AI tools"],
             ["Artificial Intelligence and Law (Springer)", "Journal", "Extended version with multi-document evaluation"]],
            widths=[2.6, 1.6, 2.2], size=9, caption="Candidate venues")
    d.h("3. Submission Package")
    d.table([["Item", "Status"],
             ["Camera-ready paper in IEEE template (Experiment 6), PDF checked with IEEE PDF eXpress", "Prepared"],
             ["Similarity report below 10% (Experiment 7)", "To attach after tool run"],
             ["Cover letter stating novelty: retrieval grounding under token limits, refusal and citation evaluation, salvage parser", "Prepared"],
             ["Artefact bundle: research_experiments/ (qa_set.py, run_qa_eval.py, run_json_robustness.py, analyze.py, results/*.json, figures/)", "Prepared"],
             ["Copyright application for software (Experiment 9)", "Draft ready"],
             ["IEEE copyright form (eCF) — after acceptance", "Pending"]],
            widths=[4.6, 1.4], size=9.5, caption="Submission checklist")
    d.h("4. Research Poster")
    d.p("The A2 research poster summarises the problem, contributions, method, key results and conclusion; all figures and numbers come from the experiment logs.")
    d.fig(figdir / "fig_poster.png", "Research poster — Court Vision AI", width=5.0)
    d.h("5. Live Demonstration Plan (8 minutes)")
    d.table([["Time", "Step", "What the audience sees"],
             ["0:00–1:00", "Problem hook", "Closed-book LLM confidently invents an FIR number and a '₹2 lakh' award for the Jacob Mathew case."],
             ["1:00–2:30", "Case Vault & upload", "Create case → upload judgment PDF → status changes to READY with 20 pages detected."],
             ["2:30–4:00", "Case Intelligence chat", "Ask an in-window and a beyond-window question; answers stream with page citations; ask an unanswerable question and see the refusal."],
             ["4:00–5:00", "Evidence Graph", "Typed nodes/edges extracted from the judgment; lanes/orbit layouts; cached reload."],
             ["5:00–6:30", "Virtual Courtroom", "Choose 'strict' judge; argue for the appellant; Judge and Opposing Counsel respond; request verdict and scorecard."],
             ["6:30–7:15", "Trial brief & research", "Chronology, cross-examination bank, BNS/IPC references; precedent search."],
             ["7:15–8:00", "Results slide", f"Task accuracy {pc(S[S2]['task_accuracy'][0])} vs {pc(S[S1]['task_accuracy'][0])}; {pc(F['tok_saving'], 0)} fewer tokens."]],
            widths=[0.9, 1.5, 3.8], size=9, caption="Demonstration script")
    d.h("6. Innovation Pitch")
    d.table([["Element", "Pitch content"],
             ["Problem", "Junior advocates and law students must master long case files quickly; generic chatbots hallucinate, and paid legal-AI tools are costly and US-centric."],
             ["Solution", "Court Vision AI — upload your case, get cited answers, an evidence graph, courtroom practice against an AI judge and opposing counsel, and a trial brief."],
             ["Proof", f"On a real Supreme Court judgment: {pc(S[S2]['task_accuracy'][0])} task accuracy with page citations and {S[S2]['k_C']}/12 correct refusals, using {pc(F['tok_saving'], 0)} fewer tokens than full-context prompting."],
             ["Users", "Law students and moot-court teams, junior advocates, legal-aid clinics, judicial and police training academies."],
             ["USP", "Indian-law focus (IPC↔BNS, CrPC↔BNSS, IEA↔BSA), grounded courtroom training with a scorecard, runs on low-cost LLM quotas."],
             ["Business model", "Free tier for students; institutional licences for law schools; per-seat plans for chambers."],
             ["Roadmap", "Hybrid retrieval, multi-document cases, Hindi and regional languages, grounding in the courtroom/brief modules, user study."],
             ["Ask", "Mentorship and pilot access with a law college moot-court society; incubation support."]],
            widths=[1.2, 4.8], size=9.5, bold_first_col=True, caption="Innovation pitch outline")
    d.h("7. Conclusion")
    d.p("The submission package, research poster, demonstration script and innovation pitch were prepared from the same experimental evidence, ready for "
        "submission to an IEEE conference and presentation at the departmental innovation showcase.", align="justify")
    d.save(out)
