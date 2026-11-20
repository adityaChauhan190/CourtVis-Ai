"""Build the Court Vision AI capstone blackbook from the VESIT 2026-27 template.

Terminology used consistently throughout the report
  * "feature"  — one of the six user-facing capabilities, always called by its in-app name:
                 Case Intelligence, Case Snapshot, Evidence Graph, Virtual Courtroom,
                 Trial Prep & Brief Generator, Legal Precedents
  * "service"  — a shared backend component (retrieval service, LLM service, precedent service)
  * "precedent library" — the knowledge base of judgments and cited authorities
Citations are written as [@key] and numbered in order of first appearance (IEEE style).
"""
import json
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Twips, Inches

from bb_lib import Builder, field_paragraph, replace_in_element, add_runs, _font, simple_field_run

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
FIG = HERE / "fig"
SCR = HERE / "screens"
EFIG = EXP / "figures"
R = json.loads((EXP / "eval/results/summary.json").read_text())
SMOKE = json.loads((EXP / "eval/results/module_smoke.json").read_text())
S = R["systems"]; J = R["json_robustness"]["parsers"]
S1, S2, S3, S4 = "S1_CV_Trunc", "S2_CV_RAG", "S3_ClosedBook", "S4_BM25_Extract"
MC = {(m["a"], m["b"]): m for m in R["mcnemar"]}
SMOKE_NAMES = {"Health": "Server health check", "Case documents": "Document listing", "Structured summary": "Case Snapshot",
               "Grounded chat": "Case Intelligence", "Evidence graph (cached)": "Evidence Graph",
               "Virtual courtroom turn": "Virtual Courtroom (argument)", "Courtroom verdict": "Virtual Courtroom (verdict)",
               "Trial brief": "Trial Prep & Brief Generator", "Precedent research": "Legal Precedents"}

TITLE = "Court Vision AI: An AI-Powered Case Intelligence and Trial Preparation Platform for Indian Legal Practice"
SHORT = "Court Vision AI"
TEAM = [("Aditya Chauhan", "30", "D20B"), ("Pranita Bhortakke", "29", "D20B"),
        ("Binoy Chhatwani", "32", "D20B"), ("Vanshika Keshwani", "59", "D20C")]
TOKEN_SAVING = 1 - S[S2]["prompt_tokens_mean"] / S[S1]["prompt_tokens_mean"]


def pc(x, d=1):
    return f"{x * 100:.{d}f}%"


def pv(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


REFS = {
    "magesh": 'V. Magesh, F. Surani, M. Dahl, M. Suzgun, C. D. Manning, and D. E. Ho, "Hallucination-free? Assessing the reliability of leading AI legal research tools," *Journal of Empirical Legal Studies*, vol. 22, pp. 216–242, 2025, doi: 10.1111/jels.12413.',
    "dahl": 'M. Dahl, V. Magesh, M. Suzgun, and D. E. Ho, "Large legal fictions: Profiling legal hallucinations in large language models," *Journal of Legal Analysis*, vol. 16, no. 1, p. 64, 2024. [Online]. Available: https://arxiv.org/abs/2401.01301',
    "iltur": 'A. Joshi, S. Paul, A. Sharma, P. Goyal, S. Ghosh, and A. Modi, "IL-TUR: Benchmark for Indian legal text understanding and reasoning," in *Proc. 62nd Annual Meeting of the Association for Computational Linguistics (ACL)*, Bangkok, Thailand, 2024, pp. 11460–11499. [Online]. Available: https://aclanthology.org/2024.acl-long.618',
    "ildc": 'V. Malik, R. Sanjay, S. K. Nigam, K. Ghosh, S. K. Guha, A. Bhattacharya, and A. Modi, "ILDC for CJPE: Indian legal documents corpus for court judgment prediction and explanation," in *Proc. ACL-IJCNLP*, 2021, pp. 4046–4062, doi: 10.18653/v1/2021.acl-long.313.',
    "inlegal": 'S. Paul, A. Mandal, P. Goyal, and S. Ghosh, "Pre-trained language models for the legal domain: A case study on Indian law," in *Proc. 19th International Conference on Artificial Intelligence and Law (ICAIL)*, Braga, Portugal, 2023, doi: 10.1145/3594536.3595165.',
    "legalbench": 'N. Guha et al., "LegalBench: A collaboratively built benchmark for measuring legal reasoning in large language models," in *Advances in Neural Information Processing Systems 36 (Datasets and Benchmarks Track)*, 2023. [Online]. Available: https://arxiv.org/abs/2308.11462',
    "agentcourt": 'G. Chen et al., "AgentCourt: Simulating court with adversarial evolvable lawyer agents," in *Findings of the Association for Computational Linguistics: ACL 2025*. [Online]. Available: https://arxiv.org/abs/2408.08089',
    "graphrag": 'D. Edge et al., "From local to global: A graph RAG approach to query-focused summarization," arXiv:2404.16130, 2024.',
    "rag": 'P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Advances in Neural Information Processing Systems 33*, 2020, pp. 9459–9474. [Online]. Available: https://arxiv.org/abs/2005.11401',
    "lexglue": 'I. Chalkidis, A. Jana, D. Hartung, M. Bommarito, I. Androutsopoulos, D. M. Katz, and N. Aletras, "LexGLUE: A benchmark dataset for legal language understanding in English," in *Proc. 60th Annual Meeting of the ACL*, 2022, pp. 4310–4330, doi: 10.18653/v1/2022.acl-long.297.',
    "ji": 'Z. Ji et al., "Survey of hallucination in natural language generation," *ACM Computing Surveys*, vol. 55, no. 12, Art. 248, 2023, doi: 10.1145/3571730.',
    "bm25": 'S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333–389, 2009, doi: 10.1561/1500000019.',
    "jacob": '*Jacob Mathew v. State of Punjab & Anr.*, (2005) 6 SCC 1, Supreme Court of India, decided 5 Aug. 2005.',
    "bns": 'Government of India, *The Bharatiya Nyaya Sanhita, 2023* (Act No. 45 of 2023); *The Bharatiya Nagarik Suraksha Sanhita, 2023* (Act No. 46 of 2023); *The Bharatiya Sakshya Adhiniyam, 2023* (Act No. 47 of 2023).',
    "fastapi": 'S. Ramírez, "FastAPI documentation." [Online]. Available: https://fastapi.tiangolo.com',
    "nextjs": 'Vercel, "Next.js documentation." [Online]. Available: https://nextjs.org/docs',
    "pymupdf": 'Artifex Software, "PyMuPDF documentation." [Online]. Available: https://pymupdf.readthedocs.io',
    "groq": 'Groq Inc., "GroqCloud API documentation." [Online]. Available: https://console.groq.com/docs',
    "mcnemar": 'Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," *Psychometrika*, vol. 12, no. 2, pp. 153–157, 1947, doi: 10.1007/BF02295996.',
    "ipr": 'Government of India, *The Copyright Act, 1957* and *The Copyright Rules, 2013*; *The Patents Act, 1970*, Section 3(k); *The Trade Marks Act, 1999*.',
}

ABSTRACT = (
    "Preparing for a court hearing requires advocates and law students to read long judgments, FIRs and witness statements, and then to "
    "organise the facts, the witnesses and the relevant precedents by hand. General-purpose AI chatbots can help with this reading, but they "
    "often invent facts and case citations, which is unacceptable in legal work. This project presents Court Vision AI, a web application that "
    "helps users prepare a case using only the documents they upload. After uploading the case files, a user can ask questions and receive "
    "answers with page references, read a short summary of the case, explore an evidence graph of the people, facts and documents involved, "
    "practise arguments in a virtual courtroom against an AI judge and an AI opposing counsel, generate a trial-preparation brief, and search "
    "for related precedents. Every judgment uploaded to the system is also added to a growing precedent library, together with the earlier "
    "cases that it cites. To keep the answers reliable, the system first finds the most relevant pages of the case file and then asks the AI to "
    "answer only from those pages, to cite them, and to say so when the answer is not in the documents. In tests on a Supreme Court judgment, "
    "this approach handled all 42 test questions correctly: it answered the 30 questions that the judgment could answer and declined the 12 "
    "that it could not. The same AI without the documents handled only 11 of the 42 questions correctly. Court Vision AI therefore offers a "
    "reliable, low-cost aid for legal case preparation in India.")
KEYWORDS = "Keywords — Legal technology, artificial intelligence, case preparation, Indian law, precedent search, evidence graph"

ACK = (
    f"The project report on “{SHORT}” is the outcome of the guidance, moral support and devotion bestowed on our group throughout "
    "our work. For this, we acknowledge and express our profound sense of gratitude to everybody who has been a source of inspiration "
    "throughout the preparation of this project. First and foremost, we offer our sincere thanks to Dr.(Mrs.) Shalu Chopra, Head of the "
    "Department of Information Technology, and to our project guide, Dr. Asma Praveen, for her valuable inputs and their consistent "
    "guidance and support. We are also grateful to Dr.(Mrs.) J. M. Nair, Principal, for her encouragement. Finally, we thank Vivekanand "
    "Education Society’s Institute of Technology for providing a stimulating atmosphere and a conducive work environment.")


# ═════════════════════════════════════════════════════════════════════════════
# Front matter (edited in place in the template)
# ═════════════════════════════════════════════════════════════════════════════

def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def para_with(kids, needle, start=0):
    return next(i for i, k in enumerate(kids) if i >= start and needle in text_of(k))


def P(d, el):
    return docx.text.paragraph.Paragraph(el, d._body)


def set_para_text(d, el, text, size=12, bold=None, italic=None, font="Times New Roman"):
    p = P(d, el)
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    add_runs(p, text, size=size, bold=bold, italic=italic, font=font)
    return p


def signature_table(d, before_el):
    """Name / roll number / signature table for the four team members."""
    t = d.add_table(rows=len(TEAM) + 1, cols=3)
    widths = [3400, 2100, 3000]
    t._tbl.tblPr.append(_jc("center"))
    for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))
    head = ["Name of the Student", "Roll No. / Division", "Signature"]
    for ri, row in enumerate([head] + [[n, f"{r} / {dv}", ""] for n, r, dv in TEAM]):
        for ci, val in enumerate(row):
            cell = t.cell(ri, ci); cell.width = Twips(widths[ci])
            par = cell.paragraphs[0]
            par.paragraph_format.space_before = Pt(10); par.paragraph_format.space_after = Pt(4)
            if ci == 2 and ri > 0:
                add_runs(par, "- - - - - - - - - - - -", size=12)
            else:
                add_runs(par, val, size=12, bold=True if ri == 0 else None)
    before_el.addprevious(t._tbl)


def _jc(v):
    e = OxmlElement("w:jc"); e.set(qn("w:val"), v); return e


def replace_signature_block(d, body, heading_text):
    """Replace '- - -' / '(Signature)' / 'Name of the Student (Roll No.)' with a team table."""
    kids = list(body.iterchildren())
    h = para_with(kids, heading_text)
    name_i = para_with(kids, "Name of the Student (Roll No.)", h)
    dash_i = next(i for i in range(name_i, h, -1) if "- - -" in text_of(kids[i]))
    signature_table(d, kids[dash_i])
    for k in kids[dash_i:name_i + 1]:
        if k.find(".//" + qn("w:sectPr")) is not None:   # keep the section break, drop the text
            for r in k.findall(qn("w:r")):
                k.remove(r)
        else:
            body.remove(k)


def _centre(el):
    """Symmetric centring: drop the template's uneven left/right/first-line indents."""
    ppr = el.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr"); el.insert(0, ppr)
    ind = ppr.find(qn("w:ind"))
    if ind is not None:
        ppr.remove(ind)
    jc = ppr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc"); ppr.append(jc)
    jc.set(qn("w:val"), "center")


