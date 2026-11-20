"""Experiments 1, 2, 3, 8 and 9 (content that does not depend on measured results)."""
from docgen import LabDoc

TITLE = "Court Vision AI: Document-Grounded, Hallucination-Resistant Generative AI for Indian Legal Case Preparation"
FIG = None  # set by build_docs

REFS = [
    'V. Magesh, F. Surani, M. Dahl, M. Suzgun, C. D. Manning, and D. E. Ho, "Hallucination-free? Assessing the reliability of leading AI legal research tools," J. Empirical Legal Stud., vol. 22, pp. 216–242, 2025, doi: 10.1111/jels.12413.',
    'M. Dahl, V. Magesh, M. Suzgun, and D. E. Ho, "Large legal fictions: Profiling legal hallucinations in large language models," J. Legal Anal., vol. 16, no. 1, p. 64, 2024. [Online]. Available: https://arxiv.org/abs/2401.01301',
    'A. Joshi, S. Paul, A. Sharma, P. Goyal, S. Ghosh, and A. Modi, "IL-TUR: Benchmark for Indian legal text understanding and reasoning," in Proc. 62nd Annu. Meeting Assoc. Comput. Linguistics (ACL), Bangkok, Thailand, 2024, pp. 11460–11499, doi: 10.18653/v1/2024.acl-long.618.',
    'V. Malik, R. Sanjay, S. K. Nigam, K. Ghosh, S. K. Guha, A. Bhattacharya, and A. Modi, "ILDC for CJPE: Indian legal documents corpus for court judgment prediction and explanation," in Proc. ACL-IJCNLP, 2021, pp. 4046–4062, doi: 10.18653/v1/2021.acl-long.313.',
    'S. Paul, A. Mandal, P. Goyal, and S. Ghosh, "Pre-trained language models for the legal domain: A case study on Indian law," in Proc. 19th Int. Conf. Artificial Intelligence and Law (ICAIL), Braga, Portugal, 2023, doi: 10.1145/3594536.3595165.',
    'N. Guha et al., "LegalBench: A collaboratively built benchmark for measuring legal reasoning in large language models," in Advances in Neural Information Processing Systems 36 (Datasets and Benchmarks Track), 2023. [Online]. Available: https://arxiv.org/abs/2308.11462',
    'G. Chen et al., "AgentCourt: Simulating court with adversarial evolvable lawyer agents," in Findings of the Assoc. Comput. Linguistics: ACL 2025. [Online]. Available: https://arxiv.org/abs/2408.08089',
    'D. Edge et al., "From local to global: A graph RAG approach to query-focused summarization," arXiv:2404.16130, 2024.',
    'P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in Advances in Neural Information Processing Systems 33, 2020, pp. 9459–9474.',
    'I. Chalkidis, A. Jana, D. Hartung, M. Bommarito, I. Androutsopoulos, D. M. Katz, and N. Aletras, "LexGLUE: A benchmark dataset for legal language understanding in English," in Proc. 60th Annu. Meeting ACL, 2022, pp. 4310–4330, doi: 10.18653/v1/2022.acl-long.297.',
    'Z. Ji et al., "Survey of hallucination in natural language generation," ACM Comput. Surv., vol. 55, no. 12, Art. 248, 2023, doi: 10.1145/3571730.',
    'S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," Found. Trends Inf. Retr., vol. 3, no. 4, pp. 333–389, 2009, doi: 10.1561/1500000019.',
    'Jacob Mathew v. State of Punjab & Anr., (2005) 6 SCC 1, Supreme Court of India, decided 5 Aug. 2005.',
    'Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," Psychometrika, vol. 12, no. 2, pp. 153–157, 1947, doi: 10.1007/BF02295996.',
]


