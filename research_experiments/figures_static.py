"""Static diagrams for the experiment write-ups (workflow, architecture, CV-RAG pipeline)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

NAVY, BLUE, TEAL, GOLD, GREY, RED = "#1F3864", "#2E75B6", "#2E8B7A", "#B8860B", "#595959", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def box(ax, x, y, w, h, text, color, fc=None, fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                linewidth=1.4, edgecolor=color, facecolor=fc or "white"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#1a1a1a",
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, color=GREY, style="-|>", ls="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=1.3, linestyle=ls, shrinkA=2, shrinkB=2))


def workflow():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.2); ax.axis("off")
    steps = [
        ("1. Problem definition\nAI legal assistants hallucinate;\nno Indian-law grounding study", NAVY),
        ("2. Literature survey\nIEEE Xplore, Scopus, ACL,\nGoogle Scholar (2020-2026)", NAVY),
        ("3. Gap analysis\ncontext truncation, refusal,\nJSON robustness untested", NAVY),
        ("4. Objectives & hypotheses\nH1 grounding vs closed-book\nH2 retrieval vs truncation", BLUE),
        ("5. Dataset construction\nCV-LegalQA-42 ground truth\n+ 3 real LLM graph outputs", BLUE),
        ("6. Implementation\nCourt Vision AI (FastAPI+Next.js)\n+ proposed CV-RAG, P4 parser", TEAL),
        ("7. Experiments\n4 QA systems x 42 questions\n5 parsers x 66 corrupted outputs", TEAL),
        ("8. Statistical analysis\nWilson CI, McNemar test,\nconfusion matrices, latency", GOLD),
        ("9. Results & conclusions\nIEEE paper, IPR filing,\nposter & demonstration", GOLD),
    ]
    pos = [(0.3, 4.6), (3.55, 4.6), (6.8, 4.6), (6.8, 2.6), (3.55, 2.6), (0.3, 2.6), (0.3, 0.6), (3.55, 0.6), (6.8, 0.6)]
    w, h = 2.9, 1.25
    for (t, c), (x, y) in zip(steps, pos):
        box(ax, x, y, w, h, t, c, fc="#F4F8FC", fs=8.6)
    for i in range(len(pos) - 1):
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        if y1 == y2:
            if x2 > x1:
                arrow(ax, x1 + w, y1 + h / 2, x2, y2 + h / 2)
            else:
                arrow(ax, x1, y1 + h / 2, x2 + w, y2 + h / 2)
        else:
            arrow(ax, x1 + w / 2, y1, x2 + w / 2, y2 + h)
    arrow(ax, 8.25, 0.6 + h, 8.25, 2.6, color=RED, ls="--")
    ax.text(8.35, 2.2, "refine if H₀\nnot rejected", fontsize=7.5, color=RED)
    fig.savefig(OUT / "fig_workflow.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def architecture():
    fig, ax = plt.subplots(figsize=(10, 6.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.4); ax.axis("off")
    box(ax, 0.2, 5.2, 9.6, 0.95, "Next.js 16 / React 19 frontend — Case Vault · Case Intelligence chat (SSE) · Evidence Graph (SVG)\n"
        "Virtual Courtroom · Trial Prep & Reports · Legal Precedents research", BLUE, fc="#EAF2FB", fs=8.8)
    box(ax, 0.2, 3.7, 9.6, 1.0, "FastAPI backend (REST + Server-Sent Events) — JWT auth · case & document services · audit log",
        NAVY, fc="#E8ECF4", fs=9)
    mods = ["Chat /\nSummary", "Evidence\nGraph", "Virtual\nCourtroom", "Trial\nBrief", "Precedent\nResearch"]
    for i, m in enumerate(mods):
        box(ax, 0.35 + i * 1.92, 2.2, 1.65, 1.0, m, TEAL, fc="#E9F5F2", fs=8.6)
        arrow(ax, 0.35 + i * 1.92 + 0.82, 3.7, 0.35 + i * 1.92 + 0.82, 3.2)
    box(ax, 0.2, 0.3, 3.0, 1.3, "PDF ingestion\nmagic-byte + size validation\nPyMuPDF text extraction", GREY, fc="#F2F2F2", fs=8.3)
    box(ax, 3.5, 0.3, 3.0, 1.3, "Groq LLM layer\ngpt-oss-120b → qwen3 → gpt-oss-20b\nfallback chain · JSON recovery", GOLD, fc="#FBF5E6", fs=8.3)
    box(ax, 6.8, 0.3, 3.0, 1.3, "Persistence\nSQLite / PostgreSQL (SQLAlchemy)\nlocal file store · graph cache", GREY, fc="#F2F2F2", fs=8.3)
    arrow(ax, 5, 5.2, 5, 4.7, style="<|-|>")
    for x in (1.7, 5.0, 8.3):
        arrow(ax, x, 2.2, x, 1.6, style="<|-|>")
    fig.savefig(OUT / "fig_architecture.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def cvrag():
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.6); ax.axis("off")
    s = [("Case\nPDFs", GREY), ("Page-aware\nextraction,\nboilerplate\nremoval", NAVY), ("1,000-char\nchunks,\n200 overlap,\n[page tag]", NAVY),
         ("BM25\nindex\nk1=1.5\nb=0.75", BLUE), ("Top-k = 6\nexcerpts in\ndocument\norder", BLUE),
         ("Legal\ngrounding\nprompt +\ncite/abstain\nrules", TEAL), ("gpt-oss-\n120b\nT = 0.2", GOLD)]
    w = 1.25
    for i, (t, c) in enumerate(s):
        box(ax, 0.1 + i * 1.42, 1.6, w, 1.35, t, c, fc="#F4F8FC", fs=7.6)
        if i:
            arrow(ax, 0.1 + (i - 1) * 1.42 + w, 2.27, 0.1 + i * 1.42, 2.27)
    box(ax, 5.8, 0.15, 4.0, 0.95, "Answer with *(Source: doc, p. N)* citations\nor \"not available in the uploaded documents\"", RED, fc="#FBEDEC", fs=8)
    arrow(ax, 0.1 + 6 * 1.42 + w / 2, 1.6, 8.6, 1.1)
    box(ax, 0.1, 0.15, 5.3, 0.95, "User question  ──►  tokenise + stop-word removal  ──►  BM25 query", GREY, fc="white", fs=8)
    arrow(ax, 4.6, 1.1, 0.1 + 3 * 1.42 + w / 2, 1.6)
    fig.savefig(OUT / "fig_cvrag.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def logo():
    from matplotlib.patches import Circle
    fig, ax = plt.subplots(figsize=(5, 2))
    ax.set_xlim(0, 5); ax.set_ylim(0, 2); ax.axis("off")
    ax.add_patch(Circle((0.95, 1), 0.78, color=NAVY))
    ax.add_patch(Circle((0.95, 1), 0.68, fill=False, ec=GOLD, lw=2))
    ax.text(0.95, 0.98, "⚖", fontsize=44, ha="center", va="center", color="white")
    ax.text(1.95, 1.15, "COURT VISION", fontsize=24, fontweight="bold", color=NAVY, va="center")
    ax.text(1.97, 0.58, "AI  ·  CASE INTELLIGENCE", fontsize=11, color=GOLD, va="center", fontweight="bold")
    fig.savefig(OUT / "fig_logo.png", dpi=220, bbox_inches="tight", transparent=False, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    workflow(); architecture(); cvrag(); logo()
    print("ok", sorted(p.name for p in OUT.iterdir()))