def certificate_layout(d, body):
    kids = list(body.iterchildren())
    top = para_with(kids, "Certificate")
    seal = para_with(kids, "VESIT, Chembur", top)
    # 1. centre the certificate heading, title, member names and degree lines
    for k in kids[top:seal]:
        t = text_of(k).strip()
        if t and not t.startswith(("Date", "Place", "Prof.", "External", "Dr.", "H.O.D")) and k.tag == qn("w:p"):
            _centre(k)
            for tn in k.iter(qn("w:t")):
                if tn.text:
                    tn.text = tn.text.strip() if tn is list(k.iter(qn("w:t")))[0] else tn.text
    # 2. replace the two-column signature area with a borderless 2 x 2 grid
    kids = list(body.iterchildren())
    g = para_with(kids, "Prof. Guide Name")
    p_end = para_with(kids, "J.M. Nair", g)
    anchor = kids[p_end + 1]
    for k in kids[g:p_end + 1]:
        body.remove(k)
    rows = [[("Dr. Asma Praveen", "Project Mentor"), ("", "External Examiner")],
            [("Dr.(Mrs.) Shalu Chopra", "H.O.D."), ("Dr.(Mrs.) J. M. Nair", "Principal")]]
    t = d.add_table(rows=2, cols=2)
    t._tbl.tblPr.append(_jc("center"))
    for gc in t._tbl.tblGrid.findall(qn("w:gridCol")):
        gc.set(qn("w:w"), "4300")
    for ri, row in enumerate(rows):
        for ci, (name, role) in enumerate(row):
            cell = t.cell(ri, ci); cell.width = Twips(4300)
            par = cell.paragraphs[0]; par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.space_before = Pt(30 if ri else 6); par.paragraph_format.space_after = Pt(0)
            add_runs(par, name if name else " ", size=12, bold=True, font="Georgia")
            par2 = cell.add_paragraph(); par2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(par2, role, size=12, bold=True, font="Georgia")
    anchor.addprevious(t._tbl)


def front_matter(d):
    body = d.element.body
    kids = list(body.iterchildren())
    # ── Cover ── (the four-line title needs the room of the template's empty spacer lines)
    ay = para_with(kids, "AY (2026-27)")
    for k in kids[:ay]:
        if k.tag == qn("w:p") and not text_of(k).strip() and k.find(".//" + qn("w:drawing")) is None \
                and k.find(".//" + qn("w:pict")) is None and k.find(".//" + qn("w:sectPr")) is None:
            body.remove(k)
    kids = list(body.iterchildren())
    i = para_with(kids, "[PROJECT TITLE]")
    replace_in_element(kids[i], "[PROJECT TITLE]", TITLE.upper())
    i = para_with(kids, "Student Name-Roll No (00)")
    cover = P(d, kids[i])
    ind = kids[i].find(qn("w:pPr") + "/" + qn("w:ind"))
    if ind is not None:                       # full text width so each name stays on one line
        for a in ("w:left", "w:right", "w:firstLine", "w:hanging"):
            if ind.get(qn(a)) is not None:
                ind.set(qn(a), "0")
    first = cover.runs[0]
    first.text = ""
    for n, r, dv in TEAM:
        first.add_text(f"{n} - Roll No. {r} ({dv})")
        first.add_break()
    for r in cover.runs[1:]:
        if "Under the guidance" not in r.text:
            r.text = ""
    i = para_with(kids, "GUIDE NAME")
    replace_in_element(kids[i], "GUIDE NAME", "Dr. Asma Praveen")
    # ── Certificate ──
    i = para_with(kids, "Project Title”")
    for t in kids[i].iter(qn("w:t")):
        if "Project Title" in (t.text or ""):
            t.text = "“" + TITLE + "”"
    cert = [k for k in kids if "Your Name ( Roll No. xxx )" in text_of(k)]
    for k, (n, r, dv) in zip(cert, TEAM):
        for t in k.iter(qn("w:t")):
            t.text = ""
        ts = list(k.iter(qn("w:t")))
        ts[0].text = f"{n} (Roll No. {r}, {dv})"
    certificate_layout(d, body)
    kids = list(body.iterchildren())
    # ── Running "Project Title" labels on front-matter pages ──
    for k in kids:
        if text_of(k).strip() == "Project Title":
            replace_in_element(k, "Project Title", SHORT)
    # ── Abstract and keywords ──
    i = para_with(kids, "Abstracts contain most")
    set_para_text(d, kids[i], ABSTRACT, size=12)
    i = para_with(kids, "Keywords-")
    set_para_text(d, kids[i], KEYWORDS, size=11, bold=True, italic=True, font="Georgia")
    # ── Acknowledgement ──
    i = para_with(kids, "The project report on")
    set_para_text(d, kids[i], ACK, size=12)
    # ── Signature blocks (declaration and acknowledgement) ──
    replace_signature_block(d, body, "Declaration")
    replace_signature_block(d, body, "ACKNOWLEDGEMENT")

    # ── Contents → TOC field ──
    kids = list(body.iterchildren())
    c = para_with(kids, "Contents")
    e = para_with(kids, "A.II. IPR", c)
    end = next(j for j in range(e, len(kids)) if kids[j].find(".//" + qn("w:sectPr")) is not None)
    for k in kids[c + 1:end]:
        body.remove(k)
    toc = field_paragraph(d, 'TOC \\h \\z \\t "BB Chapter,1,Heading 1,2,Heading 2,3"')
    list(body.iterchildren())[c].addnext(toc._p)
    # ── List of Figures → field ──
    kids = list(body.iterchildren())
    lf = para_with(kids, "List of Figures")
    lt = para_with(kids, "List of Tables", lf)
    for k in kids[lf + 1:lt]:
        if k.find(".//" + qn("w:sectPr")) is not None:
            for r in k.findall(qn("w:r")):
                k.remove(r)
        else:
            body.remove(k)
    figs = field_paragraph(d, 'TOC \\h \\z \\t "BB Figure Caption,2"')
    list(body.iterchildren())[lf].addnext(figs._p)
    # ── List of Tables → field (section break moves to the new paragraph) ──
    kids = list(body.iterchildren())
    lt = para_with(kids, "List of Tables")
    tabs = field_paragraph(d, 'TOC \\h \\z \\t "BB Table Caption,2"')
    lt_p = kids[lt]
    sect = lt_p.find(qn("w:pPr") + "/" + qn("w:sectPr"))
    lt_p.addnext(tabs._p)
    if sect is not None:
        lt_p.find(qn("w:pPr")).remove(sect)
        tabs._p.get_or_add_pPr().append(sect)
    # ── Remove the template's sample chapters ──
    kids = list(body.iterchildren())
    ack = para_with(kids, "ACKNOWLEDGEMENT")
    ack_end = next(j for j in range(ack, len(kids)) if kids[j].tag == qn("w:p") and kids[j].find(".//" + qn("w:sectPr")) is not None)
    for k in kids[ack_end + 1:]:
        if k.tag != qn("w:sectPr"):
            body.remove(k)


def setup_chapter_section(d):
    sec = d.sections[-1]
    sec.top_margin = Twips(1440); sec.bottom_margin = Twips(1300)
    sec.left_margin = Twips(1417); sec.right_margin = Twips(1134)
    sec.header_distance = Twips(600); sec.footer_distance = Twips(600)
    sp = sec._sectPr
    pg = sp.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType"); sp.append(pg)
    pg.set(qn("w:start"), "1")
    sec.header.is_linked_to_previous = False
    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for r in list(hp.runs):
        r._r.getparent().remove(r._r)
    add_runs(hp, SHORT, size=11, italic=True)
    ppr = hp._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr"); b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "6"); b.set(qn("w:space"), "1"); b.set(qn("w:color"), "000000")
    bdr.append(b); ppr.append(bdr)
    sec.footer.is_linked_to_previous = False
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in list(fp.runs):
        r._r.getparent().remove(r._r)
    simple_field_run(fp, "PAGE")


# ═════════════════════════════════════════════════════════════════════════════
# Chapter 1
# ═════════════════════════════════════════════════════════════════════════════

FEATURES = [
    ("Case Intelligence", "a chat in which the user asks questions about the case and receives answers that refer to the source document"),
    ("Case Snapshot", "a structured summary of the case: overview, key issues, important facts and dates, evidence, weaknesses and next steps"),
    ("Evidence Graph", "an interactive map of the persons, organisations, facts, evidence and dates in the case and the relationships between them"),
    ("Virtual Courtroom", "a practice session in which an AI judge and an AI opposing counsel respond to the user's arguments, ending with a verdict and a performance scorecard"),
    ("Trial Prep & Brief Generator", "a trial-preparation brief consisting of a date-wise chronology, a witness cross-examination question bank and an executive synopsis"),
    ("Legal Precedents", "precedent research backed by a precedent library that grows with every judgment uploaded to the system"),
]