def exp1(out):
    d = LabDoc(1, "Research Problem Identification and Gap Analysis")
    d.h("1. Aim:")
    d.p("To select an engineering problem, conduct a preliminary literature survey using IEEE Xplore, Scopus and Google Scholar, and identify a suitable research gap.")

    d.h("2. Select an Engineering Problem")
    d.p("**Selected problem:** Reliable, document-grounded generative AI assistance for legal case preparation in the Indian legal system.", align="justify")
    d.p("Junior advocates, law students and legal researchers in India must read long judgments, FIRs, charge-sheets and "
        "depositions to prepare for hearings. General-purpose large language models (LLMs) can summarise and answer "
        "questions, but they **hallucinate** facts, dates, parties and citations, which is unacceptable in a legal setting. "
        "Our project, **Court Vision AI**, is a full-stack system (FastAPI + Groq-hosted LLMs + Next.js) that lets a user upload "
        "case PDFs and then (i) chat with the case, (ii) obtain a structured case summary, (iii) view an LLM-extracted "
        "evidence knowledge graph, (iv) argue in a simulated Indian courtroom against an AI judge and opposing counsel, "
        "(v) generate a trial-preparation brief and (vi) research Indian precedents. The engineering problem is to make "
        "these outputs **grounded in the uploaded documents**, to make the system **refuse** when the documents do not "
        "contain the answer, and to make the LLM-to-structured-data pipeline **robust** to malformed model output.", align="justify")

    d.h("3. Preliminary Literature Survey")
    d.p("Recent papers (2020–2026) were collected from IEEE Xplore, Scopus-indexed venues (ACL Anthology, ACM DL, Wiley, "
        "Oxford Academic) and Google Scholar using the search strings: \"legal LLM hallucination\", \"retrieval-augmented "
        "generation legal\", \"Indian legal NLP benchmark\", \"court simulation LLM agents\" and \"knowledge graph RAG\".", align="justify")
    rows = [["Title of the paper", "Author(s) & Year", "Dataset", "Methodology", "Evaluation parameters", "Limitation / Problem Identified", "Research Gaps"],
            ["Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools", "Magesh, Surani, Dahl, Suzgun, Manning, Ho (2025)",
             "Pre-registered set of 200+ US legal research queries", "Expert manual evaluation of commercial RAG legal tools (Lexis+ AI, Westlaw AI) vs GPT-4",
             "Hallucination rate, correctness, groundedness", "RAG tools still hallucinate 17–33% of the time; US law only", "No study on Indian case files; effect of context truncation / refusal not isolated"],
            ["Large Legal Fictions: Profiling Legal Hallucinations in LLMs", "Dahl, Magesh, Suzgun, Ho (2024)",
             "Verifiable questions on US federal court cases", "Closed-book probing of ChatGPT 3.5, PaLM 2, Llama 2",
             "Hallucination rate by court, jurisdiction, time", "Hallucination 58–88%; models fail to correct false premises", "Only closed-book; does not test document-grounded assistants"],
            ["IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning", "Joshi, Paul, Sharma, Goyal, Ghosh, Modi (2024)",
             "8 Indian legal tasks; English + 9 Indian languages", "Benchmark suite with encoder and LLM baselines",
             "Task-specific F1 / accuracy", "Classification-style tasks; no interactive QA over user-uploaded case files", "No benchmark for grounded QA or refusal on Indian judgments"],
            ["ILDC for CJPE: Indian Legal Documents Corpus for Court Judgment Prediction and Explanation", "Malik et al. (2021)",
             "~35k Indian Supreme Court cases", "Transformer + hierarchical models for judgment prediction with explanations",
             "Accuracy, F1, explanation overlap with experts", "Prediction ≠ case preparation; explanations weakly match experts", "Practitioner-facing preparation tools not addressed"],
            ["Pre-trained Language Models for the Legal Domain: A Case Study on Indian Law (InLegalBERT)", "Paul, Mandal, Goyal, Ghosh (2023)",
             "Large corpus of Indian court judgments", "Continued pre-training of LegalBERT/CaseLawBERT on Indian text",
             "Macro-F1 on statute identification, segmentation, judgment prediction", "Encoder-only models; no generation, chat or citation", "Generative, citation-backed assistance for Indian law unexplored"],
            ["LegalBench: Measuring Legal Reasoning in LLMs", "Guha et al. (2023)",
             "162 tasks, 6 reasoning types (US law)", "Zero/few-shot evaluation of 20 LLMs",
             "Accuracy / balanced accuracy per task", "Short prompts; no long-document grounding; US law", "Long judgment grounding and context limits not measured"],
            ["AgentCourt: Simulating Court with Adversarial Evolvable Lawyer Agents", "Chen et al. (2024/2025)",
             "1,000 simulated adversarial cases", "Multi-agent LLM courtroom; adversarial self-evolution (AdvEvol)",
             "Legal task scores + professional lawyer panel", "Chinese legal setting; agents not grounded in the trainee's own case file", "No grounded, Indian-procedure courtroom trainer with performance feedback"],
            ["From Local to Global: A Graph RAG Approach to Query-Focused Summarization", "Edge et al. (2024)",
             "Podcast transcripts and news (~1M tokens)", "LLM-built entity graph + community summaries for RAG",
             "Comprehensiveness, diversity (LLM-as-judge)", "Generic domain; high indexing cost; assumes well-formed LLM JSON", "Legal evidence typing and robustness to truncated LLM output not studied"],
            ["Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", "Lewis et al. (2020)",
             "Natural Questions, TriviaQA, FEVER, etc.", "Dense retriever + seq2seq generator",
             "Exact match, accuracy", "Open-domain Wikipedia; no legal documents", "RAG for long Indian judgments under strict LLM token budgets not evaluated"]]
    d.table(rows, widths=[1.5, 1.15, 1.15, 1.35, 1.1, 1.35, 1.45], size=7.5)

    d.h2("4. Identify the Research Gap")
    d.p("Comparing the papers shows that (a) legal hallucination is well documented for **closed-book** LLMs and US commercial "
        "tools, (b) Indian legal NLP work focuses on **classification/prediction** benchmarks, and (c) court-simulation agents are "
        "**not grounded** in the trainee's own documents. None of the works measure what happens when a practical system on a "
        "free-tier LLM API must **truncate** a long Indian judgment to fit the token budget, whether it **refuses** unanswerable "
        "questions, or whether its LLM-to-JSON pipeline survives **truncated/malformed** model output.", align="justify")
    d.p("**Research Gap Statement:** \"Existing studies have addressed **legal hallucination in closed-book and commercial US "
        "legal AI tools, and classification benchmarks for Indian legal text**. However, **document-grounded question answering, "
        "calibrated refusal and robust structured extraction over long Indian judgments under strict LLM context/token limits** "
        "has not been adequately addressed. Therefore, there is a need to investigate **a retrieval-grounded, citation-enforcing "
        "architecture for an Indian legal case-preparation assistant and to evaluate it against truncated-context and closed-book "
        "baselines**.\"", align="justify")

    d.h("5. Final Research Problem Statement")
    d.p("General-purpose LLMs hallucinate case facts, and practical legal assistants that run on rate-limited LLM APIs can only send "
        "a fraction of a long Indian judgment to the model (Court Vision AI's production pipeline sends the first 18,000 characters, "
        "≈25% of a 20-page Supreme Court judgment). This research designs and evaluates **CV-RAG**, a page-tagged BM25 retrieval "
        "grounding layer with explicit citation and refusal rules for Court Vision AI, and a nested-object JSON salvage parser for "
        "its evidence-graph module. The goal is to measure, on a ground-truth question set built from *Jacob Mathew v. State of "
        "Punjab* (2005), whether retrieval grounding significantly improves answer accuracy and refusal behaviour over truncated and "
        "closed-book baselines without increasing cost or latency.", align="justify")

    d.h("6. References")
    for i, r in enumerate(REFS[:12], 1):
        d.p(f"[{i}] {r}", size=9.5, space_after=2)
    d.save(out)


