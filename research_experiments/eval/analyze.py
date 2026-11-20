"""
Experiment 5 — Statistical analysis & visualisation of Experiment 4 results.

Inputs : results/qa_results.jsonl, results/json_robustness.json,
         results/adjudication.json (optional manual overrides: {"SYSTEM|QID": "correct"|"abstain"|"wrong"})
Outputs: results/summary.json, ../figures/*.png
"""
import json
import math
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from qa_set import QA, ABSTAIN_PATTERNS  # noqa: E402

RES = HERE / "results"
FIG = HERE.parent / "figures"
FIG.mkdir(exist_ok=True)
SYSTEMS = ["S1_CV_Trunc", "S2_CV_RAG", "S3_ClosedBook", "S4_BM25_Extract"]
LABEL = {"S1_CV_Trunc": "CV-Trunc\n(production)", "S2_CV_RAG": "CV-RAG\n(proposed)",
         "S3_ClosedBook": "Closed-book\nLLM", "S4_BM25_Extract": "BM25\nextractive"}
SHORT = {"S1_CV_Trunc": "CV-Trunc (production)", "S2_CV_RAG": "CV-RAG (proposed)",
         "S3_ClosedBook": "Closed-book LLM", "S4_BM25_Extract": "BM25 extractive"}
COLORS = {"S1_CV_Trunc": "#2E75B6", "S2_CV_RAG": "#2E8B7A", "S3_ClosedBook": "#B8860B", "S4_BM25_Extract": "#7F7F7F"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

QMAP = {q["id"]: q for q in QA}
ABST = [re.compile(p, re.I) for p in ABSTAIN_PATTERNS]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


def auto_label(system, q, ans):
    """correct | abstain | wrong (answerable)  /  abstain | hallucinated (unanswerable)."""
    # Normalise typography the LLM emits (U+202F/U+00A0 spaces, U+2011 hyphens, curly quotes)
    text = (ans or "").translate({0x00A0: " ", 0x202F: " ", 0x2009: " ", 0x2007: " ", 0x2011: "-",
                                  0x2010: "-", 0x2019: "'", 0x2018: "'"})
    text = text.replace("**", "").replace("*", "")  # markdown emphasis splits phrases like "is **not provided**"
    abstained = any(p.search(text) for p in ABST)
    if q["gold"]:
        hit = all(re.search(g, text, re.I) for g in q["gold"])
        if hit:
            return "correct"
        return "abstain" if abstained else "wrong"
    if system == "S4_BM25_Extract":
        return "hallucinated"  # extractive baseline never declines
    return "abstain" if abstained else "hallucinated"


_NORM = {0x00A0: " ", 0x202F: " ", 0x2009: " ", 0x2007: " ", 0x2011: "-", 0x2010: "-", 0x2019: "'", 0x2018: "'"}


def gold_pages():
    """Pages of the judgment on which every gold pattern of a question matches."""
    import fitz
    pdf = HERE.parents[1] / "backend/storage/documents/7205352d-9ee1-45c8-8ce5-ba96a597f9d7/fb8c9db7-b262-42b7-8e59-dfe0a8754491.pdf"
    doc = fitz.open(pdf)
    pages = [re.sub(r"\s+", " ", p.get_text()) for p in doc]
    out = {}
    for q in QA:
        if not q["gold"]:
            continue
        hit = [i + 1 for i, t in enumerate(pages) if all(re.search(g, t, re.I) for g in q["gold"])]
        if not hit:  # answer spans a page break: accept either side of the best-matching pair
            hit = [i + 1 for i in range(len(pages) - 1)
                   if all(re.search(g, pages[i] + " " + pages[i + 1], re.I) for g in q["gold"])]
            hit = sorted({p for h in hit for p in (h, h + 1)})
        out[q["id"]] = hit
    return out


def citation_accuracy(latest, system="S2_CV_RAG"):
    gp = gold_pages()
    n = ok = 0
    detail = {}
    for q in QA:
        r = latest.get((system, q["id"]))
        if not q["gold"] or not r or r["label"] != "correct":
            continue
        cited = {int(x) for x in re.findall(r"p\.\s*(\d{1,2})", (r["answer"] or "").translate(_NORM))}
        n += 1
        good = bool(cited & set(gp[q["id"]]))
        ok += good
        detail[q["id"]] = dict(cited=sorted(cited), gold=gp[q["id"]], ok=good)
    return dict(k=ok, n=n, rate=wilson(ok, n), detail=detail)


def load():
    rows = [json.loads(l) for l in (RES / "qa_results.jsonl").read_text(encoding="utf-8").splitlines()]
    latest = {}
    for r in rows:
        if r.get("answer") or r["system"] == "S4_BM25_Extract":
            latest[(r["system"], r["qid"])] = r
    adj_path = RES / "adjudication.json"
    adj = json.loads(adj_path.read_text()) if adj_path.exists() else {}
    for (s, qid), r in latest.items():
        lab = auto_label(s, QMAP[qid], r.get("answer"))
        r["auto_label"] = lab
        r["label"] = adj.get(f"{s}|{qid}", lab)
        r["split"] = qid[0]
    return latest


def analyse(latest):
    out = {"systems": {}, "n_questions": len(QA)}
    per_task_correct = {}
    for s in SYSTEMS:
        rs = [latest[(s, q["id"])] for q in QA if (s, q["id"]) in latest]
        if len(rs) < len(QA):
            print(f"WARNING {s}: only {len(rs)}/{len(QA)} results")
        A = [r for r in rs if r["split"] == "A"]
        B = [r for r in rs if r["split"] == "B"]
        C = [r for r in rs if r["split"] == "C"]
        ans = A + B
        k_ans = sum(r["label"] == "correct" for r in ans)
        # Decision task: should the system answer?  positive = "answered"
        tp = sum(r["label"] != "abstain" for r in ans)          # answered an answerable q
        fn = sum(r["label"] == "abstain" for r in ans)          # declined an answerable q
        fp = sum(r["label"] == "hallucinated" for r in C)       # answered an unanswerable q
        tn = sum(r["label"] == "abstain" for r in C)            # correctly declined
        prec = tp / (tp + fp) if tp + fp else 0
        rec = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        task_ok = [(r["label"] == "correct") if r["split"] != "C" else (r["label"] == "abstain") for r in rs]
        per_task_correct[s] = {r["qid"]: ok for r, ok in zip(rs, task_ok)}
        wrong_answers = sum(r["label"] == "wrong" for r in ans)
        lat = [r["latency_s"] for r in rs if r.get("latency_s") is not None]
        pt = [r["prompt_tokens"] for r in rs if r.get("prompt_tokens")]
        ct = [r["completion_tokens"] for r in rs if r.get("completion_tokens")]
        out["systems"][s] = dict(
            n=len(rs),
            acc_answerable=wilson(k_ans, len(ans)), k_answerable=k_ans, n_answerable=len(ans),
            acc_A=wilson(sum(r["label"] == "correct" for r in A), len(A)), k_A=sum(r["label"] == "correct" for r in A), n_A=len(A),
            acc_B=wilson(sum(r["label"] == "correct" for r in B), len(B)), k_B=sum(r["label"] == "correct" for r in B), n_B=len(B),
            refusal_C=wilson(tn, len(C)), k_C=tn, n_C=len(C),
            hallucination_C=fp / len(C) if C else 0,
            wrong_answers=wrong_answers,
            false_abstain=fn,
            task_accuracy=wilson(sum(task_ok), len(task_ok)), k_task=sum(task_ok),
            confusion=dict(TP=tp, FN=fn, FP=fp, TN=tn),
            decision_precision=prec, decision_recall=rec, decision_f1=f1,
            error_rate=1 - sum(task_ok) / len(task_ok),
            latency_mean=st.mean(lat) if lat else None, latency_sd=st.stdev(lat) if len(lat) > 1 else 0,
            latency_median=st.median(lat) if lat else None,
            latency_p95=float(np.percentile(lat, 95)) if lat else None,
            latencies=lat,
            prompt_tokens_mean=st.mean(pt) if pt else 0, completion_tokens_mean=st.mean(ct) if ct else 0,
            context_chars_mean=st.mean([r.get("context_chars", 0) for r in rs]),
        )
    # McNemar (exact binomial) on per-question task correctness
    def mcnemar(a, b):
        qa = per_task_correct[a]; qb = per_task_correct[b]
        common = [q for q in qa if q in qb]
        b01 = sum(qa[q] and not qb[q] for q in common)
        b10 = sum(qb[q] and not qa[q] for q in common)
        n = b01 + b10
        p = stats.binomtest(min(b01, b10), n, 0.5).pvalue if n else 1.0
        return dict(a=a, b=b, a_only=b01, b_only=b10, p_value=p, n=len(common))
    out["mcnemar"] = [mcnemar("S2_CV_RAG", "S1_CV_Trunc"), mcnemar("S2_CV_RAG", "S3_ClosedBook"),
                      mcnemar("S1_CV_Trunc", "S3_ClosedBook"), mcnemar("S2_CV_RAG", "S4_BM25_Extract")]
    # Latency: Wilcoxon signed-rank S2 vs S1 (paired by question)
    l1 = [latest[("S1_CV_Trunc", q["id"])]["latency_s"] for q in QA if ("S1_CV_Trunc", q["id"]) in latest and ("S2_CV_RAG", q["id"]) in latest]
    l2 = [latest[("S2_CV_RAG", q["id"])]["latency_s"] for q in QA if ("S1_CV_Trunc", q["id"]) in latest and ("S2_CV_RAG", q["id"]) in latest]
    if len(l1) > 5:
        w = stats.wilcoxon(l2, l1)
        out["latency_wilcoxon_S2_vs_S1"] = dict(statistic=float(w.statistic), p_value=float(w.pvalue), n=len(l1))
    # Strict beyond-window subset: B questions whose gold patterns cannot be matched in the
    # 18,000-char production context at all.
    import fitz
    pdf = HERE.parents[1] / "backend/storage/documents/7205352d-9ee1-45c8-8ce5-ba96a597f9d7/fb8c9db7-b262-42b7-8e59-dfe0a8754491.pdf"
    window = re.sub(r"\s+", " ", "\n".join(p.get_text() for p in fitz.open(pdf))[:18000])
    strict = [q["id"] for q in QA if q["id"].startswith("B") and not all(re.search(g, window, re.I) for g in q["gold"])]
    out["B_strict_ids"] = strict
    for s in SYSTEMS:
        k = sum(latest[(s, q)]["label"] == "correct" for q in strict if (s, q) in latest)
        out["systems"][s]["acc_B_strict"] = wilson(k, len(strict))
        out["systems"][s]["k_B_strict"] = k
        out["systems"][s]["n_B_strict"] = len(strict)
    out["citation_S2"] = citation_accuracy(latest)
    out["gold_pages"] = gold_pages()
    # per-question table
    out["per_question"] = [
        dict(qid=q["id"], q=q["q"], page=q.get("page"),
             **{s: latest[(s, q["id"])]["label"] for s in SYSTEMS if (s, q["id"]) in latest})
        for q in QA]
    return out


def json_robustness():
    rows = json.loads((RES / "json_robustness.json").read_text())
    parsers = ["P0_Naive", "P1_FenceStrip", "P2_SafeJSON", "P3_Robust", "P4_NestedSalvage"]
    summ = {}
    for p in parsers:
        sub = [r for r in rows if r["parser"] == p]
        k = sum(r["parsed"] for r in sub)
        summ[p] = dict(success=wilson(k, len(sub)), k=k, n=len(sub),
                       node_recovery=st.mean(r["node_recovery"] for r in sub),
                       edge_recovery=st.mean(r["edge_recovery"] for r in sub),
                       ms_mean=st.mean(r["ms"] for r in sub))
        fmt = [r for r in sub if not r["variant"].split("_")[0].endswith("trunc") and "trunc" not in r["variant"]]
        tr = [r for r in sub if "trunc" in r["variant"]]
        summ[p]["success_format"] = sum(r["parsed"] for r in fmt) / len(fmt)
        summ[p]["success_trunc"] = sum(r["parsed"] for r in tr) / len(tr)
        summ[p]["node_recovery_trunc"] = st.mean(r["node_recovery"] for r in tr)
    # Cochran's Q across parsers on identical inputs
    keys = sorted({(r["graph"], r["variant"]) for r in rows})
    mat = np.array([[next(r["parsed"] for r in rows if (r["graph"], r["variant"]) == k and r["parser"] == p) for p in parsers] for k in keys], dtype=int)
    k_ = mat.shape[1]; col = mat.sum(0); row = mat.sum(1); N = mat.sum()
    q_stat = (k_ - 1) * (k_ * (col ** 2).sum() - N ** 2) / (k_ * N - (row ** 2).sum())
    p_q = 1 - stats.chi2.cdf(q_stat, k_ - 1)
    b = sum(1 for i in range(len(keys)) if mat[i, 4] and not mat[i, 3]); c = sum(1 for i in range(len(keys)) if mat[i, 3] and not mat[i, 4])
    p_mc = stats.binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1.0
    return dict(parsers=summ, cochran_q=float(q_stat), cochran_p=float(p_q),
                mcnemar_P4_vs_P3=dict(p4_only=b, p3_only=c, p_value=float(p_mc)), n_inputs=len(keys), rows=rows)


# ── Figures ───────────────────────────────────────────────────────────────────

def figures(s, j):
    S = s["systems"]
    # 1. Accuracy by split with Wilson CI
    fig, ax = plt.subplots(figsize=(9, 4.6))
    groups = [("acc_A", "Answerable\n(inside 18k window)"), ("acc_B", "Answerable\n(beyond 18k window)"),
              ("refusal_C", "Unanswerable\n(correct refusal)"), ("task_accuracy", "Overall task\naccuracy (42 Qs)")]
    x = np.arange(len(groups)); wd = 0.2
    for i, sy in enumerate(SYSTEMS):
        vals = [S[sy][g][0] * 100 for g, _ in groups]
        lo = [(S[sy][g][0] - S[sy][g][1]) * 100 for g, _ in groups]
        hi = [(S[sy][g][2] - S[sy][g][0]) * 100 for g, _ in groups]
        bars = ax.bar(x + (i - 1.5) * wd, vals, wd, color=COLORS[sy], label=SHORT[sy], yerr=[lo, hi], capsize=2.5, ecolor="#444")
        for b_, v in zip(bars, vals):
            ax.text(b_.get_x() + b_.get_width() / 2, 1.5, f"{v:.0f}", ha="center", va="bottom", fontsize=7, color="white", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([g[1] for g in groups]); ax.set_ylabel("Percentage (%)"); ax.set_ylim(0, 108)
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.12), frameon=False)
    ax.set_title("Accuracy vs. method (error bars: 95% Wilson CI)", fontsize=10, pad=24)
    fig.tight_layout(); fig.savefig(FIG / "fig_accuracy_by_split.png", dpi=200); plt.close(fig)

    # 2. Confusion matrices (answer/abstain decision)
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.3))
    for ax, sy in zip(axes, SYSTEMS):
        c = S[sy]["confusion"]
        m = np.array([[c["TP"], c["FN"]], [c["FP"], c["TN"]]])
        ax.imshow(m, cmap="Blues", vmin=0, vmax=30)
        for (r, cc), v in np.ndenumerate(m):
            ax.text(cc, r, f"{['TP','FN','FP','TN'][r*2+cc]}\n{v}", ha="center", va="center",
                    color="white" if v > 15 else "#1a1a1a", fontsize=10, fontweight="bold")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["Answered", "Abstained"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["Answerable\n(n=30)", "Unanswerable\n(n=12)"], fontsize=8)
        ax.set_title(SHORT[sy], fontsize=9)
        ax.set_xlabel("Predicted", fontsize=8)
    axes[0].set_ylabel("Actual", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_confusion_matrices.png", dpi=200); plt.close(fig)

    # 3. Latency box plot (LLM systems)
    llm = ["S1_CV_Trunc", "S2_CV_RAG", "S3_ClosedBook"]
    fig, ax = plt.subplots(figsize=(7, 4))
    bp = ax.boxplot([S[sy]["latencies"] for sy in llm], patch_artist=True, widths=0.5, showmeans=True)
    for patch, sy in zip(bp["boxes"], llm):
        patch.set_facecolor(COLORS[sy]); patch.set_alpha(0.75)
    ax.set_xticks(range(1, 4)); ax.set_xticklabels([LABEL[sy] for sy in llm])
    ax.set_ylabel("End-to-end LLM latency (s)"); ax.set_title("Execution time vs. method (n = 42 queries each)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_latency.png", dpi=200); plt.close(fig)

    # 4. Prompt tokens / context size
    fig, ax = plt.subplots(figsize=(7, 4))
    vals = [S[sy]["prompt_tokens_mean"] for sy in llm]
    bars = ax.bar([LABEL[sy] for sy in llm], vals, color=[COLORS[sy] for sy in llm])
    for b_, v in zip(bars, vals):
        ax.text(b_.get_x() + b_.get_width() / 2, v + 60, f"{v:,.0f}", ha="center", fontsize=9)
    ax.set_ylabel("Mean prompt tokens per query"); ax.set_title("Context cost vs. method", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_prompt_tokens.png", dpi=200); plt.close(fig)

    # 5. Error decomposition stacked bar
    fig, ax = plt.subplots(figsize=(8, 4.2))
    cats = [("Correct answer", lambda d: d["k_answerable"], "#2E8B7A"), ("Wrong answer", lambda d: d["wrong_answers"], "#C0392B"),
            ("Wrongly abstained", lambda d: d["false_abstain"], "#F0B27A"), ("Correctly refused", lambda d: d["confusion"]["TN"], "#5DADE2"),
            ("Hallucinated on unanswerable", lambda d: d["confusion"]["FP"], "#7B241C")]
    bottom = np.zeros(len(SYSTEMS))
    for name, fn, col in cats:
        v = np.array([fn(S[sy]) for sy in SYSTEMS], dtype=float)
        ax.bar([LABEL[sy] for sy in SYSTEMS], v, bottom=bottom, color=col, label=name)
        for i, vv in enumerate(v):
            if vv >= 2:
                ax.text(i, bottom[i] + vv / 2, int(vv), ha="center", va="center", fontsize=8, color="white")
        bottom += v
    ax.set_ylabel("Number of questions (of 42)"); ax.legend(fontsize=7.5, bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.set_title("Outcome decomposition per method", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_outcomes.png", dpi=200); plt.close(fig)

    # 6. JSON robustness: node recovery vs truncation point
    rows = j["rows"]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    pts = [30, 40, 50, 60, 70, 80, 90, 95]
    pcol = {"P0_Naive": "#7F7F7F", "P1_FenceStrip": "#B8860B", "P2_SafeJSON": "#2E75B6", "P3_Robust": "#8E44AD", "P4_NestedSalvage": "#2E8B7A"}

    def curve(p):
        return [st.mean(r["node_recovery"] for r in rows if r["parser"] == p and r["variant"] in (f"trunc_{t}", f"fence+trunc_{t}")) * 100 for t in pts]
    existing = [curve(p) for p in ("P0_Naive", "P1_FenceStrip", "P2_SafeJSON", "P3_Robust")]
    same = all(c == existing[0] for c in existing)
    if same:
        ax.plot(pts, existing[0], marker="s", color="#8E44AD", lw=1.6, label="P0–P3 existing parsers (identical)")
    else:
        for p in ("P0_Naive", "P1_FenceStrip", "P2_SafeJSON", "P3_Robust"):
            ax.plot(pts, curve(p), marker="o", color=pcol[p], label=p.replace("_", " "), lw=1.4)
    y4 = curve("P4_NestedSalvage")
    ax.plot(pts, y4, marker="o", color=pcol["P4_NestedSalvage"], lw=2.2, label="P4 nested salvage (proposed)")
    for xx, yy in zip(pts, y4):
        ax.annotate(f"{yy:.0f}", (xx, yy), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8, color="#2E8B7A")
    ax.set_xlabel("Point at which the LLM response was truncated (% of full JSON)")
    ax.set_ylabel("Graph nodes recovered (%)"); ax.set_ylim(-5, 105)
    ax.set_title("Evidence-graph recovery from truncated LLM output", fontsize=10); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_json_truncation.png", dpi=200); plt.close(fig)

    # 7. JSON parse success by parser (format vs truncation)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ps = list(pcol)
    a = [j["parsers"][p]["success_format"] * 100 for p in ps]; b_ = [j["parsers"][p]["success_trunc"] * 100 for p in ps]
    xx = np.arange(len(ps))
    ax.bar(xx - 0.18, a, 0.36, label="Formatting noise (6 variants)", color="#2E75B6")
    ax.bar(xx + 0.18, b_, 0.36, label="Truncated output (16 variants)", color="#2E8B7A")
    ax.set_xticks(xx); ax.set_xticklabels([p.replace("_", "\n") for p in ps], fontsize=8)
    ax.set_ylabel("Parse success (%)"); ax.set_ylim(0, 110); ax.legend(fontsize=8)
    ax.set_title("JSON parse success vs. parser", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_json_success.png", dpi=200); plt.close(fig)


def main():
    latest = load()
    s = analyse(latest)
    j = json_robustness()
    figures(s, j)
    j_out = {k: v for k, v in j.items() if k != "rows"}
    for sy in s["systems"].values():
        sy.pop("latencies", None)
    s["json_robustness"] = j_out
    (RES / "summary.json").write_text(json.dumps(s, indent=1))
    for sy, d in s["systems"].items():
        print(f"{sy:16s} n={d['n']:2d} ansAcc={d['acc_answerable'][0]:.3f} A={d['k_A']}/{d['n_A']} B={d['k_B']}/{d['n_B']} "
              f"refuse={d['k_C']}/{d['n_C']} task={d['k_task']}/42 F1={d['decision_f1']:.3f} "
              f"lat={d['latency_mean'] or 0:.2f}s tok={d['prompt_tokens_mean']:.0f} conf={d['confusion']}")
    for m in s["mcnemar"]:
        print("McNemar", m)
    print("Wilcoxon", s.get("latency_wilcoxon_S2_vs_S1"))
    print("Cochran Q", j_out["cochran_q"], j_out["cochran_p"], j_out["mcnemar_P4_vs_P3"])


if __name__ == "__main__":
    main()