def chapter1(b: Builder):
    b.chapter_divider(1, "Introduction")
    b.chapter_title(1, "Introduction")
    b.h1("1.1  Introduction")
    b.p("Courts in India carry a very large number of pending cases, and a large part of an advocate's preparation time is spent reading: judgments that "
        "run to dozens of pages, First Information Reports (FIRs), charge-sheets, medical reports and witness statements. From these documents, the advocate "
        "has to build a chronology of events, identify the witnesses and the contradictions in their statements, frame questions for cross-examination, find "
        "binding precedents and practise oral arguments. For law students and junior advocates, who have the least experience and the least access to paid "
        "research databases, this preparation is both the most demanding and the most valuable part of learning the profession.")
    b.p("Large language models (LLMs), the technology behind modern AI chatbots, can read and summarise text, answer questions and draft arguments, and "
        "they are increasingly used by lawyers. However, research on legal AI shows that LLMs often produce false statements, a problem known as "
        "**hallucination** [@ji]. When they answer from memory, without the source documents, they invent case facts, parties and citations in 58–88% of "
        "cases [@dahl], and even commercial legal research tools that look up documents before answering still hallucinate in 17–33% of answers [@magesh]. "
        "In legal work, an invented FIR number or a non-existent precedent is not a minor error: it can mislead the court and harm the client.")
    b.p("**Court Vision AI** addresses this problem. It is a web application in which a user creates a case, uploads the case documents as PDF files, and "
        "then uses six features that all work only from those documents:")
    b.bullets([f"**{n}** — {d}." for n, d in FEATURES])
    b.p("The central technique of the project, named **CV-RAG** (Court Vision retrieval-augmented generation), divides the entire case file into short "
        "passages tagged with their page numbers, finds the passages most relevant to each request, and gives only those passages to the LLM. The LLM is "
        "instructed to cite the page for every fact and to reply that the information is not available when the passages do not contain the answer. This "
        "technique was evaluated experimentally against the application's original design, against the same LLM without documents, and against a "
        "traditional keyword-search approach.")

    b.h1("1.2  Problem Definition")
    b.p("The problem addressed by this project is to design and build a case-preparation system for Indian legal practice that:")
    b.numbered([
        "answers questions, maps evidence and prepares trial briefs strictly from the user's own case documents, with page references;",
        "declines to answer, rather than inventing facts, when the documents do not contain the answer;",
        "uses the whole of a long judgment, even though the free AI service used by the project accepts only about 8,000 tokens (roughly 30,000 characters) per minute; and",
        "builds a reusable precedent library, with verifiable citations, from the judgments that users upload.",
    ])
    b.p("At the start of this work, the Case Intelligence feature sent only the first 18,000 characters of a case to the LLM. For the 72,720-character "
        "*Jacob Mathew* judgment [@jacob] used in our evaluation, this is only 24.8% of the text, so questions about later pages could not be answered. In "
        "addition, the Case Snapshot and Trial Prep & Brief Generator features displayed fixed template text whenever the AI response could not be read, and "
        "the Evidence Graph often showed the same person or document more than once under different names.")

    b.h1("1.3  Objectives")
    b.numbered([
        "To design and develop Court Vision AI, a web application for Indian legal case preparation with case management, secure PDF upload and six document-grounded features.",
        "To propose and implement CV-RAG, a method that selects the most relevant page-tagged passages of a case file so that the AI answers from the whole file, cites pages and declines when the answer is absent, within the limits of a free AI service.",
        "To build a precedent library that automatically stores every uploaded judgment and every earlier case cited in it, together with the citation printed in the judgment.",
        "To ensure that no feature ever displays fixed template text in place of a genuine AI result, and that AI-suggested precedents are clearly separated from verified ones.",
        "To make the Evidence Graph useful to advocates by removing duplicate entities and by labelling every relationship with its legal significance.",
        "To evaluate the system quantitatively on a set of test questions with known answers, measuring accuracy, correct refusals, invented answers, response time and cost.",
    ])

    b.h1("1.4  Motivation")
    b.p("Three observations motivated this project. First, reliable legal research tools are expensive and are designed mainly for American and British law, "
        "so students and junior advocates in India often rely on free general-purpose chatbots that confidently invent case facts. In our own test, the AI "
        "model used by Court Vision AI, when asked about the *Jacob Mathew* case without the documents, answered only "
        f"{S[S3]['k_answerable']} of 30 factual questions correctly. It also invented a nurse's name, a two-year sentence, a compensation award of "
        "₹2 lakh and an FIR number, none of which appear in the judgment.")
    b.p("Second, trial preparation is a skill learnt through practice: moot courts, mock cross-examinations and feedback from senior advocates. A virtual "
        "courtroom that argues back using the facts of the student's own case, and a brief that shows how the record can be organised for trial, make such "
        "practice available at any time. Third, every judgment that a user uploads is itself a source of precedents: a Supreme Court judgment typically "
        "cites twenty or more earlier decisions with their reported citations. Capturing these citations automatically turns every upload into an addition "
        "to a growing and verifiable research library.")

    b.h1("1.5  Scope of the Work")
    b.p("The scope of the project is as follows:")
    b.bullets([
        "A web application for advocates, law students and legal researchers, with registration, secure login, a Case Vault for managing cases, PDF upload of up to 50 MB per file, and a document viewer.",
        "The six document-grounded features listed in Section 1.1.",
        "A precedent library built from uploaded judgments and the cases they cite, with each precedent labelled as verified (found in the library) or as an unverified AI suggestion.",
        "Support for the Indian legal context, including references under both the old and the new criminal laws (IPC and BNS, CrPC and BNSS, Evidence Act and BSA) [@bns].",
        "An experimental evaluation of answer accuracy and of the reliability of the system's processing of AI responses.",
    ])
    b.p("The following are outside the scope of the current phase: scanned or handwritten documents that require optical character recognition (OCR), "
        "documents in languages other than English, integration with court e-filing systems, and legal advice to the general public. Court Vision AI is a "
        "preparation and learning aid for legally trained users, and it always asks them to verify citations before relying on them.")

    b.h1("1.6  Feasibility Study")
    b.p("The feasibility of the project was assessed from five points of view, summarised in Table 1.1.")
    b.table([["Aspect", "Assessment"],
             ["Technical", "All components are mature open-source tools (FastAPI, PostgreSQL, PyMuPDF and Next.js). The AI model runs on the Groq cloud service and is accessed over the internet, so no graphics card (GPU) is required. The passage search runs in a few milliseconds on a laptop."],
             ["Economic", "Development used the team members' own laptops, free and open-source software and the free tier of the Groq service. The only expected cost is ₹1,500 for printing and binding this report (Section 3.8)."],
             ["Operational", "The complete system starts with a single command (`docker compose up`) and runs as four containers. Users need only a web browser."],
             ["Legal and ethical", "Only publicly available judgments and documents owned by the user are processed. Answers carry page references, unverified AI suggestions are labelled as such, and the interface states that the tool does not replace qualified legal advice."],
             ["Schedule", "The platform, its evaluation and this report were completed in Semester VII (August–November 2026). Further work is planned for Semester VIII (Section 3.4)."]],
            [1.3, 5], caption="Feasibility study", bold_first_col=True)

    b.h1("1.7  Organization of the Report")
    b.p("The rest of this report is organised as follows:")
    b.bullets([
        "**Chapter 2 — Literature Survey** reviews nine research papers on legal AI, Indian legal language processing, retrieval-augmented generation and court simulation, and identifies the research gaps.",
        "**Chapter 3 — Proposed Methodology** presents the requirements, the proposed algorithms, the project timeline, the UML, block and data flow diagrams, the hardware and software requirements and the cost estimate.",
        "**Chapter 4 — Implementation & Results** describes the implementation of each feature, shows the screens and outputs of the application, analyses the experimental results, and lists the limitations and observations.",
        "**Chapter 5 — Conclusion** summarises the work, outlines the future scope and gives the details of the research paper prepared from this project. The references and appendices follow.",
    ])


# ═════════════════════════════════════════════════════════════════════════════
# Chapter 2
# ═════════════════════════════════════════════════════════════════════════════

REVIEW = [
    ("magesh", "Magesh et al.", "2025", "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools",
     "Magesh et al. [@magesh] carried out the first pre-registered evaluation of commercial AI legal research tools that claim to be free of "
     "hallucinations because they retrieve documents before answering. They tested Lexis+ AI, Westlaw AI-Assisted Research and Ask Practical Law AI "
     "on more than 200 American legal research questions and found that the tools still hallucinated in 17–33% of their answers, sometimes by citing "
     "a real case for a point that the case does not support. This study shows that retrieval alone is not sufficient: the AI must also be required to "
     "cite its sources and to decline when the sources are silent, which shaped the citation and refusal rules of Court Vision AI.",
     "Retrieval-based commercial tools compared with GPT-4; manual expert grading", "Hallucination in 17–33% of answers; US law only",
     "Enforce citations and refusals, and measure citation accuracy"),
    ("dahl", "Dahl et al.", "2024", "Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models",
     "Dahl et al. [@dahl] asked publicly available LLMs (ChatGPT 3.5, PaLM 2 and Llama 2) verifiable questions about American federal court cases, "
     "without giving them any documents. The models gave false answers in 58–88% of cases, often accepted false assumptions in the question, and "
     "could not reliably tell when they were wrong. This confirms that a legal assistant must not rely on the model's memory; our own baseline "
     "without documents behaved in the same way on an Indian judgment.",
     "Questioning of three public LLMs without documents", "False answers in 58–88% of cases",
     "Answer only from the user's documents"),
    ("iltur", "Joshi et al.", "2024", "IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning",
     "Joshi et al. [@iltur] created IL-TUR, a set of eight tasks on Indian legal documents in English and nine Indian languages, such as identifying "
     "the role of each sentence in a judgment, identifying the relevant statutes and predicting judgments. Their results show that current models "
     "remain far from expert performance on Indian legal reasoning. However, the tasks are mainly classification tasks and do not cover question "
     "answering over a user's own case file, which led us to build our own set of test questions.",
     "Benchmark of eight tasks; baseline models including LLMs", "Models far from expert level; no question answering over case files",
     "Create a test set with known answers on an Indian judgment"),
    ("ildc", "Malik et al.", "2021", "ILDC for CJPE: Indian Legal Documents Corpus for Court Judgment Prediction and Explanation",
     "Malik et al. [@ildc] released a collection of about 35,000 Indian Supreme Court cases and studied whether models can predict the outcome of a "
     "case and explain the prediction. The models predicted outcomes reasonably well, but their explanations matched those of legal experts poorly. "
     "Predicting outcomes is therefore risky and is not what practitioners need for day-to-day preparation; Court Vision AI instead uses the case "
     "record to support practice and feedback.",
     "Transformer-based models on Supreme Court judgments", "Reasonable prediction; weak explanations",
     "Support preparation and practice rather than prediction"),
    ("inlegal", "Paul et al.", "2023", "Pre-trained Language Models for the Legal Domain: A Case Study on Indian Law",
     "Paul et al. [@inlegal] further trained existing legal language models on a large collection of Indian court judgments and showed that this "
     "improves the identification of relevant statutes, the division of judgments into their parts, and judgment prediction. These models classify "
     "text but cannot answer questions, hold a conversation or cite sources. This work shows that Indian legal language benefits from special "
     "handling; for answering questions, our project instead guides a general LLM with passages selected from the user's documents.",
     "Further training of BERT-based models on Indian judgments", "Better accuracy on Indian tasks; no answer generation",
     "Guide a general LLM with selected passages"),
    ("legalbench", "Guha et al.", "2023", "LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models",
     "Guha et al. [@legalbench], working with legal professionals, built LegalBench, a set of 162 tasks covering six types of legal reasoning, and "
     "used it to evaluate 20 LLMs. The models' performance varied widely across the types of reasoning. Because each task uses only a short piece of "
     "text, the benchmark does not test how a system copes with long documents, which was the main difficulty we observed in Court Vision AI.",
     "Evaluation of 20 LLMs on 162 legal tasks", "Short texts; long documents not tested; US law",
     "Focus on selecting the right parts of long documents"),
    ("agentcourt", "Chen et al.", "2025", "AgentCourt: Simulating Court with Adversarial Evolvable Lawyer Agents",
     "Chen et al. [@agentcourt] simulated court proceedings with AI agents acting as the judge and the lawyers, and improved the lawyer agents over "
     "1,000 simulated cases by making them argue against each other. Professional lawyers judged the improved agents to be more responsive and more "
     "rigorous. The simulation is based on Chinese law and the agents do not use the trainee's own case documents. The Virtual Courtroom of Court "
     "Vision AI follows the same idea for Indian practice, but grounds the judge and the opposing counsel in the user's own case file and adds a "
     "performance scorecard.",
     "AI judge and lawyer agents that improve by arguing against each other", "Chinese law; not based on the trainee's documents",
     "Ground the courtroom in the user's case file; add a scorecard"),
    ("graphrag", "Edge et al.", "2024", "From Local to Global: A Graph RAG Approach to Query-Focused Summarization",
     "Edge et al. [@graphrag] used an LLM to build a graph of the entities in a collection of documents and the relationships between them, and used "
     "summaries of this graph to answer broad questions about the collection. The approach produced more complete answers, but it is designed for "
     "general documents and assumes that the AI always returns well-formed output. Our Evidence Graph adapts the idea to legal evidence, removes "
     "duplicate entities, and recovers usable data even when the AI's output is incomplete.",
     "AI-built entity graph with community summaries", "General documents; assumes well-formed AI output",
     "Legal entity types, duplicate removal and recovery of incomplete output"),
    ("rag", "Lewis et al.", "2020", "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
     "Lewis et al. [@rag] introduced retrieval-augmented generation (RAG), in which a search component first finds relevant passages and the language "
     "model then writes its answer from them. RAG improved the factual accuracy of answers to general-knowledge questions based on Wikipedia, but it "
     "was not designed for legal documents or for strict limits on the amount of text that can be sent to the model. CV-RAG applies this principle to "
     "long Indian judgments, using page-tagged passages and a keyword-based ranking method that needs no special hardware or training.",
     "Search component combined with a text-generation model", "General knowledge only; no legal documents",
     "Apply retrieval to long judgments with page tags"),
]


