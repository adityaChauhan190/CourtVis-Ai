"""Diagrams for the Court Vision AI blackbook (drawn from the actual code base)."""
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle

OUT = Path(__file__).resolve().parent / "fig"
OUT.mkdir(exist_ok=True)
NAVY, BLUE, TEAL, GOLD, GREY, RED = "#1F3864", "#2E75B6", "#2E8B7A", "#B8860B", "#595959", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def box(ax, x, y, w, h, text, ec=NAVY, fc="#F4F8FC", fs=8.5, bold=False, round_=True):
    if round_:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", lw=1.3, ec=ec, fc=fc))
    else:
        ax.add_patch(Rectangle((x, y), w, h, lw=1.3, ec=ec, fc=fc))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2, text=None, color=GREY, ls="-", fs=7.5, both=False):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<|-|>" if both else "-|>", color=color, lw=1.2, ls=ls, shrinkA=2, shrinkB=2))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, text, fontsize=fs, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


def actor(ax, x, y, name):
    ax.add_patch(plt.Circle((x, y + 0.55), 0.13, fill=False, lw=1.3))
    ax.plot([x, x], [y + 0.42, y + 0.05], color="black", lw=1.3)
    ax.plot([x - 0.22, x + 0.22], [y + 0.3, y + 0.3], color="black", lw=1.3)
    ax.plot([x, x - 0.18], [y + 0.05, y - 0.25], color="black", lw=1.3)
    ax.plot([x, x + 0.18], [y + 0.05, y - 0.25], color="black", lw=1.3)
    ax.text(x, y - 0.32, name, ha="center", va="top", fontsize=8.5, fontweight="bold")


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def use_case():
    fig, ax = plt.subplots(figsize=(10, 7.4)); ax.set_xlim(0, 10); ax.set_ylim(0, 7.4); ax.axis("off")
    ax.add_patch(Rectangle((2.2, 0.2), 5.6, 7.0, fill=False, lw=1.5))
    ax.text(5.0, 6.95, "Court Vision AI", ha="center", fontsize=10, fontweight="bold")
    cases = ["Register / Log in", "Create & manage case", "Upload case PDFs", "Chat with case (cited answers)",
             "View structured case summary", "Explore evidence graph", "Argue in virtual courtroom",
             "Request verdict & scorecard", "Generate trial-prep brief", "Search precedents (library + AI)",
             "Index judgment into precedent library"]
    ys = [6.45 - i * 0.57 for i in range(len(cases))]
    for c, y in zip(cases, ys):
        ax.add_patch(Ellipse((5.0, y), 3.7, 0.46, fill=True, fc="#F4F8FC", ec=BLUE, lw=1.2))
        ax.text(5.0, y, c, ha="center", va="center", fontsize=8.2)
    actor(ax, 0.9, 3.6, "Advocate /\nLaw student")
    actor(ax, 9.1, 4.8, "Groq LLM\n(gpt-oss-120b)")
    actor(ax, 9.1, 1.6, "Background\nworker")
    for y in ys[:10]:
        ax.plot([1.15, 3.15], [3.9, y], color=GREY, lw=0.7)
    for y in (ys[3], ys[4], ys[5], ys[6], ys[7], ys[8], ys[9]):
        ax.plot([8.85, 6.85], [5.1, y], color=GOLD, lw=0.7, ls="--")
    for y in (ys[2], ys[10]):
        ax.plot([8.85, 6.85], [1.9, y], color=TEAL, lw=0.7, ls="--")
    save(fig, "uml_use_case.png")