def exp2(out, figdir):
    d = LabDoc(2, "Research Planning and Methodology Design")
    d.h("1. Aim")
    d.p("Formulate objectives, hypothesis, research methodology, workflow diagram, experimental plan, timeline, and expected contribution.")
    d.h("2. Research Topic")
    d.table([["Research Problem / Topic", TITLE],
             ["Research Gap Identified in Experiment 1",
              "Document-grounded QA, calibrated refusal and robust structured extraction over long Indian judgments under strict LLM "
              "context/token limits have not been evaluated. Court Vision AI's production pipeline truncates documents to 18,000 "
              "characters, so most of a long judgment is invisible to the model."]],
            widths=[1, 2.2], header=False, bold_first_col=True, size=10)
    d.h("3. Research Objectives")
    d.numbered([
        "To design and implement Court Vision AI, a full-stack legal case-preparation assistant (case vault, PDF ingestion, grounded chat, evidence graph, virtual courtroom, trial brief, precedent research).",
        "To build a ground-truth evaluation set (CV-LegalQA-42) from a real Supreme Court judgment, with answerable questions inside and beyond the production context window and deliberately unanswerable questions.",
        "To propose CV-RAG, a page-tagged BM25 retrieval grounding layer with citation and refusal rules, that works within an 8,000 tokens-per-minute free-tier LLM budget.",
        "To compare CV-RAG with the production truncated-context pipeline, a closed-book LLM and an extractive BM25 baseline on answer accuracy, refusal, hallucination, latency and token cost.",
        "To evaluate and improve the robustness of the evidence-graph JSON parser against malformed and truncated LLM output.",
        "To analyse results statistically (Wilson 95% CIs, McNemar's exact test, Cochran's Q, Wilcoxon signed-rank) and disseminate them through an IEEE paper, IPR filing and project showcase.",
    ])
    d.h("4. Hypothesis")
    d.table([["Null Hypothesis (H₀)",
              "H₀₁: Retrieval grounding (CV-RAG) yields no difference in task accuracy (correct answers on answerable questions + correct "
              "refusals on unanswerable ones) compared with the truncated production pipeline (CV-Trunc) or a closed-book LLM.\n"
              "H₀₂: The nested-object salvage parser recovers no more evidence-graph data from malformed LLM output than the existing parser."],
             ["Alternative Hypothesis (H₁)",
              "H₁₁: CV-RAG achieves significantly higher task accuracy than CV-Trunc and the closed-book LLM (McNemar's exact test, α = 0.05).\n"
              "H₁₂: The salvage parser achieves significantly higher parse success on corrupted/truncated output (Cochran's Q and McNemar, α = 0.05)."],
             ["Variables / Parameters to be considered",
              "Independent: context strategy (none / truncated 18k chars / BM25 top-6 chunks / extractive only); JSON parser variant.\n"
              "Dependent: answer accuracy, refusal rate, hallucination rate, decision precision/recall/F1, latency, prompt tokens, parse success, node/edge recovery.\n"
              "Controlled: LLM (openai/gpt-oss-120b on Groq), temperature 0.2, max_tokens 2048, identical legal system prompt, same document and question set."]],
            widths=[1, 2.6], header=False, bold_first_col=True, size=9.5)
    d.h("5. Research Methodology")
    d.table([["Research Approach / Method", "Experimental, quantitative comparative study (design-science: build the artefact, then evaluate it against baselines)."],
             ["Data / Dataset / Input", "Jacob Mathew v. State of Punjab & Anr., (2005) 6 SCC 1 — 20-page PDF, 72,720 characters; CV-LegalQA-42 ground-truth questions; 3 evidence graphs produced by the LLM for real cases in the Court Vision database."],
             ["Tools / Technologies", "Python 3.11, FastAPI, SQLAlchemy, PyMuPDF, Groq SDK (gpt-oss-120b), Next.js 16 / React 19 / TypeScript, SQLite, NumPy, SciPy, Matplotlib."],
             ["Proposed Method / Technique", "CV-RAG: page-aware text extraction → boilerplate removal → 1,000-character chunks (200 overlap) tagged with page numbers → Okapi BM25 (k1 = 1.5, b = 0.75) → top-6 excerpts in document order → legal grounding prompt with page-citation and abstain rules → gpt-oss-120b.\nP4 salvage parser: brace-stack scan that parses every complete JSON object at any depth and classifies nodes/edges."],
             ["Evaluation / Performance Measures", "Answer accuracy (A/B splits), correct-refusal rate, hallucination rate, task accuracy, confusion matrix (answer/abstain), precision, recall, F1, latency (s), prompt tokens; parse success and node/edge recovery for JSON."],
             ["Expected Methodology Steps", "1) Literature review and gap → 2) system design and implementation → 3) build ground truth → 4) implement baselines and proposed methods → 5) run experiments with rate-limit-aware harness → 6) automatic scoring with regex gold patterns → 7) statistical testing → 8) documentation, paper, IPR."]],
            widths=[1, 2.6], header=False, bold_first_col=True, size=9.5)
    d.h("6. Workflow Diagram")
    d.p("The proposed research workflow from problem definition to expected results is shown below.")
    d.fig(figdir / "fig_workflow.png", "Proposed Research Workflow", width=6.6)
    d.fig(figdir / "fig_architecture.png", "Court Vision AI system architecture", width=6.4)
    d.h("7. Experimental Plan")
    d.table([["Sr.", "Experimental Activity / Step", "Details / Expected Output"],
             ["1", "Ground-truth construction", "42 questions from the judgment: 16 answerable inside the 18k-char window (A), 14 answerable only beyond it (B), 12 unanswerable (C); regex gold patterns and page numbers."],
             ["2", "Baseline systems", "S1 CV-Trunc (production prompt + truncation), S3 closed-book LLM, S4 BM25 extractive; JSON parsers P0–P3 taken from the code base."],
             ["3", "Proposed systems", "S2 CV-RAG; P4 nested-object salvage parser."],
             ["4", "Run experiments", "4 systems × 42 questions with model pinned, T = 0.2, 429-aware retry; 5 parsers × 66 corrupted LLM outputs. Results logged to JSONL."],
             ["5", "Analysis and validation", "Accuracy with Wilson CIs, confusion matrices, McNemar/Cochran's Q/Wilcoxon tests, latency and token cost plots; accept/reject H₀."]],
            widths=[0.4, 1.6, 4.2], size=9.5)
    d.h("8. Timeline")
    d.table([["Activity", "Start Date", "End Date", "Status / Remarks"],
             ["Literature / Problem Finalization/Objectives", "03-08-2026", "14-08-2026", "Completed — gap identified (Exp. 1)"],
             ["Methodology Design", "15-08-2026", "28-08-2026", "Completed — objectives, hypotheses, workflow"],
             ["Implementation / Experiment", "29-08-2026", "10-10-2026", "Completed — Court Vision AI modules, CV-RAG, P4 parser"],
             ["Data Collection / Analysis", "11-10-2026", "19-10-2026", "Completed — QA and JSON robustness runs, statistics"],
             ["Result Evaluation", "19-10-2026", "26-10-2026", "In progress — paper drafting, peer review"],
             ["Final Documentation", "27-10-2026", "10-11-2026", "Planned — IPR filing, poster, submission"]],
            widths=[2.2, 1, 1, 2.2], size=9.5)
    d.h("9. Expected Contribution")
    d.bullets([
        "**A working artefact:** Court Vision AI, an Indian-law case-preparation assistant integrating grounded chat, evidence graphs, courtroom simulation, trial briefs and precedent research.",
        "**CV-LegalQA-42:** a reproducible ground-truth set that separately measures in-window recall, beyond-window recall and refusal on a real Supreme Court judgment.",
        "**CV-RAG:** evidence that page-tagged retrieval grounding beats truncated full-context prompting at lower token cost, enabling use on free-tier LLM quotas.",
        "**Robust structured extraction:** identification of a defect in the existing partial-JSON recovery and a salvage parser that recovers evidence graphs from truncated LLM output.",
        "**Quantified risk:** measured hallucination of a closed-book LLM on Indian case facts, supporting the need for grounded legal AI.",
    ])
    d.save(out)