def chapter2(b: Builder):
    b.chapter_divider(2, "Literature Survey")
    b.chapter_title(2, "Literature Survey")
    b.h1("2.1  Introduction")
    b.p("Before designing Court Vision AI, existing research was studied to learn which techniques work, where existing systems fail, and which problems "
        "remain open for a tool intended for legal practitioners in India. The survey covered research on the use of large language models in law, the "
        "processing of Indian legal text, retrieval-augmented generation, the construction of knowledge graphs, and the simulation of court proceedings. "
        "Earlier benchmark work on English legal text [@lexglue] and surveys of AI hallucination [@ji] were also consulted for background.")
    b.p("The sources were collected from IEEE Xplore, the ACL Anthology, the ACM Digital Library, journals published by Wiley and Oxford University Press, "
        "arXiv and Google Scholar. The search terms included “legal LLM hallucination”, “retrieval-augmented generation legal”, "
        "“Indian legal NLP benchmark”, “court simulation LLM agents” and “knowledge graph RAG”. Preference was given to recent "
        "papers published in reputed journals and conferences. For each paper, the problem, the method, the results, the limitations and the relevance to "
        "this project were noted.")

    b.h1("2.2  Review of Literature Survey")
    b.p("The nine papers reviewed are summarised below, each under its title, followed by a comparison in Table 2.1.")
    for i, (key, _, _, title, para, *_) in enumerate(REVIEW, 1):
        b.h3(f"2.2.{i}  {title}")
        b.p(para)
    rows = [["Sr. No.", "Author(s) & Year", "Paper Title", "Methodology / Technology Used", "Key Observations", "Inference Drawn"]]
    for i, (key, auth, yr, title, _, meth, obs, inf) in enumerate(REVIEW, 1):
        rows.append([str(i), f"{auth} [@{key}], {yr}", title, meth, obs, inf])
    b.table(rows, [0.5, 1.2, 1.9, 1.5, 1.5, 1.6], caption="Summary of the literature reviewed", size=8.5)

    b.h1("2.3  Research Gaps")
    b.p("Comparing the reviewed papers with existing tools revealed the gaps listed in Table 2.2, together with the way in which the proposed project "
        "addresses each of them.")
    b.table([["Sr. No.", "Existing Approach / System", "Identified Limitation / Research Gap", "Proposed Project's Approach"],
             ["1", "Commercial legal research tools [@magesh]", "Still hallucinate in 17–33% of answers; citations are hard to verify; designed for US law and costly", "Page-tagged passages, compulsory page references and an explicit rule to decline; citation accuracy measured"],
             ["2", "General-purpose LLMs used without documents [@dahl]", "Answer from memory and invent facts and citations", "Every feature answers only from the user's uploaded documents"],
             ["3", "Indian legal language research [@iltur, @ildc, @inlegal]", "Focus on classification and prediction; no evaluation of question answering or refusal on Indian judgments", "A test set of 42 questions with known answers on a Supreme Court judgment"],
             ["4", "Legal reasoning benchmarks and RAG [@legalbench, @rag]", "Limits on the amount of text that affordable AI services accept are not studied; cutting the text silently hides later pages", "CV-RAG selects the most relevant passages from the whole file within a limit of 8,000 tokens per minute"],
             ["5", "Court simulation with AI agents [@agentcourt]", "Not based on the trainee's case; not Indian procedure; no feedback to the trainee", "Judge and opposing counsel grounded in the case documents; verdict and performance scorecard"],
             ["6", "Graphs built by AI [@graphrag]", "General entity types, repeated entities, failure when the AI output is incomplete", "Legal entity types, automatic removal of duplicates and recovery of incomplete output"],
             ["7", "Precedent databases", "Paid and separate from the case file; AI tools invent citations", "Precedent library built automatically from uploaded judgments and the cases they cite; AI suggestions shown as verified only when found in the library"]],
            [0.5, 1.7, 2.4, 2.4], caption="Research gap analysis", size=9)
    b.p("The most significant gap is that **no existing system both bases every answer on the user's own long Indian case file and works within the "
        "limits of an affordable AI service**. Existing approaches either answer from the model's memory and hallucinate, or cut the case file short and "
        "miss its later pages, or depend on expensive proprietary databases. This gap justifies the design of Court Vision AI, which selects the relevant "
        "parts of the whole file for every request and builds its own verifiable precedent library.")

    b.h1("2.4  Conclusion")
    b.p("The literature shows that LLMs are useful legal assistants only when their answers are grounded in source documents. Without documents they invent "
        "legal facts at very high rates [@dahl], and even with document retrieval the problem persists unless citations and refusals are enforced "
        "[@magesh]. Research on Indian legal text [@iltur, @ildc, @inlegal] provides valuable datasets and models but concentrates on classification and "
        "prediction rather than on supporting a practitioner's preparation. Court simulation [@agentcourt] and graph-based summarisation [@graphrag] "
        "demonstrate useful interfaces, but neither is tied to the user's own case file.")
    b.p("These findings support the objectives of this project: a document-grounded assistant for Indian case preparation that cites its sources, a method "
        "of selecting passages that uses the whole case file within a small budget, an evidence graph designed for legal reasoning, and a precedent library "
        "whose entries can be verified. The next chapter describes the requirements and the methodology proposed to achieve these objectives.")


# ═════════════════════════════════════════════════════════════════════════════
# Chapter 3
# ═════════════════════════════════════════════════════════════════════════════