def sequence():
    fig, ax = plt.subplots(figsize=(11, 7)); ax.set_xlim(0, 11); ax.set_ylim(0, 7.2); ax.axis("off")
    parts = ["Advocate\n(Browser)", "Next.js\nfrontend", "FastAPI\nroute", "Retrieval\n(BM25)", "Precedent\nlibrary", "Groq LLM"]
    xs = [0.8 + i * 1.9 for i in range(len(parts))]
    for x, p in zip(xs, parts):
        box(ax, x - 0.75, 6.4, 1.5, 0.65, p, fs=8, bold=True)
        ax.plot([x, x], [0.2, 6.4], color=GREY, lw=0.8, ls="--")
    msgs = [(0, 1, "Open Trial Prep, select case"), (1, 2, "GET /cases/{id}/trial-brief"),
            (2, 3, "case_chunks(): page-tagged chunks"), (3, 2, "date / witness / issue excerpts"),
            (2, 5, "Chronology prompt (JSON)"), (5, 2, "chronology[] with page cites"),
            (2, 5, "Cross-examination prompt"), (5, 2, "witness question bank"),
            (2, 5, "Synopsis prompt"), (5, 2, "7-section synopsis"),
            (2, 4, "search(case issues)"), (4, 2, "related precedents + citations"),
            (2, 1, "brief JSON (+ errors if any section failed)"), (1, 0, "render tabs, export Markdown")]
    y = 6.0
    for a, b, t in msgs:
        dash = "--" if xs[b] < xs[a] else "-"
        arrow(ax, xs[a], y, xs[b], y, color=NAVY if dash == "-" else GREY, ls=dash)
        ax.text((xs[a] + xs[b]) / 2, y + 0.1, t, ha="center", fontsize=7.4)
        y -= 0.42
    save(fig, "uml_sequence.png")