def exp3(out):
    d = LabDoc(3, "Dataset / Experimental Setup Preparation")
    d.h("1. Aim")
    d.p("To identify the dataset or develop the experimental setup, define evaluation metrics, baseline methods, and success criteria.")
    d.h("2. Research Topic")
    d.table([["Research Problem / Topic", TITLE],
             ["Proposed Methodology from Experiment 2",
              "CV-RAG (page-tagged BM25 retrieval grounding with citation/abstain rules) compared with the production truncated-context "
              "pipeline, a closed-book LLM and an extractive BM25 baseline; P4 nested-object salvage parser compared with the parsers "
              "currently in the code base."]],
            widths=[1, 2.4], header=False, bold_first_col=True, size=10)
    d.h("3. Dataset Details")
    d.p("Two datasets were prepared. **Dataset 1 (CV-LegalQA-42)** is a ground-truth question set built manually from the full text of "
        "*Jacob Mathew v. State of Punjab & Anr.*, (2005) 6 SCC 1 — the judgment stored in the Court Vision case vault. "
        "**Dataset 2 (CV-GraphJSON-66)** consists of the three evidence graphs that the LLM actually generated for the three cases "
        "in the Court Vision database (9/10, 19/25 and 11/15 nodes/edges), each serialised and corrupted in 22 realistic ways.", align="justify")
    d.table([["Number of Records / Samples", "Dataset 1: 42 question–answer records (16 + 14 + 12).\nDataset 2: 3 graphs × 22 variants = 66 raw LLM outputs (330 parser runs)."],
             ["Features / Attributes", "Dataset 1: question id, question text, gold-answer regex patterns (all must match), source page, split.\nDataset 2: graph id, corruption variant, raw text, reference node/edge ids."],
             ["Classes / Categories", "A — answerable inside the 18,000-char production window (pages 1–5);\nB — answerable only beyond the window (pages 6–20);\nC — not answerable from the document (should be refused)."],
             ["Training / Testing Split", "No training is performed (zero-shot LLM evaluation). 100% of records are used as the test set; BM25 is unsupervised and indexes only the judgment text."],
             ["Data Format", "Source: PDF (20 pages, 72,720 extracted characters). Ground truth: Python module (qa_set.py). Results: JSONL / JSON."],
             ["Pre-processing Required", "PyMuPDF text extraction; removal of Indian Kanoon running headers, URLs and page numbers; whitespace normalisation; 1,000-char chunks with 200-char overlap tagged with page; lower-casing, alphanumeric tokenisation and stop-word removal for BM25."]],
            widths=[1, 2.6], header=False, bold_first_col=True, size=9.5)
    d.p("**Sample records from CV-LegalQA-42:**", space_after=2)
    d.table([["ID", "Question", "Gold pattern(s)", "Page"],
             ["A04", "For how long did no doctor turn up after the duty nurse was contacted?", "20 (to|-) 25", "1"],
             ["A14", "In Andrews v. DPP, which Law Lord said simple lack of care is not enough?", "atkin", "5"],
             ["B03", "From whom should the IO preferably obtain a medical opinion?", "government service", "19"],
             ["B06", "In Achutrao Haribhau Khodwa, what was left inside the patient's abdomen?", "\\bmop\\b", "15"],
             ["C09", "What was the FIR number registered at Police Station Division No. 3, Ludhiana?", "— (must refuse)", "—"],
             ["C12", "Which section of the Bharatiya Nyaya Sanhita, 2023 did the Court apply?", "— (anachronism; must refuse)", "—"]],
            widths=[0.45, 3.3, 1.6, 0.5], size=9)
    d.h("4. Experimental Setup Details")
    d.table([["Component", "Configuration"],
             ["Hardware", "AMD Ryzen 5 5625U (6 cores / 12 threads), 7.3 GB RAM, Windows 11 Home"],
             ["Runtime", "Python 3.11.5 (backend & experiments), Node.js 23.6.0 (frontend)"],
             ["Backend", "FastAPI 0.115.6, SQLAlchemy 2.0.36, SQLite, PyMuPDF 1.25.1, groq 0.13.0, pydantic 2.10"],
             ["Frontend", "Next.js 16.3.1, React 19.2.8, TypeScript 5, CSS Modules"],
             ["LLM", "openai/gpt-oss-120b on Groq Cloud, pinned (fallback chain disabled for fairness); temperature 0.2; max_tokens 2048"],
             ["API limits", "8,000 tokens/minute, 1,000 requests/day (free tier) — harness waits on HTTP 429 using the server's retry hint"],
             ["Production context (S1)", "chat.py logic: MAX_CONTEXT_CHARS = 18,000 → 18,004 chars of the 72,720-char judgment (24.8%)"],
             ["Retrieval (S2, S4)", "91 page-tagged chunks; Okapi BM25 k1 = 1.5, b = 0.75; top-k = 6 (S2) / top-1 (S4)"],
             ["Analysis", "NumPy, SciPy 1.x (binomtest, wilcoxon, chi2), Matplotlib; scripts in research_experiments/eval/"]],
            widths=[1.3, 4.2], size=9.5)
    d.h("5. Evaluation Metrics")
    d.p("The following metrics are computed for every system. For the answer/abstain decision, the positive class is \"answered\".")
    d.table([["Metric", "Definition / Formula", "Purpose"],
             ["Answer accuracy", "Correct answers ÷ answerable questions (A + B); reported separately for A and B", "Factual correctness when the answer exists"],
             ["Correct-refusal rate", "TN ÷ unanswerable questions (C)", "Ability to say \"not in the documents\""],
             ["Hallucination rate", "FP ÷ unanswerable questions (C)", "Fabrication of facts absent from the record"],
             ["Task accuracy", "(correct answers on A+B + correct refusals on C) ÷ 42", "Single overall score"],
             ["Precision / Recall / F1", "P = TP/(TP+FP), R = TP/(TP+FN), F1 = 2PR/(P+R)", "Quality of the answer-vs-abstain decision"],
             ["Error rate", "1 − task accuracy", "Template comparison measure"],
             ["Latency", "Wall-clock seconds per query (mean, median, p95)", "Execution time"],
             ["Prompt tokens", "usage.prompt_tokens reported by the API", "Cost / rate-limit pressure"],
             ["Parse success, node/edge recovery", "Parsed ≥1 valid node; recovered ÷ reference nodes/edges", "Robustness of LLM→JSON pipeline"],
             ["95% CI & significance", "Wilson score interval; McNemar exact test; Cochran's Q; Wilcoxon signed-rank (α = 0.05)", "Statistical validity"]],
            widths=[1.3, 2.6, 1.8], size=9)
    d.h("6. Baseline Methods")
    d.p("The proposed CV-RAG and P4 parser are compared with the following existing or standard methods.")
    d.table([["Sr.", "Baseline Method", "Brief Description", "Reason for Selection"],
             ["1", "CV-Trunc (production Court Vision)", "Real LEGAL_SYSTEM_PROMPT_TEMPLATE with the first 18,000 chars of the case documents", "Shows the effect of the current context-truncation design"],
             ["2", "Closed-book LLM", "Same model, told the case name, no documents", "Measures parametric knowledge and hallucination (as in Dahl et al.)"],
             ["3", "BM25 extractive", "Returns the single best BM25 chunk, no LLM", "Classical IR baseline; isolates the value of generation"],
             ["4", "Existing JSON parsers (P0–P3)", "json.loads; summary fence-strip; reports _safe_json; graph _extract_json", "Parsers currently used across Court Vision modules"]],
            widths=[0.4, 1.5, 2.4, 2], size=9.5)
    d.h("7. Success Criteria")
    d.table([["Sr.", "Success Criterion", "How will it be verified?"],
             ["1", "CV-RAG task accuracy is significantly higher than CV-Trunc and the closed-book LLM", "McNemar exact test on paired per-question outcomes, p < 0.05"],
             ["2", "CV-RAG answers ≥ 80% of answerable questions correctly, including beyond-window (B) questions", "Accuracy on A + B with Wilson 95% CI"],
             ["3", "Hallucination on unanswerable questions ≤ 10% for the grounded systems", "FP count on the 12 C questions; confusion matrix"],
             ["4", "CV-RAG uses fewer prompt tokens and is no slower than CV-Trunc", "Mean prompt tokens; Wilcoxon signed-rank on latency"],
             ["5", "Salvage parser recovers graphs from truncated output where existing parsers fail", "Parse success on 48 truncated inputs; Cochran's Q / McNemar"]],
            widths=[0.4, 2.8, 2.6], size=9.5)
    d.save(out)