def chapter3(b: Builder):
    b.chapter_divider(3, "Proposed Methodology")
    b.chapter_title(3, "Proposed Methodology")
    b.h1("3.1  Introduction")
    b.p("Court Vision AI is designed as a three-tier web application: a Next.js user interface [@nextjs], a FastAPI server [@fastapi] that implements the six "
        "features, and a data layer consisting of a PostgreSQL database and file storage. All six features rely on three shared backend services developed "
        "in this project: a **retrieval service**, which divides documents into page-tagged passages and ranks them; an **LLM service**, which "
        "communicates with the Groq AI service [@groq] and handles its limits and errors; and a **precedent service**, which builds and searches the "
        "precedent library.")
    b.p("The project followed an iterative approach in five phases: (1) study of the problem and survey of the literature; (2) requirement analysis and "
        "design; (3) step-by-step development of the application and its features; (4) quantitative evaluation against other approaches; and "
        "(5) improvement based on the evaluation, followed by documentation. This approach links every design decision to an objective in Section 1.3 "
        "and to a measured result in Chapter 4.")

    b.h1("3.2  Requirement Gathering")
    b.p("The requirements were derived from a study of existing systems, from the limitations reported in the literature (Chapter 2), and from a "
        "step-by-step analysis of how an advocate prepares a case: reading the record, extracting dates and parties, identifying witnesses and "
        "contradictions, researching precedents and rehearsing arguments.")
    b.h2("3.2.1  Requirement Gathering Approach")
    b.p("The following techniques were used to identify the requirements:")
    b.bullets([
        "**Study of existing systems:** free judgment portals, paid research databases and general-purpose chatbots were compared in terms of reliability, citation of sources, cost and support for Indian law.",
        "**Analysis of the literature:** each limitation reported in the reviewed papers was turned into a requirement, for example compulsory citations, refusal when the answer is absent, and tolerance of incomplete AI output.",
        "**Walk-through of the preparation process:** the preparation of a real Supreme Court judgment, *Jacob Mathew v. State of Punjab* [@jacob], was carried out step by step to identify the outputs an advocate needs at each stage.",
        "**Testing of prototypes:** each feature was tested on stored cases, and every failure observed — text cut short, template text, repeated entities and invented citations — was turned into a new requirement.",
    ])
    b.h2("3.2.2  Functional Requirements")
    b.p("Table 3.1 lists the functions that the system must perform.")
    b.table([["ID", "Functional requirement"],
             ["FR1", "Users can register, log in securely and see only their own cases."],
             ["FR2", "Users can create, edit, list and delete cases, recording the case name, type, number and their role (defence, prosecution, researcher or student)."],
             ["FR3", "Users can upload PDF documents of up to 50 MB. The system checks that each file is a genuine PDF, stores it and processes it in the background, showing its status (uploading, processing, ready or failed)."],
             ["FR4", "Case Intelligence: users can ask questions about a case and receive answers, displayed as they are generated, that refer to the source document; the system declines when the documents do not contain the answer."],
             ["FR5", "Case Snapshot: the system generates a structured summary of the case (overview, key issues, facts, dates, evidence, weaknesses and next steps)."],
             ["FR6", "Evidence Graph: the system shows the persons, organisations, dates, locations, facts and evidence in the case, without duplicates, and labels every relationship with its meaning."],
             ["FR7", "Virtual Courtroom: users can argue in four phases (opening statements, examination of evidence, legal arguments and closing arguments) before an AI judge whose temperament can be strict, inquisitive or balanced, against an AI opposing counsel, and can request a verdict with a performance scorecard."],
             ["FR8", "Trial Prep & Brief Generator: the system generates a date-wise chronology, a witness cross-examination question bank and a seven-section synopsis, each item referring to a page, together with related precedents."],
             ["FR9", "Every processed judgment is added to the precedent library, together with every earlier case cited in it and the citation printed in the judgment."],
             ["FR10", "Legal Precedents: users can search for precedents; results combine matches from the library, with the matching passage and page, and AI suggestions, each labelled as verified or unverified."],
             ["FR11", "No feature displays fixed template text in place of an AI result; any failure is reported to the user."],
             ["FR12", "Users can copy the trial-preparation brief as formatted text (Markdown) and print it."]],
            [0.7, 6], caption="Functional requirements", size=9.5)
    b.h2("3.2.3  Non-Functional Requirements")
    b.p("Table 3.2 lists the quality requirements of the system.")
    b.table([["Category", "Requirement"],
             ["Reliability of answers", "Answers must be supported by the uploaded documents and refer to their pages; questions that the documents cannot answer must be declined (target: no more than 10% invented answers)."],
             ["Performance", "Chat answers should begin to appear within a few seconds; the search for relevant passages should take less than 50 ms; a complete trial-preparation brief should be ready within about one to two minutes on the free AI service."],
             ["Cost", "Every request must fit the free-tier limit of 8,000 tokens per minute, covering both the text sent and the answer requested."],
             ["Robustness", "The system must switch to another AI model if one fails, wait and retry when the service is busy, repair small errors in AI output, and recover usable data from incomplete AI output."],
             ["Security", "Passwords are stored as bcrypt hashes, users are authenticated with JSON Web Tokens (JWT), uploaded files are validated, documents are served only to logged-in users, and secret keys are kept in environment variables."],
             ["Usability", "Each case has a single workspace (documents, chat, graph and snapshot); the source of every result is clearly labelled; the layout adapts to the screen size."],
             ["Portability and scalability", "The server keeps no session state, the database layer works with both SQLite and PostgreSQL, file storage can be moved to cloud storage, and the whole system is deployed with Docker Compose."],
             ["Maintainability", "Shared backend services replace repeated code, and data structures are type-checked on both the server (Pydantic) and the user interface (TypeScript)."]],
            [1.6, 5], caption="Non-functional requirements", size=9.5, bold_first_col=True)
    b.h2("3.2.4  User Requirements")
    b.p("Table 3.3 summarises the needs of the three main types of user.")
    b.table([["User", "Needs"],
             ["Law student or moot-court participant", "Understand a judgment quickly, see who did what and when, practise arguments and receive feedback, and learn which precedents matter."],
             ["Junior advocate", "A chronology and witness questions for the hearing, the contradictions in the record, precedents with verifiable citations, and a printable brief."],
             ["Legal researcher", "Search across all the judgments collected so far, see the exact passage and page, and distinguish verified precedents from AI suggestions."]],
            [1.8, 5], caption="User requirements", size=9.5, bold_first_col=True)

    b.h1("3.3  Proposed Algorithm")
    b.p("The proposed system addresses the research gaps identified in Section 2.3 through five algorithms. Together, they ensure that every AI result is "
        "drawn from the whole case file, refers to its source, and fails openly rather than silently.")
    b.h2("3.3.1  CV-RAG: Page-Tagged Passage Retrieval")
    b.p(f"Each processed PDF is read page by page using PyMuPDF [@pymupdf]. Repeated headers, footers, web addresses and page numbers are removed, and the "
        "text of each page is divided into passages of 1,000 characters, with an overlap of 200 characters between consecutive passages. Each passage is "
        "tagged with its document name and page number. For a request *q*, every passage *d* is scored with the Okapi BM25 ranking function [@bm25]:")
    b.p("score(q, d) = Σ IDF(t) · f(t, d) · (k₁ + 1) / [ f(t, d) + k₁ · (1 − b + b · |d| / avgdl) ],   summed over each term t in q,", align="center", size=11)
    b.p("IDF(t) = ln[ 1 + (N − n(t) + 0.5) / (n(t) + 0.5) ]", align="center", size=11)
    b.p("where f(t, d) is the number of times the term t occurs in the passage d, |d| is the length of the passage, avgdl is the average passage length, "
        "N is the number of passages and n(t) is the number of passages that contain t; the constants are k₁ = 1.5 and b = 0.75. The highest-scoring "
        "passages are put back in their original order and sent to the LLM in the form “[document, p. N] text”, together with two rules: cite the "
        "page for every fact, and reply “This information is not available in the uploaded documents” when the passages do not contain the answer. "
        "Figure 3.1 illustrates the complete process.")
    b.figure(EFIG / "fig_cvrag.png", "CV-RAG passage retrieval and grounding process", width=6.3)
    b.h2("3.3.2  Building the Precedent Library")
    b.p("When a judgment has been processed, it is added to the precedent library, and every earlier case that it cites is added as well. The steps are "
        "shown below.")
    b.code("""
Algorithm IndexDocument(doc)
 1  pages <- cleaned text of each page of doc
 2  h <- SHA-256 fingerprint of the normalised full text
 3  if the library already holds a judgment with fingerprint h: stop      (stored only once)
 4  details <- AI reads the first 6,000 and last 4,000 characters and returns:
               title, citation, court, date, bench, ratio decidendi,
               key principles, statutes, keywords, outcome
 5  if the AI fails: read the title, citation and court directly from the text
 6  store the judgment with its details and its page-wise text
 7  ExtractCitedCases(judgment)

Algorithm ExtractCitedCases(j)
 1  find every reported citation in j (SCC, SCR, AIR, All ER, WLR, AC, Bom LR, ...)
    and keep 260 characters of text on each side of it, with its page number
 2  give the passages to the AI in groups of 12; it returns the case name,
    the citation and the point for which the case was cited
 3  accept a case only if its citation matches the printed citation of that passage
    and a word of the case name appears in that passage          (prevents mismatches)
 4  identify the court from the law report (e.g. SCC, SCR -> Supreme Court of India;
    AIR PC -> Privy Council)
 5  store the cited case, linked to judgment j                    (no duplicates)
""")
    b.h2("3.3.3  Evidence Graph Extraction and Duplicate Removal")
    b.p("The AI receives the opening and closing pages of the case file together with the passages that the retrieval service ranks highest for parties, "
        "witnesses, evidence, dates and findings (up to 10,000 characters in total). It must return each real-world entity once, with all the other names "
        "by which the record refers to it, a one-line description of its role with a page reference, and, for every relationship, a short phrase stating "
        "its legal significance. A duplicate-removal step then:")
    b.numbered([
        "normalises every name by converting it to lower case and removing punctuation and titles such as Dr., Shri, Smt., Late and Hon'ble;",
        "merges two entities when any of their names match or, for persons, when one name of two or more words is contained in the other;",
        "redirects the relationships of a merged entity to the remaining entity and removes self-links, repeated links and links to unknown entities; and",
        "keeps the 28 most connected entities and stores the graph, which is cleared automatically whenever the documents of the case change.",
    ])
    b.h2("3.3.4  Three-Step Trial-Preparation Brief")
    b.p("A single large request for the complete brief exceeded the AI's output limit and previously caused the feature to show template text. The brief "
        "is therefore produced in three focused steps, each of which receives the parts of the whole case file that are relevant to it:")
    b.numbered([
        "**Chronology:** passages that contain dates, giving preference to those with the most dates.",
        "**Cross-examination question bank:** passages about witnesses, statements, reports and exhibits.",
        "**Synopsis:** the opening and closing parts of the record, together with passages about the issues, the arguments and the findings.",
    ])
    b.p("The case description entered by the user is presented to the AI as a note that the record overrides. Section numbers must be kept exactly as they "
        "appear in the record, and the equivalent section under the new criminal laws (for example, Section 304A IPC and Section 106 BNS) is added only "
        "when it is certain. Related precedents are attached from the precedent library, and any step that fails is reported to the user.")
    b.h2("3.3.5  Reliable Reading of AI Output")
    b.p("Several features ask the AI to reply in JSON, a structured text format. When the reply is too long, the AI service cuts it off, and an "
        "incomplete JSON reply cannot be read by standard methods. The following algorithm recovers every complete item from such a reply:")
    b.code("""
Algorithm ReadAIOutput(text)
 1  remove reasoning blocks and code fences; repair doubled colons and trailing commas
 2  try to read the whole text as JSON; if that fails, try the part between the first '{' and the last '}'
 3  if the reply was cut off, recover every complete item at any level:
        keep a stack of the positions of '{' (ignoring characters inside quoted text)
        on each '}': take the text from the matching '{' and try to read it as JSON
 4  return the recovered items; the calling feature keeps those of the expected shape
    (graph entities and links, chronology entries, witnesses, precedents)
""")
    b.p("In addition, when the AI service rejects a reply because of a small formatting error, the rejected text is repaired and used instead of being "
        "discarded, so that the result of the strongest model is preserved.")

    b.h1("3.4  Gantt Chart for Timeline")
    b.p("The project spans Semesters VII and VIII of the academic year 2026-27. Figure 3.2 shows the Gantt chart, in which completed work is shown in green, "
        "work in progress in gold and work planned for Semester VIII in blue.")
    b.figure(FIG / "gantt.png", "Gantt chart for the project timeline", width=6.4)

    b.h1("3.5  Architectural Diagrams")
    b.h2("3.5.1  UML Diagrams")
    b.p("Three UML diagrams describe the system: a use case diagram (what the users can do), a sequence diagram (the order of the messages exchanged for "
        "one request) and a class diagram (how the data is stored).")
    b.figure(FIG / "uml_use_case.png", "UML use case diagram", width=5.6)
    b.p("**Explanation:** the main actor, the advocate or law student, can register and log in, manage cases, upload case files and use the six features. "
        "Two system actors support these use cases. The **Groq AI model** generates the answers, summaries, graphs, courtroom responses, briefs and "
        "precedent suggestions. The **background worker** processes every uploaded file and adds each judgment, with the cases it cites, to the precedent "
        "library, so that indexing never delays the user.")
    b.figure(FIG / "uml_sequence.png", "UML sequence diagram for generating a trial-preparation brief", width=6.4)
    b.p("**Explanation:** when the user opens the Trial Prep & Brief Generator and selects a case, the user interface sends one request to the server. The "
        "server first asks the retrieval service for the relevant passages of the whole case file. It then sends three separate requests to the AI model — "
        "one each for the chronology, the cross-examination question bank and the synopsis — and receives each part with its page references. Next, it "
        "searches the precedent library for related precedents. Finally, it returns the complete brief, together with an error note for any part that "
        "could not be generated, and the user interface displays it in three tabs.")
    b.figure(FIG / "uml_class.png", "UML class diagram of the data model", width=6.4)
    b.p("**Explanation:** a **User** owns many **Cases**, and a case can be shared with other users through **CaseMember**. Each case has many "
        "**Documents**, and each document has a **ProcessingJob** that records the progress of its background processing. Important actions are recorded "
        "in the **AuditLog**. Every processed judgment is stored once in the **Precedent** table, and each case cited in it is stored as a further "
        "Precedent linked back to the judgment that cites it (the *cites* relationship).")
    b.h2("3.5.2  Block Diagram")
    b.figure(FIG / "block_diagram.png", "Block diagram of Court Vision AI", width=6.4)
    b.p("**Explanation:** the system is organised in five layers, from top to bottom:")
    b.numbered([
        "**Presentation layer** — the Next.js web interface through which the user works with the Case Vault, the documents and the six features.",
        "**API layer** — the FastAPI server, which checks the user's login, validates every request and passes it to the right feature.",
        "**Features** — the six features of Court Vision AI (Case Intelligence and Case Snapshot are shown together because they share the same case documents).",
        "**Shared services** — the retrieval service (finds the relevant page-tagged passages), the LLM service (communicates with the Groq AI model) and the precedent service (builds and searches the precedent library).",
        "**Data layer** — the background worker that processes PDF files, the PostgreSQL database and the file storage.",
    ])
    b.p("Because all six features use the same shared services, improvements such as passage retrieval or the reliable reading of AI output benefit "
        "every feature at once.")
    b.h2("3.5.3  Data Flow Diagram")
    b.figure(FIG / "dfd_level0.png", "Data flow diagram, Level 0 (context diagram)", width=6.0)
    b.p("**Explanation of Level 0:** the context diagram treats the whole of Court Vision AI as a single process. The advocate or law student sends case "
        "details, PDF files, questions and arguments, and receives cited answers, the evidence graph, the trial-preparation brief, verdicts and precedents. "
        "The legal records (judgments and FIRs) enter the system as PDF files. The system sends grounded prompts — instructions together with the "
        "relevant passages — to the Groq AI model, which returns its replies as text or structured data.")
    b.figure(FIG / "dfd_level1.png", "Data flow diagram, Level 1", width=6.4)
    b.p("**Explanation of Level 1:** the single process of Level 0 is divided into six processes and three data stores:")
    b.table([["Process / store", "What it does"],
             ["1.0  Authenticate & manage case", "Logs the user in and creates or updates cases, which are kept in data store D1 (Cases / Users)."],
             ["2.0  Upload & validate PDF", "Checks that each uploaded file is a genuine PDF within the size limit and passes it on."],
             ["3.0  Extract text, chunk pages", "Saves the file in data store D2 (Documents + files) and converts it into page-tagged passages."],
             ["4.0  Index into precedent library", "Adds the judgment and every case it cites to data store D3 (Precedents)."],
             ["5.0  Grounded AI features", "Receives the relevant passages, sends grounded prompts to the Groq AI model and returns the answers, graph, brief and verdict to the user."],
             ["6.0  Precedent search", "Searches data store D3 and supplies related precedents to process 5.0."]],
            [2.2, 4.4], caption="Processes and data stores of the Level 1 data flow diagram", size=9.5, bold_first_col=True)
    b.h2("3.5.4  Timeline Chart")
    b.figure(FIG / "timeline.png", "Timeline chart of project milestones", width=6.4)
    b.p("**Explanation:** the timeline shows the main milestones in order. The milestones in green — from the identification of the research gap in "
        "August 2026 to the research paper, the IPR documents and this report in November 2026 — have been completed. The milestones in blue, namely the "
        "use of CV-RAG in the Case Intelligence feature and the final submission, are planned for Semester VIII.")

    b.h1("3.6  Hardware Requirements")
    b.p("Table 3.5 lists the hardware used for development and the minimum hardware recommended for deployment.")
    b.table([["Component", "Development (used)", "Minimum for deployment"],
             ["Processor", "AMD Ryzen 5 5625U, 6 cores / 12 threads", "2 virtual CPUs"],
             ["Memory", "8 GB RAM (7.3 GB usable)", "4 GB RAM (8 GB when the database and cache run on the same machine)"],
             ["Storage", "Solid-state drive; about 300 KB per 20-page judgment", "20 GB of disk space"],
             ["Graphics card (GPU)", "Not required; the AI model runs on the Groq cloud service", "Not required"],
             ["Network", "Broadband internet connection for the AI service", "Stable internet connection"],
             ["Client", "Any modern web browser", "Chrome, Edge or Firefox at a resolution of 1366 × 768 or higher"]],
            [1.3, 2.5, 2.5], caption="Hardware requirements", size=9.5, bold_first_col=True)

    b.h1("3.7  Software Requirements")
    b.p("Table 3.6 lists the software used in the project.")
    b.table([["Layer", "Software and version", "Purpose"],
             ["Operating system", "Windows 11 (development); Linux containers (deployment)", "Host platform"],
             ["Server", "Python 3.11, FastAPI 0.115, Uvicorn 0.32, SQLAlchemy 2.0, Pydantic 2.10", "Application programming interface (API), database access and validation"],
             ["Document processing", "PyMuPDF 1.25", "Reading text from PDF files"],
             ["Artificial intelligence", "Groq software development kit 0.13; models openai/gpt-oss-120b, qwen/qwen3.8-27b and openai/gpt-oss-20b", "Text generation, with automatic switching between models"],
             ["Passage ranking", "Okapi BM25, implemented in Python", "Selecting relevant passages and searching the precedent library"],
             ["Security", "python-jose (JWT) and passlib with bcrypt", "Authentication and password hashing"],
             ["Database", "PostgreSQL 16 (deployment) and SQLite (development)", "Permanent data storage"],
             ["User interface", "Next.js 16.3, React 19.2, TypeScript 5 and CSS Modules", "Web interface"],
             ["Deployment", "Docker and Docker Compose", "Packaging and running the system as containers"],
             ["Analysis and documentation", "NumPy, SciPy, Matplotlib, python-docx and Microsoft Word", "Evaluation, charts and this report"]],
            [1.4, 2.8, 2.2], caption="Software requirements", size=9.5, bold_first_col=True)

    b.h1("3.8  Cost Estimation")
    b.p("The cost of developing, testing and demonstrating the project is estimated in Table 3.7. The team members' own laptops are listed as existing "
        "resources, and free and open-source software is listed at ₹0.")
    b.table([["Sr. No.", "Item / Resource", "Description", "Estimated Cost (₹)"],
             ["1", "Hardware", "Team members' own laptops (existing resource; no purchase)", "0"],
             ["2", "Software / Tools", "Python, FastAPI, PostgreSQL, Next.js, Docker and Visual Studio Code (free and open-source)", "0"],
             ["3", "Cloud / Hosting", "The system runs locally with Docker Compose for development and demonstration", "0"],
             ["4", "APIs / Services", "Groq AI service, free tier (8,000 tokens per minute and 200,000 tokens per day per key)", "0"],
             ["5", "Other Expenses", "Printing and binding of the project report", "1,500"],
             ["", "**Total Estimated Cost**", "", "**₹1,500**"]],
            [0.7, 1.5, 3.3, 1.3], caption="Cost estimation", size=9.5)
    b.p("The project was designed to run on free services. Because CV-RAG sends about 60% less text to the AI than the original design, more requests fit "
        "within the free limit per minute. The only recurring costs that would arise in a production deployment are the use of the AI service beyond its "
        "free tier and, optionally, a cloud server; neither was needed for this project.")

    b.h1("3.9  Conclusion")
    b.p("This chapter presented the proposed methodology for Court Vision AI. The requirements were gathered from existing systems, from the literature and "
        "from an analysis of how an advocate prepares a case, and were expressed as twelve functional and eight non-functional requirements. The proposed "
        "system is based on five algorithms: page-tagged passage retrieval (CV-RAG), the automatic building of the precedent library, the extraction of "
        "the evidence graph with duplicate removal, the three-step trial-preparation brief, and the reliable reading of AI output. The UML, block and data "
        "flow diagrams describe a layered architecture with three shared backend services. All the requirements are met with open-source software and free "
        "service tiers at an estimated cost of ₹1,500, which provides a sound foundation for the implementation and evaluation described in Chapter 4.")