def class_diagram():
    fig, ax = plt.subplots(figsize=(11, 6.6)); ax.set_xlim(0, 11); ax.set_ylim(0, 6.6); ax.axis("off")

    def cls(x, y, w, name, attrs):
        h = 0.38 + 0.25 * len(attrs)
        ax.add_patch(Rectangle((x, y - h), w, h, fc="#F4F8FC", ec=NAVY, lw=1.2))
        ax.add_patch(Rectangle((x, y - 0.38), w, 0.38, fc="#DCE6F2", ec=NAVY, lw=1.2))
        ax.text(x + w / 2, y - 0.19, name, ha="center", va="center", fontsize=9, fontweight="bold")
        for i, a in enumerate(attrs):
            ax.text(x + 0.08, y - 0.55 - 0.25 * i, a, fontsize=7.4, va="center", family="DejaVu Sans Mono")
        return (x, y, w, h)

    u = cls(0.2, 6.4, 2.3, "User", ["id: UUID", "email: str", "name: str", "hashed_password", "role: admin|user", "is_active: bool"])
    c = cls(3.2, 6.4, 2.6, "Case", ["id: UUID", "owner_id: FK User", "name, case_number", "case_type: enum", "user_role: enum",
                                     "status: enum", "evidence_graph: JSON"])
    d = cls(6.5, 6.4, 2.6, "Document", ["id: UUID", "case_id: FK Case", "original_name", "storage_path", "page_count: int",
                                         "status: uploading|", "  processing|ready|failed"])
    p = cls(6.5, 2.9, 4.3, "Precedent  (knowledge base)", ["id, content_hash (unique)", "case_title, citation, court", "ratio_decidendi, key_principles[]",
                                                           "statutory_provisions[], keywords[]", "pages: [{page, text}]", "extraction: ai|heuristic|cited",
                                                           "cited_in_id → Precedent"])
    j = cls(9.5, 6.4, 1.4, "ProcessingJob", ["document_id", "status", "error_message"])
    a = cls(3.2, 2.9, 2.6, "AuditLog", ["user_id, case_id", "document_id", "action: enum", "log_metadata: JSON", "created_at"])
    m = cls(0.2, 2.9, 2.3, "CaseMember", ["case_id: FK", "user_id: FK", "role: viewer|…"])
    arrow(ax, 2.5, 5.6, 3.2, 5.6, "1  owns  *")
    arrow(ax, 5.8, 5.6, 6.5, 5.6, "1  has  *")
    arrow(ax, 9.1, 5.9, 9.5, 5.9)
    arrow(ax, 7.8, 4.3, 7.8, 2.9, "indexed into  0..1")
    arrow(ax, 4.5, 4.4, 4.5, 2.9, "*")
    arrow(ax, 1.35, 4.6, 1.35, 2.9, "*")
    ax.annotate("", xy=(10.8, 1.2), xytext=(10.8, 2.3), arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-0.9", color=GOLD))
    ax.text(10.55, 1.0, "cites", fontsize=7.5, color=GOLD)
    save(fig, "uml_class.png")


def block():
    fig, ax = plt.subplots(figsize=(11, 6.3)); ax.set_xlim(0, 11); ax.set_ylim(0, 6.3); ax.axis("off")
    box(ax, 0.2, 5.1, 10.6, 0.95, "PRESENTATION LAYER — Next.js 16 / React 19\nCase Vault · Document library · Case Intelligence chat (SSE) · Evidence Graph (SVG lanes/orbit) · "
        "Virtual Courtroom · Trial Prep & Reports · Legal Precedents", ec=BLUE, fc="#EAF2FB", fs=8.5)
    box(ax, 0.2, 3.85, 10.6, 0.85, "API LAYER — FastAPI (REST + Server-Sent Events) · JWT auth · validation · error handlers · CORS", ec=NAVY, fc="#E8ECF4", fs=8.5)
    mods = ["Case Intelligence\n& Case Snapshot", "Evidence\nGraph", "Virtual\nCourtroom", "Trial Prep &\nBrief Generator", "Legal\nPrecedents"]
    for i, mname in enumerate(mods):
        box(ax, 0.35 + i * 2.1, 2.55, 1.8, 0.95, mname, ec=TEAL, fc="#E9F5F2", fs=8.5, bold=True)
    box(ax, 0.2, 1.25, 3.3, 0.95, "Retrieval service\npage-tagged chunks · Okapi BM25", ec=GOLD, fc="#FBF5E6", fs=8)
    box(ax, 3.85, 1.25, 3.3, 0.95, "LLM service (Groq)\nmodel fallback · 429 wait · JSON repair", ec=GOLD, fc="#FBF5E6", fs=8)
    box(ax, 7.5, 1.25, 3.3, 0.95, "Precedent service\nindex judgments · extract cited cases", ec=GOLD, fc="#FBF5E6", fs=8)
    box(ax, 0.2, 0.1, 3.3, 0.8, "PDF ingestion worker\nvalidation · PyMuPDF · status", ec=GREY, fc="#F2F2F2", fs=8)
    box(ax, 3.85, 0.1, 3.3, 0.8, "PostgreSQL / SQLite\n(SQLAlchemy ORM)", ec=GREY, fc="#F2F2F2", fs=8)
    box(ax, 7.5, 0.1, 3.3, 0.8, "File storage\n(local volume / S3-ready)", ec=GREY, fc="#F2F2F2", fs=8)
    arrow(ax, 5.5, 5.1, 5.5, 4.7, both=True)
    for i in range(5):
        arrow(ax, 1.25 + i * 2.1, 3.85, 1.25 + i * 2.1, 3.5)
    for x in (1.85, 5.5, 9.15):
        arrow(ax, x, 2.55, x, 2.2, both=True)
        arrow(ax, x, 1.25, x, 0.9, both=True)
    save(fig, "block_diagram.png")


def dfd0():
    fig, ax = plt.subplots(figsize=(10, 4.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 4.6); ax.axis("off")
    box(ax, 0.2, 1.8, 1.9, 1.0, "Advocate /\nLaw student", ec=NAVY, fc="#EAF2FB", round_=False, bold=True)
    ax.add_patch(plt.Circle((5.0, 2.3), 1.35, fc="#E9F5F2", ec=TEAL, lw=1.6))
    ax.text(5.0, 2.3, "0\nCourt Vision AI\nsystem", ha="center", va="center", fontsize=10, fontweight="bold")
    box(ax, 7.9, 3.2, 1.9, 0.9, "Groq LLM API", ec=GOLD, fc="#FBF5E6", round_=False, bold=True)
    box(ax, 7.9, 0.5, 1.9, 0.9, "Indian legal\nrecords (PDF)", ec=GREY, fc="#F2F2F2", round_=False, bold=True)
    arrow(ax, 2.1, 2.55, 3.65, 2.55, "case details, PDFs,\nquestions, arguments")
    arrow(ax, 3.65, 2.05, 2.1, 2.05, "cited answers, graph,\nbrief, verdict, precedents")
    arrow(ax, 6.2, 2.9, 7.9, 3.55, "grounded prompts")
    arrow(ax, 7.9, 3.35, 6.3, 2.6, "JSON / text")
    arrow(ax, 7.9, 0.95, 6.15, 1.7, "judgments, FIRs")
    save(fig, "dfd_level0.png")


def dfd1():
    fig, ax = plt.subplots(figsize=(11, 7.4)); ax.set_xlim(0, 11); ax.set_ylim(0, 7.3); ax.axis("off")

    def proc(x, y, n, t):
        ax.add_patch(plt.Circle((x, y), 0.72, fc="#E9F5F2", ec=TEAL, lw=1.4))
        ax.text(x, y, f"{n}\n{t}", ha="center", va="center", fontsize=7.6, fontweight="bold")

    def store(x, y, t):
        ax.plot([x, x + 2.0], [y + 0.25, y + 0.25], color=NAVY, lw=1.3)
        ax.plot([x, x + 2.0], [y - 0.25, y - 0.25], color=NAVY, lw=1.3)
        ax.plot([x, x], [y - 0.25, y + 0.25], color=NAVY, lw=1.3)
        ax.text(x + 1.0, y, t, ha="center", va="center", fontsize=8)

    box(ax, 0.1, 3.2, 1.5, 0.8, "Advocate", ec=NAVY, fc="#EAF2FB", round_=False, bold=True)
    proc(2.7, 5.9, "1.0", "Authenticate\n& manage case")
    proc(2.7, 3.6, "2.0", "Upload &\nvalidate PDF")
    proc(5.3, 3.6, "3.0", "Extract text,\nchunk pages")
    proc(5.3, 1.2, "4.0", "Index into\nprecedent KB")
    proc(8.0, 5.9, "5.0", "Grounded AI\nfeatures")
    proc(8.0, 3.6, "6.0", "Precedent\nsearch")
    store(1.0, 1.9, "D1  Cases / Users")
    store(4.3, 6.4, "D2  Documents + files")
    store(7.0, 1.2, "D3  Precedents")
    box(ax, 9.6, 4.6, 1.3, 0.8, "Groq\nLLM", ec=GOLD, fc="#FBF5E6", round_=False, bold=True)
    arrow(ax, 1.6, 3.8, 2.0, 5.6, "login, case")
    arrow(ax, 1.6, 3.6, 1.98, 3.6, "PDF")
    arrow(ax, 2.1, 5.45, 1.82, 2.18, both=True)
    ax.text(1.62, 2.75, "case rows", fontsize=7.5, ha="right")
    arrow(ax, 3.42, 3.6, 4.58, 3.6, "valid PDF")
    arrow(ax, 4.6, 4.1, 5.0, 6.15, "file + status")
    arrow(ax, 5.3, 2.88, 5.3, 1.92, "page text")
    arrow(ax, 6.02, 1.2, 7.0, 1.2, "judgment +\ncited cases")
    arrow(ax, 6.0, 3.95, 7.4, 5.5, "excerpts")
    arrow(ax, 8.72, 5.9, 9.6, 5.1, "prompts", both=True)
    arrow(ax, 8.0, 1.45, 8.0, 2.88, "matches")
    arrow(ax, 8.0, 4.32, 8.0, 5.18, "related\nprecedents")
    ax.plot([8.0, 8.0, 0.55], [6.62, 6.95, 6.95], color=NAVY, lw=1.2)
    ax.text(5.0, 7.03, "answers · evidence graph · brief · verdict · precedents", ha="center", fontsize=7.6, color=NAVY)
    arrow(ax, 0.55, 4.6, 0.55, 4.0, color=NAVY)
    ax.plot([0.55, 0.55], [6.95, 4.6], color=NAVY, lw=1.2)
    save(fig, "dfd_level1.png")


PLAN = [  # (task, start, end, status)
    ("Problem identification & literature survey", date(2026, 8, 3), date(2026, 8, 14), "done"),
    ("Requirements & methodology design", date(2026, 8, 15), date(2026, 8, 28), "done"),
    ("Core platform: auth, cases, PDF ingestion", date(2026, 8, 16), date(2026, 9, 12), "done"),
    ("Case Intelligence chat & summary", date(2026, 8, 25), date(2026, 9, 20), "done"),
    ("Evidence graph & virtual courtroom", date(2026, 9, 10), date(2026, 10, 5), "done"),
    ("Trial brief & precedent research", date(2026, 9, 25), date(2026, 10, 10), "done"),
    ("Evaluation (CV-LegalQA-42, JSON robustness)", date(2026, 10, 11), date(2026, 10, 19), "done"),
    ("Precedent KB, grounded brief, graph de-duplication", date(2026, 10, 19), date(2026, 10, 25), "done"),
    ("Research paper, IPR filing, blackbook", date(2026, 10, 20), date(2026, 11, 10), "active"),
    ("Grounded chat (CV-RAG) & multi-document evaluation", date(2027, 1, 5), date(2027, 2, 15), "planned"),
    ("User study with advocates / law students", date(2027, 2, 1), date(2027, 3, 15), "planned"),
    ("Deployment, final testing & report", date(2027, 3, 10), date(2027, 4, 15), "planned"),
]


def gantt():
    fig, ax = plt.subplots(figsize=(11, 5.4))
    col = {"done": TEAL, "active": GOLD, "planned": "#9DB5D4"}
    for i, (t, s, e, st) in enumerate(PLAN):
        ax.barh(i, (e - s).days, left=mdates.date2num(s), color=col[st], edgecolor="white", height=0.62)
    ax.set_yticks(range(len(PLAN))); ax.set_yticklabels([p[0] for p in PLAN], fontsize=8.5); ax.invert_yaxis()
    ax.xaxis_date(); ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.axvline(mdates.date2num(date(2026, 10, 19)), color=RED, lw=1.2, ls="--")
    ax.text(mdates.date2num(date(2026, 10, 21)), -0.7, "today (19 Oct 2026)", color=RED, fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color="#E5E5E5")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=col["done"], label="Completed"), Patch(color=col["active"], label="In progress"),
                       Patch(color=col["planned"], label="Planned (Sem VIII)")], loc="lower right", fontsize=8)
    ax.set_title("Project Gantt chart — AY 2026-27", fontsize=11, fontweight="bold")
    save(fig, "gantt.png")