PATENTS = [
    ["US 12,353,469 B1 (2025)", "Verification and citation for language model outputs", "Verifies LLM answers against a knowledge base and attaches citations; legal example with time-annotated court holdings.",
     "Generic verification post-processor; no case-file vault, Indian statute mapping, courtroom simulation or evidence graph."],
    ["US 9,064,241 B2 (2015)", "Systems, methods, and media for providing virtual mock trials", "Online mock trials and focus groups where participants act as jurors to test a case.",
     "Human jurors, no LLM judge/opposing counsel, no grounding in uploaded documents or advocacy scorecard."],
    ["US 2001/0053967 A1 (2001)", "Virtual summary jury trial and dispute resolution method and systems", "Virtual trial with a virtual judge for dispute resolution/jury research.",
     "Pre-LLM; rule/workflow based; aimed at dispute resolution, not lawyer training."],
    ["WO 2021/164226 A1 (2021)", "Legal case knowledge-graph query method", "Builds a legal knowledge graph from judgment documents (entities + relations) and answers keyword queries.",
     "Query/retrieval graph; no LLM extraction, evidence-type ontology (supports/contradicts) or recovery from malformed LLM JSON."],
    ["US 2025/0131289 A1 (2025)", "Knowledge Graph Extraction", "LLM-based entity/relationship and claim extraction for graph RAG.",
     "Domain-agnostic; no legal evidence typing, Indian-law context or courtroom integration."],
]