# ═════════════════════════════════════════════════════════════════════════════
# Chapter 4
# ═════════════════════════════════════════════════════════════════════════════

def chapter4(b: Builder):
    b.chapter_divider(4, "Implementation & Results")
    b.chapter_title(4, "Implementation & Results")
    b.h1("4.1  Introduction")
    b.p("This chapter describes how the methodology of Chapter 3 was turned into a working system and how the system was evaluated. The implementation "
        "covered the server and its programming interface, the six features, the precedent library and the user interface, all deployed with Docker "
        "Compose. The evaluation covered three aspects: (1) the accuracy of answers on a set of test questions with known answers, compared with three "
        "other approaches; (2) the reliability with which the system reads AI output; and (3) a functional test of every feature of the running system.")

    b.h1("4.2  Implementation")
    b.h2("4.2.1  Project Structure")
    b.p("The source code is organised as follows:")
    b.code("""
court-vision-ai/
|-- backend/app/
|   |-- main.py                  start-up, security settings, routes
|   |-- api/routes/              auth, cases, documents, chat, graph, courtroom,
|   |                            reports, research, health
|   |-- services/
|   |   |-- llm.py               LLM service
|   |   |-- retrieval.py         retrieval service (passages, BM25)
|   |   |-- precedent_service.py precedent service (library)
|   |   +-- case_service.py, document_service.py
|   |-- models/                  User, Case, Document, Precedent, AuditLog, ...
|   |-- core/                    configuration, database, security
|   +-- storage/local.py         file storage
|-- frontend/src/
|   |-- app/workspace/           pages of the six features
|   |-- components/              chat, graph, courtroom, document library, ...
|   +-- lib/                     typed connection to the server
|-- research_experiments/        evaluation programs, results and charts
+-- docker-compose.yml           user interface, server, PostgreSQL, Redis
""")
    b.h2("4.2.2  Server Interface")
    b.p("The server offers the interface listed in Table 4.1. Its documentation is generated automatically (Figure 4.1).")
    b.table([["Endpoint", "Method", "Purpose"],
             ["/api/auth/register, /api/auth/login, /api/auth/me", "POST, POST, GET", "Registration, login and current user"],
             ["/api/cases, /api/cases/{id}", "GET, POST, PATCH, DELETE", "Case Vault"],
             ["/api/cases/{id}/documents, /api/documents/{id}", "POST, GET, DELETE", "Upload, list, status and secure download of documents"],
             ["/api/cases/{id}/chat, /api/cases/{id}/chat/stream", "POST", "Case Intelligence, with answers displayed as they are generated"],
             ["/api/cases/{id}/summary", "GET", "Case Snapshot"],
             ["/api/cases/{id}/graph", "GET", "Evidence Graph (stored for each case)"],
             ["/api/cases/{id}/courtroom, /api/cases/{id}/courtroom/verdict", "POST", "Virtual Courtroom: one exchange, and the verdict with scorecard"],
             ["/api/cases/{id}/trial-brief", "GET", "Trial Prep & Brief Generator"],
             ["/api/research/query", "POST", "Legal Precedents search"],
             ["/api/research/library, /api/research/library/reindex", "GET, POST", "View or rebuild the precedent library"],
             ["/health", "GET", "Health check of the server and database"]],
            [2.9, 1.3, 2.4], caption="Server interface of Court Vision AI", size=9)
    b.figure(SCR / "api_docs.jpg", "Automatically generated documentation of the server interface", width=5.6)
    b.h2("4.2.3  Document Processing and the Precedent Library")
    b.p("When a file is uploaded, the server checks that its name ends in .pdf, that it is no larger than 50 MB and that its content begins with the PDF "
        "signature. The file is then saved, marked as processing and handed to a background task. The task opens the file with PyMuPDF, records the "
        "number of pages and marks the document as ready. It then clears the stored evidence graph of the case, because the case file has changed, and "
        "adds the judgment to the precedent library. When the server starts, any processed document that is not yet in the library is added "
        "automatically. The relevant part of the code is shown below.")
    b.code("""
# services/document_service.py  (background task, after the PDF is ready)
case.evidence_graph = None            # the stored graph is out of date once the case file changes
db.commit()
try:
    index_document(db, doc, store)    # the judgment and every case it cites -> precedent library
except Exception as e:
    db.rollback()
    logger.warning(f"Precedent indexing failed: {e}")
""")
    b.h2("4.2.4  LLM Service")
    b.p("All features communicate with the Groq AI service through the LLM service. It tries the preferred model first and then the alternative models, "
        "waits and retries when the service reports that it is busy, and reduces the requested answer length so that each request fits within the limit "
        "of 8,000 tokens per minute; a larger request would be rejected immediately. It also asks for structured (JSON) output and repairs or recovers "
        "faulty output, as described in Section 3.3.5. A simplified version of the code is shown below.")
    b.code("""
def chat(messages, max_tokens=2048, temperature=0.2):
    prompt_size = estimated_tokens(messages)
    if prompt_size + max_tokens > LIMIT - 200:         # stay within the free limit
        max_tokens = max(600, LIMIT - 200 - prompt_size)
    for model in [preferred_model] + alternative_models:
        for attempt in range(3):
            try:
                reply = groq.create(model, messages, max_tokens, temperature)
                return reply.text, model
            except ServiceBusy as e:                   # HTTP 429: wait, then retry
                time.sleep(e.retry_after)
            except JsonFormatError as e:               # repair the model's own output
                return e.rejected_text, model
            except Exception:
                break                                  # try the next model
    raise LLMError("All AI models failed")
""")
    b.h2("4.2.5  Implementation of the Features")
    b.bullets([
        "**Case Intelligence:** a conversation about the case that remembers earlier questions. Answers are sent to the browser word by word as they are generated, and each answer shows the excerpt of the document it is based on.",
        "**Case Snapshot:** a structured summary displayed beside the conversation. If the summary cannot be generated, an error is shown; the fixed summary text previously built into the code has been removed.",
        "**Evidence Graph:** generated as described in Section 3.3.3 and displayed as an interactive diagram with two layouts, filters by entity type, highlighting of contradictions and a details panel.",
        "**Virtual Courtroom:** every argument from the user receives two separate responses, one from the judge (in the selected temperament) and one from the opposing counsel, both based on the case documents. The verdict includes the outcome, the reasoning, the key findings and a scorecard for legal reasoning, use of evidence and courtroom conduct, as assessed by the AI; no default scores are ever inserted.",
        "**Trial Prep & Brief Generator:** generated in three steps as described in Section 3.3.4 and displayed in three tabs, with options to copy and print the brief.",
        "**Legal Precedents:** searches the precedent library with BM25, giving extra weight to the summary details of each precedent, and shows the most relevant passage of each result. AI suggestions are checked against the library; suggestions for which the AI cannot give a reliable citation are withheld, and the user is informed.",
    ])
    b.h2("4.2.6  User Interface and Deployment")
    b.p("The user interface is a Next.js application with a sidebar (Overview, Case Vault, Evidence Graphs, Virtual Courtroom, Legal Precedents and Trial "
        "Prep & Reports) and a three-column case workspace showing the documents, the chat or graph, and the Case Snapshot. Every request to the server "
        "carries the user's login token. The system is deployed with Docker Compose as four containers: the user interface (port 3000), the server "
        "(port 8000), the PostgreSQL database and the Redis cache.")

    b.h1("4.3  Results of Implementation")
    b.p("This section presents the screens and outputs of the implemented system.")
    b.h2("4.3.1  Login")
    b.p("Figure 4.2 shows the sign-in page, through which users log in or create an account.")
    b.figure(SCR / "login.jpg", "Sign-in page of Court Vision AI", width=5.6)
    b.h2("4.3.2  Evidence Graph")
    b.p("Figure 4.3 shows the Evidence Graph generated for a maintenance case under Section 125 of the Code of Criminal Procedure uploaded by the team. "
        "The entities are arranged in five columns: courts and authorities, parties and witnesses, claims and material facts, evidence and documents, and "
        "the timeline. Contradictory claims are highlighted in red. Selecting an entity (Figure 4.4) dims the rest of the graph and labels each of its "
        "relationships; for example, the High Court order *sets the reduced amount* of maintenance.")
    b.figure(SCR / "evidence_graph_full.png", "Evidence Graph with entity columns and highlighted contradictions", width=6.3)
    b.figure(SCR / "evidence_graph_focus.png", "Evidence Graph with one entity selected and its relationships labelled", width=6.3)
    b.p("For the *Jacob Mathew* judgment, the improved Evidence Graph contained 17 distinct entities and 16 relationships, each entity with a description "
        "and page reference, for example “Dr. Jacob Mathew — treating doctor accused under Section 304A IPC (p. 1)”. The relationships carry legal "
        "meaning; for example, *terminal cancer stage* contradicts *empty oxygen cylinder* as the cause of death. No entity appeared more than once.")
    b.h2("4.3.3  Virtual Courtroom")
    b.p("Figures 4.5 to 4.7 show a Virtual Courtroom session on the same maintenance case. The court opens the session (Figure 4.5); when the user asks "
        "for a verdict, the opposing counsel points out that the affidavit of disclosure required by the Supreme Court's guidelines has not been filed "
        "(Figure 4.6); and the verdict dismisses the matter for this procedural deficiency, giving reasons drawn from the uploaded document (Figure 4.7).")
    b.figure(SCR / "courtroom_open.png", "Virtual Courtroom: the session is opened by the court", width=6.3)
    b.figure(SCR / "courtroom_exchange.png", "Virtual Courtroom: responses of the judge and the opposing counsel", width=6.3)
    b.figure(SCR / "courtroom_verdict.png", "Virtual Courtroom: verdict with judicial reasoning", width=6.3)
    b.h2("4.3.4  Trial Prep & Brief Generator")
    b.p("Figure 4.8 shows the chronology tab of the Trial Prep & Brief Generator for the maintenance case, with the source page of each event.")
    b.figure(SCR / "trial_brief.png", "Trial Prep & Brief Generator: date-wise chronology with source pages", width=6.3)
    b.p("For the *Jacob Mathew* judgment, the brief contained seven dated events, six witnesses with 19 cross-examination questions, a seven-section "
        "synopsis and five related precedents from the library, with every item referring to its page. Generating the brief took between 56 and 91 "
        "seconds on the free AI service. The chronology is reproduced in Table 4.2.")
    b.table([["Date", "Event (as generated)", "Source"],
             ["15.02.1995", "Late Jiwan Lal Sharma was admitted as a patient in a private ward of CMC Hospital, Ludhiana.", "p. 1"],
             ["22.02.1995", "At about 11 p.m. the patient had difficulty in breathing; the duty nurse called a doctor.", "p. 1"],
             ["22.02.1995", "An oxygen cylinder was connected but was found to be empty; arranging a replacement took a further 5–7 minutes.", "p. 1"],
             ["18.12.2002", "The High Court dismissed the petition seeking the quashing of the FIR and the subsequent proceedings.", "p. 2"],
             ["24.01.2003", "The application for recalling the High Court's order was dismissed.", "p. 2"],
             ["09.09.2004", "A two-judge Bench doubted the decision in Dr. Suresh Gupta's case and referred the matter to a larger Bench.", "p. 3"],
             ["05.08.2005", "The Supreme Court delivered its judgment.", "p. 1"]],
            [1.0, 4.6, 0.8], caption="Chronology generated for Jacob Mathew v. State of Punjab", size=9.5)
    b.h2("4.3.5  Precedent Library and Legal Precedents")
    b.p("Processing the *Jacob Mathew* judgment added the judgment itself and the 21 earlier cases cited in it to the precedent library, each with the "
        "citation printed in the judgment and the court identified from the law report. Including the other judgments uploaded by the team, the library "
        "contained 24 precedents at the time of writing. A sample is shown in Table 4.3.")
    b.table([["Cited case (as extracted)", "Citation", "Court"],
             ["Dr. Suresh Gupta v. Govt. of NCT of Delhi", "(2004) 6 SCC 422", "Supreme Court of India"],
             ["Syad Akbar v. State of Karnataka", "(1980) 1 SCC 30", "Supreme Court of India"],
             ["Kurban Hussein Mohamedalli Rangawalla v. State of Maharashtra", "(1965) 2 SCR 622", "Supreme Court of India"],
             ["Juggankhan v. State of Madhya Pradesh", "(1965) 1 SCR 14", "Supreme Court of India"],
             ["Dr. Laxman Balkrishna Joshi v. Dr. Trimbak Bapu Godbole", "(1969) 1 SCR 206", "Supreme Court of India"],
             ["Indian Medical Association v. V. P. Shantha", "(1995) 6 SCC 651", "Supreme Court of India"],
             ["Poonam Verma v. Ashwin Patel", "(1996) 4 SCC 332", "Supreme Court of India"],
             ["Achutrao Haribhau Khodwa v. State of Maharashtra", "(1996) 2 SCC 634", "Supreme Court of India"],
             ["Spring Meadows Hospital v. Harjol Ahluwalia", "(1998) 4 SCC 39", "Supreme Court of India"],
             ["State of Haryana v. Smt. Santra", "(2000) 5 SCC 182", "Supreme Court of India"],
             ["John Oni Akerele v. The King", "AIR 1943 PC 72", "Privy Council"],
             ["Emperor v. Omkar Rampratap", "4 Bom LR 679", "Bombay High Court"],
             ["Bolam v. Friern Hospital Management Committee", "[1957] 1 W.L.R. 582", "English courts"],
             ["Andrews v. Director of Public Prosecutions", "[1937] A.C. 576", "English courts"],
             ["Maynard v. West Midlands Regional Health Authority", "[1985] 1 All ER 635", "English courts"]],
            [3.4, 1.6, 1.6], caption="Sample of the cases added to the precedent library from one judgment", size=9)
    b.p("A search for *criminal liability of doctors for medical negligence under Section 304A* returned 11 precedents, all verified against the library: "
        "10 library matches, each with the matching passage and page, and one AI suggestion, which the system corrected to the actual case and citation "
        "held in the library (*Laxman Balkrishna Joshi v. Trimbak Bapu Godbole*, (1969) 1 SCR 206). Seven further AI suggestions, for which the AI could "
        "not give a reliable citation, were withheld, and the user was informed.")

    b.h1("4.4  Result Analysis")
    b.h2("4.4.1  Accuracy of Answers")
    b.p("To measure whether Court Vision AI answers only from the case file, the team prepared a set of 42 test questions from the full text of *Jacob "
        "Mathew v. State of Punjab* [@jacob], a 20-page Supreme Court judgment, before running any test. The questions are of two kinds:")
    b.bullets([
        "**Answerable questions (30):** the answer is written in the judgment, so the correct behaviour is to give that answer. These are divided into "
        "**group A** (16 questions), whose answers appear in the first 18,000 characters of the judgment — the only part that the original design of "
        "Court Vision AI sent to the AI — and **group B** (14 questions), whose answers appear only on later pages.",
        "**Unanswerable questions (12), group C:** the question is realistic, but the judgment does not contain the answer, for example the FIR number or "
        "the name of the duty nurse. The correct behaviour is to *decline*, that is, to reply that the information is not available in the uploaded "
        "documents. These questions were included deliberately, because a system that answers them must be inventing facts.",
    ])
    b.p("Table 4.4 gives one example from each group, with the expected behaviour.")
    b.table([["Group", "Example question", "Expected behaviour"],
             ["A — answerable from the beginning of the judgment", "On what date was Jiwan Lal Sharma admitted to the hospital?", "Answer “15.02.1995” (stated on page 1)."],
             ["B — answerable only from later pages", "Which English case laid down the test for medical negligence that the Court held applicable in India?", "Answer “Bolam v. Friern Hospital Management Committee” (stated on page 6)."],
             ["C — not answerable from the judgment", "On what exact date was the FIR lodged by Ashok Kumar Sharma?", "Decline: the judgment mentions the FIR but never states its date."]],
            [1.8, 2.6, 2.2], caption="Examples of the three groups of test questions", size=9.5)
    b.p("Every reply was then classified as follows:")
    b.bullets([
        "**Correct answer** — for an answerable question, the reply contains the key fact of the known answer (for example, the correct date or case name).",
        "**Correctly declined** — for an unanswerable question, the reply states that the information is not available, without inventing an answer.",
        "**Invented answer** — for an unanswerable question, the reply gives an answer anyway. For the FIR question above, the AI without documents replied "
        "that the FIR was lodged on “2 March 1995”, a date that does not appear anywhere in the judgment, whereas CV-RAG replied “This "
        "information is not available in the uploaded documents.”",
        "**Wrongly declined** — for an answerable question, the reply says the information is not available even though the judgment contains it.",
        "**Handled correctly** — the total of correct answers and correct declines, out of 42.",
    ])
    b.p("Four approaches were compared using the same AI model (openai/gpt-oss-120b): (1) the **original design**, which sends only the first 18,000 "
        "characters of the case file; (2) **CV-RAG**, the proposed method; (3) the **AI without documents**, which receives only the name of the case; and "
        "(4) **keyword search only**, which returns the best-matching passage of the judgment without using AI. Each reply was compared automatically with "
        "the known answer. The results are shown in Table 4.5.")
    rows = [["Measure", "CV-RAG (proposed)", "Original design", "AI without documents", "Keyword search only"]]
    for lab, f in [("Correct answers, answerable questions (of 30)", lambda d: d["k_answerable"]),
                   ("  of which in group A (of 16)", lambda d: d["k_A"]),
                   ("  of which in group B (of 14)", lambda d: d["k_B"]),
                   ("Correctly declined, group C (of 12)", lambda d: d["k_C"]),
                   ("Invented answers, group C (of 12)", lambda d: d["confusion"]["FP"]),
                   ("Questions handled correctly (of 42)", lambda d: f"{d['k_task']} ({pc(d['task_accuracy'][0])})"),
                   ("Average text sent to the AI (tokens)", lambda d: f"{d['prompt_tokens_mean']:,.0f}"),
                   ("Average response time (seconds)", lambda d: f"{d['latency_mean']:.2f}")]:
        rows.append([lab] + [str(f(S[s])) for s in (S2, S1, S3, S4)])
    rows[-1][-1] = "under 0.01"; rows[-2][-1] = "0"
    b.table(rows, [2.4, 1.1, 1.1, 1.2, 1.1], caption="Accuracy of answers on the 42 test questions", size=9.5)
    b.figure(FIG / "fig_accuracy_by_split.png", "Accuracy of each approach by question group", width=6.2)
    b.p(f"CV-RAG answered every answerable question correctly and declined every question that the judgment cannot answer. The original design answered "
        f"all the questions in group A but only {S[S1]['k_B']} of the 14 questions in group B, usually by stating, correctly from its point of view, that the "
        "information was not in the text it had received. These replies count as *wrongly declined*: the judgment does contain the answers, but on pages "
        "that the original design never sent to the AI. The AI without documents answered only "
        f"{S[S3]['k_answerable']} of the 30 answerable questions correctly and invented answers to {S[S3]['confusion']['FP']} of the 12 unanswerable ones. "
        f"The keyword search found a relevant passage for {S[S4]['k_answerable']} questions, but it can never decline, so it returned a passage for all 12 "
        "unanswerable questions. Figure 4.10 shows these outcomes as confusion matrices, in which the system's decision to answer or to decline is compared "
        "with whether the judgment contains the answer.")
    b.figure(FIG / "fig_confusion_matrices.png", "Confusion matrices of the decision to answer or to decline", width=6.4)
    b.figure(FIG / "fig_outcomes.png", "Outcome of the 42 questions for each approach", width=5.4)
    b.p("The statistical significance of the differences was tested with McNemar's test [@mcnemar], which compares two approaches on the same questions, "
        "and with the Wilcoxon signed-rank test for response times. The results are given in Table 4.6.")
    b.table([["Comparison", "Test", "Result"],
             ["CV-RAG and the original design", "McNemar's test", f"{MC[(S2, S1)]['a_only']} questions better, {MC[(S2, S1)]['b_only']} worse; {pv(MC[(S2, S1)]['p_value'])}"],
             ["CV-RAG and the AI without documents", "McNemar's test", f"{MC[(S2, S3)]['a_only']} better, {MC[(S2, S3)]['b_only']} worse; {pv(MC[(S2, S3)]['p_value'])}"],
             ["CV-RAG and keyword search only", "McNemar's test", f"{MC[(S2, S4)]['a_only']} better, {MC[(S2, S4)]['b_only']} worse; {pv(MC[(S2, S4)]['p_value'])}"],
             ["Response time of CV-RAG and the original design", "Wilcoxon signed-rank test", f"{R['latency_wilcoxon_S2_vs_S1']['n']} pairs; {pv(R['latency_wilcoxon_S2_vs_S1']['p_value'])}"]],
            [2.6, 1.7, 2.3], caption="Statistical significance of the results (5% significance level)", size=9.5)
    b.p(f"All the differences are statistically significant. In addition, CV-RAG sent an average of {S[S2]['prompt_tokens_mean']:,.0f} tokens per question "
        f"to the AI, compared with {S[S1]['prompt_tokens_mean']:,.0f} for the original design ({pc(TOKEN_SAVING, 0)} less), and it responded faster "
        f"({S[S2]['latency_mean']:.2f} seconds compared with {S[S1]['latency_mean']:.2f} seconds, Figure 4.12). Of the 30 correct answers given by CV-RAG, "
        f"{R['citation_S2']['k']} referred to a page that actually contains the answer; the other three referred to a neighbouring or related page.")
    b.figure(FIG / "fig_latency.png", "Distribution of response times for the three approaches that use AI", width=4.6)
    b.h2("4.4.2  Reliability of Reading AI Output")
    b.p("To test how reliably the system reads AI output, three evidence graphs produced by the AI for stored cases were altered in 22 realistic ways, for "
        "example by adding formatting marks, explanatory text or reasoning notes, or by cutting the reply off at points between 30% and 95% of its length. "
        "Each of the resulting 66 replies was read by the four methods previously used in the code and by the proposed method (Section 3.3.5). Table 4.7 "
        "and Figure 4.13 show the results.")
    jr = [["Reading method", "Replies read (of 66)", "Cut-off replies read", "Entities recovered from cut-off replies"]]
    for p, lab in [("P0_Naive", "Standard JSON reading"), ("P1_FenceStrip", "Removal of formatting marks (Case Snapshot)"),
                   ("P2_SafeJSON", "Bracket search (Trial Prep)"), ("P3_Robust", "Original partial recovery (Evidence Graph)"),
                   ("P4_NestedSalvage", "Proposed recovery method")]:
        x = J[p]
        jr.append([lab, str(x["k"]), pc(x["success_trunc"], 0), pc(x["node_recovery_trunc"], 0)])
    b.table(jr, [2.6, 1.2, 1.3, 1.9], caption="Reliability of reading AI output", size=9.5)
    b.figure(FIG / "fig_json_truncation.png", "Graph entities recovered from replies cut off at different points", width=5.4)
    b.p(f"None of the previous methods could read any of the 48 cut-off replies. The original recovery routine of the Evidence Graph looked only for items "
        "at the outermost level of the reply, which is never complete when the reply is cut off. The proposed method read all 66 replies and recovered "
        f"{pc(J['P4_NestedSalvage']['node_recovery_trunc'], 0)} of the graph entities from the cut-off replies; the difference is statistically "
        "significant (Cochran's Q test, p < 0.001). The same method is now used by the Trial Prep & Brief Generator, the Legal Precedents feature and the "
        "building of the precedent library.")
    b.h2("4.4.3  Functional Testing of the Features")
    b.p("Every feature of the running system was tested once on the stored *Jacob Mathew* case. A test passed only if the feature returned a genuine AI "
        "result of the expected form, and not the fixed template text that the original code returned on failure. The results are shown in Table 4.8.")
    b.table([["Function tested", "Server response", "Time (seconds)", "Result"]] +
            [[SMOKE_NAMES.get(r["module"], r["module"]), str(r["status"]), f"{r['latency_s']:.2f}", "Pass" if r["ok"] else "Fail (template text returned)"] for r in SMOKE],
            [2.6, 1.1, 1.1, 1.8], caption="Functional test of the running system (before the redesign of the trial-preparation brief)", size=9.5)
    b.p("The test showed that the Trial Prep & Brief Generator responded successfully but returned its built-in template: the AI had reached its output "
        "limit of 1,800 tokens in the middle of its reply, the reply could not be read, and the feature silently displayed the template. After the "
        "three-step redesign described in Section 3.3.4, the brief was generated successfully from the case record with every item referring to its page, "
        "and all fixed template text was removed from the code.")

    b.h1("4.5  Limitations")
    b.p("The current system has the following limitations:")
    b.bullets([
        "The accuracy evaluation used one judgment and 42 questions, with one answer per question, so the results need to be confirmed on a larger collection of documents.",
        "Answers were checked automatically against patterns of the correct answer; such a check may accept an answer that also contains unsupported extra details, so doubtful answers were also checked by hand.",
        "BM25 matches words, so a question worded very differently from the judgment may retrieve less relevant passages.",
        "The Case Intelligence feature still sends the beginning of the case file rather than the passages selected by CV-RAG; CV-RAG is currently used by the Trial Prep & Brief Generator, the Evidence Graph and the Legal Precedents feature.",
        "AI-suggested precedents that are not in the library cannot be verified automatically and are therefore withheld; the library grows only as users upload judgments.",
        "Scanned PDF files without a text layer are not supported, and only English documents were tested.",
        "On the free AI service, a complete trial-preparation brief takes one to two minutes, and the daily limit of 200,000 tokens per key can be reached during heavy use.",
    ])

    b.h1("4.6  Observation / Remarks")
    b.p("The following observations were made during the implementation and testing of the system:")
    b.bullets([
        f"**Grounding in the documents is decisive.** The same AI model handled {pc(S[S3]['task_accuracy'][0], 0)} of the questions correctly without the documents and 100% with the passages selected by CV-RAG; the limiting factor was the information given to the model, not the model itself.",
        "**Cutting the text short fails silently.** The original design gave polite and plausible refusals to questions that it could have answered, and a user would not have recognised these as a limitation of the system.",
        "**Fixed fallback text is misleading.** Template text written for one case was displayed for other cases as if it were an analysis; replacing it with clear error messages made failures visible.",
        "**The record must take priority over user notes.** A test case whose description read “Murder at Colaba – 2024” caused the first version of the synopsis to mix this note with the facts of the judgment; labelling the description as a note that the record overrides solved the problem.",
        "**Free service limits influence the design.** The AI service counts both the text sent and the answer requested against its limit of 8,000 tokens per minute, so requests are now sized automatically; smaller, focused requests are also faster.",
        "**Judgments are a rich source of precedents.** A single Supreme Court judgment provided 21 cited cases with printed citations, so the library contained real, verifiable entries after the very first upload.",
        "**AI citation suggestions need verification.** Without a match in the library, the AI suggested cases that looked plausible but could not be verified, so verified and unverified results must be kept separate.",
    ])

    b.h1("4.7  Conclusion")
    b.p("Court Vision AI was implemented as a complete web application, packaged in containers, with six document-grounded features, a precedent library "
        "that grows automatically and three shared backend services. The evaluation showed that CV-RAG handled all 42 test questions correctly, answering "
        f"every answerable question and declining every unanswerable one ({pv(MC[(S2, S1)]['p_value'])} compared with the original design), while sending "
        f"{pc(TOKEN_SAVING, 0)} less text to the AI. It also showed that the proposed method of reading AI output removed a failure that affected every "
        "cut-off reply. The objectives set out in Section 1.3 were achieved. The main limitations are the evaluation on a single judgment and the pending use "
        "of CV-RAG in the Case Intelligence feature; both are addressed in the future scope in the next chapter.")