def timeline():
    ms = [(date(2026, 8, 14), "Gap identified\n(Exp. 1)"), (date(2026, 8, 28), "Methodology\nfrozen"),
          (date(2026, 9, 12), "PDF ingestion\n& case vault live"), (date(2026, 9, 20), "Grounded chat\n+ summary"),
          (date(2026, 10, 5), "Evidence graph\n+ courtroom"), (date(2026, 10, 10), "Trial brief +\nresearch"),
          (date(2026, 10, 19), "Evaluation:\nCV-RAG 42/42"), (date(2026, 10, 25), "Precedent KB\n(22 authorities)"),
          (date(2026, 11, 10), "Paper, IPR,\nblackbook"), (date(2027, 2, 15), "Grounded chat\n(planned)"),
          (date(2027, 4, 15), "Final submission\n(planned)")]
    fig, ax = plt.subplots(figsize=(11, 3.4))
    ax.axhline(0, color=NAVY, lw=2)
    for i, (d, t) in enumerate(ms):
        up = 1 if i % 2 == 0 else -1
        planned = d > date(2026, 11, 10)
        ax.plot([i, i], [0, 0.5 * up], color=GREY, lw=1)
        ax.scatter([i], [0], s=70, color="#9DB5D4" if planned else TEAL, zorder=3, edgecolor=NAVY)
        ax.text(i, 0.56 * up, t, ha="center", va="bottom" if up > 0 else "top", fontsize=7.8)
        ax.text(i, -0.12 * up, d.strftime("%d %b %Y"), ha="center", va="top" if up > 0 else "bottom", fontsize=6.8, color=GREY)
    ax.set_xlim(-0.6, len(ms) - 0.4); ax.set_ylim(-1.35, 1.35); ax.axis("off")
    ax.set_title("Milestone timeline (completed = green, planned = blue)", fontsize=11, fontweight="bold")
    save(fig, "timeline.png")


if __name__ == "__main__":
    use_case(); sequence(); class_diagram(); block(); dfd0(); dfd1(); gantt(); timeline()
    print(sorted(p.name for p in OUT.iterdir()))