def exp8(out):
    d = LabDoc(8, "Patent / Copyright / Trademark Prior-Art Search", template_no=1)
    d.h("1. Aim:")
    d.p("To perform a novelty (prior-art) search using Google Patents, InPASS and WIPO PATENTSCOPE, and to evaluate patentability or identify opportunities for Copyright/Trademark registration for Court Vision AI.")
    d.h("2. Invention / Work Summary")
    d.p("**Court Vision AI** is a legal case-preparation platform. Its candidate inventive features are:", space_after=2)
    d.numbered([
        "Document-grounded legal QA with page-tagged retrieval (CV-RAG), mandatory page citations and an explicit refusal rule.",
        "Virtual Indian courtroom: two independently prompted LLM roles (Judge with selectable temperament — strict / inquisitive / balanced — and Opposing Counsel) grounded in the user's own case documents, ending in a verdict and a junior-advocate performance scorecard.",
        "LLM-extracted evidence knowledge graph with legal node types (person, organisation, date, location, fact, evidence) and edge types (supports, contradicts, testified_by, filed_by …), cached per case, with a regex fallback and nested-object salvage of truncated LLM JSON.",
        "Trial-preparation brief (chronology, witness cross-examination bank, 7-section synopsis) with dual IPC/BNS, CrPC/BNSS and IEA/BSA references.",
    ])
    d.h("3. Search Strategy")
    d.table([["Database", "Query / Classification used", "Records screened"],
             ["Google Patents", "(\"language model\" OR LLM) AND (legal OR court) AND (citation OR grounding); \"virtual courtroom\" OR \"mock trial\" AND (judge OR counsel); \"knowledge graph\" AND (judgment OR legal case)", "≈40 titles/abstracts; 5 closest retained (Table 2)"],
             ["WIPO PATENTSCOPE", "EN_TI/EN_AB: (legal OR judicial OR court) AND (\"knowledge graph\" OR \"large language model\" OR \"mock trial\"); IPC G06F 40/30, G06F 16/36, G06N 3/08, G06Q 50/18, G09B 19/00", "Same family members as Google Patents (WO 2021/164226)"],
             ["InPASS (Indian Patent Office)", "Title/abstract keywords: legal AND (\"artificial intelligence\" OR \"language model\"); court AND simulation; IPC G06Q 50/18", "Web-indexed search found no directly overlapping Indian publication — to be confirmed directly on the InPASS portal"],
             ["Non-patent literature", "IEEE Xplore, ACL Anthology, arXiv (see Exp. 1)", "AgentCourt (2024/25), GraphRAG (2024), commercial mock-trial tools"]],
            widths=[1.2, 3.5, 1.8], size=9, caption="Search strategy")
    d.h("4. Prior-Art Analysis")
    d.table([["Document", "Title", "Disclosure", "Difference from Court Vision AI"]] + PATENTS,
            widths=[1.15, 1.45, 2.05, 2.15], size=8.5, caption="Closest prior art")
    d.p("**Non-patent prior art:** AgentCourt (Chen et al., 2024/25) simulates courts with evolving LLM lawyer agents (Chinese law, not grounded in a "
        "trainee's documents); commercial tools (e.g. SimLab VR, inSession, MockTrialOnline) offer AI judges/opposing counsel for practice; "
        "GraphRAG (Edge et al., 2024) builds LLM entity graphs for summarisation. Each of these individually discloses one ingredient of "
        "Court Vision AI.", align="justify")
    d.h("5. Patentability Evaluation")
    d.table([["Criterion (Patents Act, 1970)", "Assessment"],
             ["Novelty — Sec. 2(1)(j)", "Partial. The specific combination (grounded courtroom simulation with temperament control + advocacy scorecard + evidence graph on the same Indian case file) was not found as a single disclosure. Individual elements are known."],
             ["Inventive step — Sec. 2(1)(ja)", "Weak-to-moderate. Combining known LLM prompting, BM25 retrieval and knowledge-graph extraction would likely be considered obvious to a person skilled in the art unless a technical effect (e.g. measured reduction of prompt tokens with higher accuracy under rate limits) is claimed."],
             ["Industrial applicability — Sec. 2(1)(ac)", "Yes — usable by law firms, law schools, legal-aid clinics and courts' training academies."],
             ["Exclusion — Sec. 3(k)", "\"A mathematical or business method or a computer programme per se or algorithms\" is not patentable. Court Vision AI is primarily software running on general-purpose hardware; a patent would need to demonstrate a technical effect/contribution (CRI Guidelines 2017)."],
             ["Conclusion", "A product patent is **not recommended** at this stage. The work is best protected by **copyright (software + documentation)** and a **trademark** for the product name/logo; a provisional patent application may be considered later for the retrieval-under-rate-limit technique if further technical effect is established."]],
            widths=[1.6, 4.4], size=9, bold_first_col=True)
    d.h("6. Copyright and Trademark Opportunities")
    d.bullets([
        "**Copyright (Copyright Act, 1957):** source code (≈4,400 lines Python, ≈6,650 lines TypeScript/TSX, ≈7,500 lines CSS) is a literary work; register as \"Computer Software\" via Form XIV at copyright.gov.in. The user manual, research paper and UI artwork can be registered separately.",
        "**Trademark (Trade Marks Act, 1999):** word mark \"COURT VISION AI\" and the scales logo in Class 9 (downloadable software), Class 42 (SaaS) and Class 45 (legal-research services). Note: \"CourtVision\" is already used by a sports-analytics product, so a phonetic search in Classes 9/42 on the IP India public search is essential; a composite mark (logo + words) is more registrable.",
    ])
    d.h("7. Conclusion")
    d.p("The prior-art search shows that verification/citation for LLM outputs, virtual mock trials and legal knowledge graphs exist separately in "
        "the patent literature. Court Vision AI's integration of these for Indian legal training is novel as a combination but faces "
        "Section 3(k) and obviousness hurdles. Hence the recommended IPR route is copyright registration of the software and a trademark "
        "application for the brand, carried out in Experiment 9.", align="justify")
    d.h("8. References")
    d.numbered(["Google Patents, https://patents.google.com (records listed in Table 2).",
                "WIPO PATENTSCOPE, https://patentscope.wipo.int.",
                "Indian Patent Advanced Search System (InPASS), https://iprsearch.ipindia.gov.in/PublicSearch.",
                "The Patents Act, 1970 (as amended), Sections 2(1)(j), 2(1)(ja), 2(1)(ac), 3(k); Guidelines for Examination of Computer Related Inventions (CRI), 2017.",
                "G. Chen et al., \"AgentCourt: Simulating court with adversarial evolvable lawyer agents,\" Findings of ACL 2025, arXiv:2408.08089."], size=9.5)
    d.save(out)