# ═════════════════════════════════════════════════════════════════════════════
# Chapter 5, references and appendix
# ═════════════════════════════════════════════════════════════════════════════

def chapter5(b: Builder):
    b.chapter_divider(5, "Conclusion")
    b.chapter_title(5, "Conclusion")
    b.h1("5.1  Conclusion")
    b.p("This project set out to give advocates and law students in India an AI assistant that they can trust when preparing a case. Court Vision AI "
        "achieves this by basing all six of its features — Case Intelligence, Case Snapshot, Evidence Graph, Virtual Courtroom, Trial Prep & Brief "
        "Generator and Legal Precedents — on the user's own case documents, by referring to the pages of those documents, and by declining to answer "
        "rather than inventing facts when the documents are silent.")
    b.p(f"The main finding is that the reliability of the answers depends more on giving the AI the right information than on the AI model itself. With "
        f"CV-RAG, the same model improved from {pc(S[S3]['task_accuracy'][0], 0)} of questions handled correctly without documents, and "
        f"{pc(S[S1]['task_accuracy'][0], 0)} with only the beginning of the file, to {pc(S[S2]['task_accuracy'][0], 0)}, while sending "
        f"{pc(TOKEN_SAVING, 0)} less text, which makes the use of a free AI service practical. Further improvements identified through testing — a "
        "reliable method of reading AI output, a three-step trial-preparation brief, automatic removal of duplicate entities and the removal of all "
        "fixed template text — turned silent failures into correct results or clear error messages. Finally, the precedent library turns every "
        "uploaded judgment into a verifiable research resource by also storing the cases that it cites.")
    b.h1("5.2  Future Scope")
    b.p("The project can be extended in the following directions:")
    b.bullets([
        "Use CV-RAG in the Case Intelligence and Virtual Courtroom features, and combine keyword search with meaning-based search so that differently worded questions also find the right passages.",
        "Evaluate the system on a larger collection of Indian judgments, with answers checked by legal experts, and conduct a study with law students and junior advocates.",
        "Verify AI-suggested citations automatically against public judgment databases before displaying them.",
        "Support scanned FIRs and charge-sheets through optical character recognition, and add Hindi and regional languages.",
        "Track timelines and contradictions across several documents of the same case, for example between an FIR, a witness statement and a medical report.",
        "Allow several users to work together on a case, for use in law firms and law-school classrooms, and deploy the system on a cloud server.",
    ])
    b.h1("5.3  Published Paper")
    b.p("A research paper based on this project has been prepared in the IEEE conference format. Its details are given in Table 5.1.")
    b.table([["Item", "Details"],
             ["Title", "Court Vision AI: Retrieval-Grounded, Citation-Enforcing Generative AI for Indian Legal Case Preparation"],
             ["Authors", ", ".join(n for n, _, _ in TEAM) + ", and Dr. Asma Praveen; Department of Information Technology, VESIT, Mumbai"],
             ["Intended conferences", "IEEE INDICON, IEEE ICCCNT, or the Natural Legal Language Processing (NLLP) Workshop"],
             ["Status", "Paper and submission material prepared; to be submitted"],
             ["Link", "To be added after publication"]],
            [1.4, 5], caption="Details of the research paper", size=10, bold_first_col=True)


def references_and_appendix(b: Builder):
    b.unnumbered_title("References")
    b.references_placeholder()
    b.unnumbered_title("Appendix")
    b.h1("A.I  Publication Details")
    b.p("**Camera-ready or published paper:** the paper described in Section 5.3 is to be attached after this page once it has been submitted, together "
        "with the name of the conference, the submission number, the acceptance status and, if applicable, the presentation certificate.")
    b.p("**Plagiarism report:** the similarity report produced with the institute's licensed software is to be attached here. The target is an overall "
        "similarity of less than 10%, which corresponds to Level 0 of the UGC (Promotion of Academic Integrity and Prevention of Plagiarism in Higher "
        "Educational Institutions) Regulations, 2018.")
    b.h1("A.II  IPR: Copyright / Patent / Trademark")
    b.p("A search of Google Patents, WIPO PATENTSCOPE and the Indian Patent Advanced Search System (InPASS) found related but separate inventions, such as "
        "the verification and citation of AI outputs (US 12,353,469 B1), virtual mock trials (US 9,064,241) and the querying of legal knowledge graphs "
        "(WO 2021/164226 A1). Because Section 3(k) of the Patents Act, 1970 excludes computer programs as such from patent protection [@ipr], the "
        "protection recommended for the project is summarised in Table A.1.")
    cap = b.d.add_paragraph(style=b.tab_style)
    r = cap.add_run("Table A.1: Protection of intellectual property"); _font(r, "Times New Roman", 11, True)
    b.table([["Instrument", "Details", "Status"],
             ["Copyright (software)", "Form XIV under the Copyright Rules, 2013; literary work (computer software) titled “Court Vision AI”; fee ₹500", "Application drafted; to be filed"],
             ["Trademark", "Form TM-A; word mark COURT VISION AI and logo in Classes 9, 42 and 45; a search for similar marks is required, because the name “CourtVision” is used by an unrelated sports-analytics product", "Proposal drafted"],
             ["Patent", "Not recommended at this stage because of Section 3(k); may be reconsidered if a technical effect beyond the software is demonstrated", "Not applicable"]],
            [1.4, 3.8, 1.3], caption=None, size=9.5, bold_first_col=True)


def main():
    d = docx.Document(str(HERE / "template.docx"))
    front_matter(d)
    setup_chapter_section(d)
    b = Builder(d)
    chapter1(b); chapter2(b); chapter3(b); chapter4(b); chapter5(b); references_and_appendix(b)
    order = b.fill_references(REFS)
    unused = [k for k in REFS if k not in order[:len(order)]]
    d.core_properties.title = TITLE
    d.core_properties.author = ", ".join(n for n, _, _ in TEAM)
    out = HERE / "CourtVisionAI_Blackbook_draft.docx"
    d.save(str(out))
    from bb_lib import CITE_ORDER
    print("saved", out.name, "| cited", len(CITE_ORDER), "of", len(REFS), "| never cited:", [k for k in REFS if k not in CITE_ORDER])


if __name__ == "__main__":
    main()