def exp9(out, figdir):
    d = LabDoc(9, "Preparation of IPR Document", template_no=1)
    d.h("1. Aim:")
    d.p("To draft an IPR document — (i) Copyright Registration document for the Court Vision AI software and (ii) a Trademark proposal for the product name/logo — based on the prior-art findings of Experiment 8.")
    d.h("2. Choice of IPR Instrument")
    d.p("Experiment 8 concluded that a patent is weak under Section 3(k) of the Patents Act, while the code base and brand are clearly protectable. "
        "Therefore the primary document prepared is a **Copyright Registration application for Computer Software (Form XIV, Copyright Rules, 2013)**, "
        "supported by a **Trademark proposal (Form TM-A)**.", align="justify")
    d.h("3. Copyright Registration — Statement of Particulars (Form XIV)")
    d.table([["Field", "Particulars"],
             ["1. Applicant name, address & nationality", "________________________ (group members / institute, as agreed), Indian"],
             ["2. Nature of applicant's interest", "Author(s) and owner(s) of the copyright"],
             ["3. Title of the work", "COURT VISION AI — AI-Powered Case Intelligence & Trial Preparation Platform"],
             ["4. Class / description of the work", "Literary work — Computer Software (source code, object code and user documentation)"],
             ["5. Language of the work", "Python 3.11, TypeScript/TSX, CSS, SQL; documentation in English"],
             ["6. Name, address & nationality of author(s)", "________________________ (all contributing students), Indian"],
             ["7. Whether the work is published", "Unpublished (no public release); private deployment for academic evaluation"],
             ["8. Year & country of first publication", "Not applicable (unpublished) — year of creation 2026, India"],
             ["9. Other persons with rights in the work", "None / Institute policy on student IP to be confirmed (attach NOC if required)"],
             ["10. Licences granted", "None"],
             ["11. Fee", "₹500 per work (Literary / Computer Software) — payable online at copyright.gov.in"],
             ["12. Documents enclosed", "Source code extract (first and last 10 pages), object-code/build description, statement of further particulars, NOC from co-authors, Power of Attorney (if filed through agent), ID proof"]],
            widths=[2, 4], size=9, bold_first_col=True, caption="Form XIV — Statement of Particulars (draft)")
    d.h2("3.1 Statement of Further Particulars (Computer Software)")
    d.table([["Item", "Details"],
             ["Purpose of the software", "Helps advocates, law students and researchers prepare cases: grounded chat over uploaded case PDFs, structured case summary, evidence knowledge graph, virtual courtroom with AI judge/opposing counsel and scorecard, trial-preparation brief and Indian precedent research."],
             ["Modules (backend)", "auth, cases, documents, chat (REST + SSE streaming), graph, courtroom, reports, research, health; services: case_service, document_service; storage abstraction; SQLAlchemy models (User, Case, CaseMember, Document, DocumentPage, DocumentProcessingJob, AuditLog)."],
             ["Modules (frontend)", "Landing, auth, workspace dashboard, case vault, case workspace (documents + chat + graph + snapshot), document viewer, courtroom, evidence-graph, reports, research pages; components CaseIntelligenceChat, EvidenceGraph, VirtualCourtroom, DocumentLibrary, DocumentUploadZone, Sidebar, AuthProvider."],
             ["Size of source code", "Backend: 38 Python files, ≈4,400 lines. Frontend: 23 TS/TSX files, ≈6,650 lines; 21 CSS-module files, ≈7,500 lines."],
             ["Third-party components", "FastAPI, SQLAlchemy, PyMuPDF, Groq SDK, Next.js, React (open-source licences — excluded from the claim; only original code is claimed)."],
             ["Platform", "Web application; Windows / Linux; Docker Compose deployment (PostgreSQL, Redis, backend, frontend)."]],
            widths=[1.6, 4.4], size=9, bold_first_col=True)
    d.h2("3.2 Filing Procedure")
    d.numbered([
        "Create an account on https://copyright.gov.in and choose \"Literary/Dramatic\" → \"Computer Software\".",
        "Fill Form XIV (Statement of Particulars and Statement of Further Particulars) with the details above.",
        "Upload the source-code extract as PDF, NOC(s) from co-authors and ID proofs; pay the ₹500 fee online.",
        "Diary number is generated; a 30-day mandatory waiting period allows objections.",
        "Examination; reply to any discrepancy letter within 30 days; on acceptance the Registration Certificate (Extract of the Register of Copyrights) is issued.",
    ])
    d.h("4. Trademark Proposal")
    d.table([["Field", "Proposal"],
             ["Mark", "COURT VISION AI (word mark) and composite logo (scales-of-justice icon + wordmark)"],
             ["Form / Act", "Form TM-A, Trade Marks Act, 1999 and Trade Marks Rules, 2017"],
             ["Classes (Nice)", "Class 9 — downloadable software for legal research and case analysis\nClass 42 — Software-as-a-Service; providing temporary use of AI software for document analysis\nClass 45 — Legal research services"],
             ["Applicant category", "Individual / Start-up / Small enterprise (fee ₹4,500 per class, e-filing) — otherwise ₹9,000 per class"],
             ["User claim", "\"Proposed to be used\""],
             ["Distinctiveness", "\"Court\" + \"Vision\" is suggestive (not descriptive) for legal software; adding the logo and \"AI\" increases distinctiveness."],
             ["Risk / search", "\"CourtVision\" is used by a sports-analytics product; conduct phonetic and device search on IP India public search in Classes 9/42 before filing. Fallback marks: NYAYADRISHTI, COURTVISION LEX."],
             ["Logo copyright", "If the logo is also registered as an artistic work, a search certificate from the Trade Marks Registry (Form TM-C) is required."]],
            widths=[1.5, 4.5], size=9, bold_first_col=True, caption="Trademark application proposal")
    d.fig(figdir / "fig_logo.png", "Proposed composite mark (logo concept)", width=3.6)
    d.h("5. Declaration (draft)")
    d.p("We hereby declare that COURT VISION AI is our original work, that the particulars given above are true to the best of our knowledge, and that "
        "no part of the claimed source code has been copied from any copyrighted work other than the open-source libraries acknowledged above, "
        "which are used under their respective licences.", align="justify")
    d.p("Place: Mumbai            Date: ____________            Signature(s) of applicant(s): ______________________")
    d.h("6. Conclusion")
    d.p("A complete draft of the copyright registration (Form XIV with statement of further particulars) and a trademark proposal (Form TM-A, Classes 9, 42 and 45) "
        "was prepared for Court Vision AI. Copyright protects the expression of the software immediately on creation, and registration provides prima facie "
        "evidence of authorship; the trademark protects the brand once a clearance search is done.", align="justify")
    d.save(out)
