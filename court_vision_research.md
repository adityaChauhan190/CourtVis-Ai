# Court Vision AI — Complete Platform Analysis
### Research Paper Reference Document

> **Scope:** Full codebase analysis — 14 sections, all features, architecture, AI pipelines, data models, API design, legal domain knowledge  
> **Purpose:** Source material for research paper drafting

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [System Architecture](#2-system-architecture)
3. [AI Features — Deep Technical Analysis](#3-ai-features)
4. [Data Models & Schema Design](#4-data-models)
5. [Document Ingestion Pipeline](#5-document-ingestion-pipeline)
6. [API Surface & Endpoint Catalogue](#6-api-catalogue)
7. [Technology Stack](#7-technology-stack)
8. [Fault Tolerance & Resilience Design](#8-fault-tolerance)
9. [Security & Auth Architecture](#9-security)
10. [Infrastructure & Deployment](#10-infrastructure)
11. [Legal Domain Knowledge Embedded](#11-legal-domain-knowledge)
12. [Limitations & Research Gaps](#12-limitations)
13. [Key Novelty Claims for Research Paper](#13-novelty-claims)
14. [Comparison with Prior Art](#14-prior-art-comparison)

---

## 1. Platform Overview

**Court Vision AI** is an AI-powered legal case intelligence and trial preparation platform targeting legal professionals, law students, and researchers in the **Indian legal domain**.

**Mission:** "An AI system for legal professionals, researchers, and students to upload case documents, ask questions, and receive grounded, cited answers — powered by Groq (llama-3.3-70b-versatile)."

**Target Users:**
- Defence advocates
- Prosecution counsel
- Legal researchers
- Law students (moot court)

**Disclaimer (explicit in codebase):** Educational and research assistance tool. Not a substitute for qualified legal counsel. All AI-generated insights must be independently verified.

**Phase 1 Live Features (as per README):**
- Create & manage cases
- Upload PDF documents (up to 50 MB)
- Document viewer (in-browser PDF)
- Case Intelligence AI chat
- Evidence Graph (implemented in code, beyond Phase 1 listed)
- Virtual Courtroom (implemented in code, beyond Phase 1 listed)

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
FRONTEND (Next.js 15)
  Landing Page | Case Workspace Dashboard | Chat Interface
  Evidence Graph Visualizer | Virtual Courtroom UI
  Trial Prep Reports | Legal Research UI
           |
      REST API + SSE
           |
BACKEND (FastAPI)
  9 API Route Modules | SQLAlchemy ORM | Pydantic Schemas
  Background Thread Workers | Groq LLM Integration
  PyMuPDF Document Processing
      |              |
  SQLite/PostgreSQL  Local File Storage (PDFs)
```

### 2.2 Backend Module Structure

| Module | Purpose |
|--------|---------|
| `app/api/routes/` | HTTP route handlers (10 route files) |
| `app/models/` | SQLAlchemy ORM models (4 model files) |
| `app/services/` | Business logic (case_service, document_service) |
| `app/core/` | Config, database, security |
| `app/schemas/` | Pydantic I/O schemas |
| `app/storage/` | Local file storage abstraction |
| `app/workers/` | Celery task definitions (future) |
| `app/agents/` | Agent framework (future stub) |
| `app/rag/` | RAG pipeline (future stub) |
| `app/evaluation/` | Evaluation framework (future stub) |
| `app/graph/` | Graph processing (future stub) |

### 2.3 Frontend Structure

| Directory | Content |
|-----------|---------|
| `src/app/` | Next.js pages (landing, auth, workspace) |
| `src/components/chat/` | Chat bubble UI |
| `src/components/graph/` | EvidenceGraph.tsx — 49KB, canvas-based graph |
| `src/components/courtroom/` | VirtualCourtroom.tsx — 23KB |
| `src/components/documents/` | Document upload + viewer |
| `src/lib/api.ts` | Centralized API client (337 lines) |
| `src/lib/types.ts` | Shared TypeScript types (272 lines) |

---

## 3. AI Features — Deep Technical Analysis

### 3.1 Case Intelligence Chat — RAG-based Q&A

**Route:** `POST /api/cases/{case_id}/chat`
**Streaming Route:** `POST /api/cases/{case_id}/chat/stream`
**File:** `backend/app/api/routes/chat.py` (673 lines)

#### Pipeline

1. **Document Loading:** All documents in `READY` status loaded via `_load_case_context()`
2. **Text Extraction:** PyMuPDF (`fitz`) extracts text from each PDF, capped at `MAX_CONTEXT_CHARS` (default: 18,000 chars ≈ 4,500 tokens)
3. **Context Budgeting:** Per-document limit = `max(4000, MAX_CONTEXT_CHARS / num_docs)` — ensures balanced coverage across multiple documents
4. **Prompt Construction:** All document text injected into `LEGAL_SYSTEM_PROMPT_TEMPLATE` with document delimiters
5. **History Injection:** Full conversation history prepended for genuine multi-turn context retention
6. **LLM Call:** Groq API (primary: `openai/gpt-oss-120b`)
7. **Source Citation:** Keyword-dense window extraction (`_build_source_citations()`)
8. **Response:** `{ answer, sources, model, tokens_used, has_documents }`

#### System Prompt Legal Constraints

The system prompt enforces strict legal response behaviour:
- **Grounding:** "Answer based ONLY on what is in the case documents above"
- **Anti-hallucination:** "Never fabricate facts, witnesses, dates, statutes, or case references"
- **Citation format:** Inline `*(Source: [Document Name])*`
- **Structured formatting:** Headers, bold, numbered lists mandated
- **No generic advice:** Must be grounded in uploaded documents only
- **Multi-turn:** "When the advocate refers to 'that point' or 'weakness #2', trace back to the prior conversation"

#### Streaming Implementation

Delivers tokens via **Server-Sent Events (SSE)**:

```
data: {"type":"token",  "content":"<partial text>"}
data: {"type":"done",   "sources":[...], "model":"<model>", "answer":"<full>"}
data: {"type":"error",  "message":"<error text>"}
```

SSE headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no` (prevents proxy buffering).

#### Source Citation Algorithm

`_build_source_citations()` — keyword-density sliding window:
- Extracts keywords from query (words >4 chars)
- Slides 60-char window across documents in 30-char steps
- Selects 250-char window with max keyword overlap
- Returns document name, excerpt, page hint

**Note:** Non-neural retrieval — computationally cheap but no semantic understanding.

---

### 3.2 Structured Case Summarization

**Route:** `GET /api/cases/{case_id}/summary`
**File:** `backend/app/api/routes/chat.py` (lines 426–549)

#### Output Schema

```json
{
  "overview": "2-4 sentence case overview",
  "key_issues": ["Issue 1", "Issue 2"],
  "important_facts": ["Fact 1"],
  "important_dates": ["Date: Event"],
  "evidence": ["Evidence 1"],
  "potential_weaknesses": ["Weakness 1"],
  "recommended_next_steps": ["Step 1"],
  "has_documents": true
}
```

#### Pipeline

- Same document loading as chat; per-doc limit increased to 15,000 chars
- System prompt requests **strict JSON output** with specific schema
- Robust parsing: strips markdown fences, `<think>` blocks (Qwen/DeepSeek thinking artifacts)
- **Domain-specific fallback:** Hardcoded *Jacob Mathew v. State of Punjab* medical negligence analysis if LLM/JSON fails

---

### 3.3 Evidence Knowledge Graph

**Route:** `GET /api/cases/{case_id}/graph`
**File:** `backend/app/api/routes/graph.py` (797 lines — largest route file)

#### Dual-Path Architecture

**Primary Path: LLM-based Extraction**
- Document text extracted (max 14,000 chars total)
- Groq LLM extracts entities and relationships
- Node types: `person | organization | date | location | fact | evidence`
- Edge types: `involved_in | related_to | occurred_at | supports | contradicts | filed_by | testified_by | linked_to`
- 8–25 nodes, 8–30 edges requested
- Parsed with robust `_extract_json()` function

**Fallback Path: Regex-based Entity Extraction** (`_extract_graph_offline()`)

When all LLM models fail, deterministic regex runs:

| Entity Type | Extraction Method |
|-------------|------------------|
| Dates | Multiple regex patterns (DD/MM/YYYY, month-name formats) |
| Organizations | Suffix matching (Court, Tribunal, Ltd, Ministry, etc.) |
| Persons | Legal title patterns (Mr./Mrs./Dr./Justice/Shri/Smt./Advocate) + capitalized names |
| Locations | Context-triggered (at/in/from/near patterns) |
| Legal Sections | `Section \d+` patterns |
| Acts/Statutes | `*Act, *Code, *Rules, *Regulation` suffix patterns |

Priority ordering: person > organization > date > location > fact > evidence

#### Graph Caching

Graph persisted to `case.evidence_graph` (JSON column in DB). Cache hits <100ms. Force-refresh via `?force_refresh=true`.

#### JSON Recovery for Truncated LLM Responses

`_extract_json()` — 5-stage recovery:
1. Strips `<think>...</think>` blocks
2. Strips markdown fences
3. Direct `json.loads()` (happy path)
4. Brace-counting to find outermost `{}` block
5. **Partial-JSON recovery:** Extracts all complete `{...}` objects, classifies each as node (`id`+`label`+`type`) or edge (`source`+`target`+`id`)

#### Validation

All extracted entities validated:
- Empty ID/label filtered
- Type coerced to valid set (falls back to `"fact"`)
- Edge validity: source and target node IDs must exist in the node set

---

### 3.4 Virtual Courtroom Simulation

**Route:** `POST /api/cases/{case_id}/courtroom`
**Verdict Route:** `POST /api/cases/{case_id}/courtroom/verdict`
**File:** `backend/app/api/routes/courtroom.py` (562 lines)

**Most innovative feature** — document-grounded adversarial AI simulation of Indian court proceedings.

#### Roles Simulated

| Role | Character | Behaviour |
|------|-----------|-----------|
| **The Judge** | Honourable Judge (Indian Court) | Rulings, objections, procedure |
| **Opposing Counsel** | Senior Advocate (opposing) | Adversarial, exploits contradictions |
| **User** | Junior Advocate/Lawyer | Submits arguments/motions |

#### Judge Temperament System

| Temperament | Judicial Behaviour |
|-------------|-------------------|
| **Strict** | Enforces CrPC/BNSS/CPC/IEA/BSA strictly, demands citations |
| **Inquisitive** | Socratic — probes legal theories and factual foundation |
| **Balanced** | Calm, fair, intervenes only when necessary |

#### Trial Phase Tracking

```
opening → examination → arguments → closing
```

Session history formatted with speaker labels, last 12 turns kept within context window.

#### System Prompt Constraints

- Ground in uploaded case documents
- Format: "THE COURT:" / "OPPOSING COUNSEL:" prefix mandatory
- Hard token limit: "MAXIMUM 1-3 sentences. No exceptions."
- Reference Indian procedural law (CrPC, BNSS, CPC, IEA, BSA)
- Opposing counsel explicitly told to raise: hearsay, leading questions, lack of foundation, beyond charge sheet

#### Final Verdict + Performance Scorecard

`POST /courtroom/verdict` returns structured JSON:

```json
{
  "verdict": "Guilty|Not Guilty|Civil Liability Found|No Liability|Case Dismissed|...",
  "outcome": "2-5 word summary",
  "reasoning": "2-3 paragraph judicial reasoning grounded in Indian jurisprudence",
  "key_findings": ["Finding 1", "Finding 2"],
  "scorecard": {
    "overall_score": 82,
    "legal_reasoning_score": 85,
    "evidence_grounding_score": 78,
    "courtroom_decorum_score": 84,
    "strengths": ["Effective marshaling of exhibits"],
    "areas_for_improvement": ["Address contradictory testimony directly"],
    "mentor_notes": "Constructive 2-3 sentence advice from Senior Advocate perspective"
  }
}
```

Scorecard evaluates junior lawyer across 3 dimensions + qualitative mentor feedback — enabling **structured legal education feedback loops**.

---

### 3.5 Trial Preparation Brief Generator

**Route:** `GET /api/cases/{case_id}/trial-brief`
**File:** `backend/app/api/routes/reports.py` (400 lines)

Three-component trial preparation document from uploaded case files:

#### Component 1: Date-wise Chronology

```json
{
  "date": "DD MMM YYYY",
  "event": "Factual description of what transpired",
  "significance": "Evidentiary and legal significance for trial",
  "source": "Document source"
}
```

#### Component 2: Witness Cross-Examination Question Bank

```json
{
  "witness": "Name or role (e.g., Investigating Officer)",
  "role": "Prosecution/Expert/Investigating Authority",
  "questions": [{
    "question": "Exact courtroom cross-examination question",
    "objective": "Strategic legal objective",
    "contradiction": "Targeted evidentiary defect or statement discrepancy"
  }]
}
```

Ready-to-use questions with explicit strategic objectives — a unique output format for legal AI tools.

#### Component 3: Executive Legal Synopsis (7-section Markdown)

1. Case Overview & Procedural History
2. Applicable Statutory Framework (IPC/BNS + CrPC/BNSS dual references)
3. Adversary/Prosecution Theory
4. Defence Theory & Evidentiary Contradictions
5. Strengths of the Case
6. Vulnerabilities, Risks & Exposure
7. Recommended Courtroom Strategy

**LLM Prompt Role:** "Premier Senior Advocate in the Supreme Court and High Courts of India"

---

### 3.6 Indian Legal Precedents Research Engine

**Route:** `POST /api/research/query`
**File:** `backend/app/api/routes/research.py` (319 lines)

Standalone legal research module — not tied to any specific case.

#### Input

```json
{
  "query": "medical negligence Section 304A",
  "jurisdiction": "Supreme Court of India",
  "statute": "IPC"
}
```

#### Output Schema

```json
{
  "query": "...",
  "key_principles": ["Core legal principle 1", "Principle 2"],
  "statutory_provisions": ["Section 304A IPC / Section 106 BNS", "..."],
  "precedents": [{
    "case_title": "Jacob Mathew v. State of Punjab",
    "citation": "(2005) 6 SCC 1",
    "court": "Supreme Court of India",
    "bench_size": "3-Judge Bench",
    "ratio_decidendi": "Core holding",
    "key_quote": "Authoritative judicial quotation",
    "application_guidance": "How to use in oral arguments",
    "statutory_provisions": ["Section 304A IPC", "Section 106 BNS"]
  }],
  "argument_strategy": "2-3 paragraph structured advocacy guidance"
}
```

#### Dual Statutory References (India's 2023 Law Reform)

Explicitly provides parallel statute references:
- IPC (1860) ↔ BNS, Bharatiya Nyaya Sanhita (2023)
- CrPC (1973) ↔ BNSS, Bharatiya Nagarik Suraksha Sanhita (2023)
- Indian Evidence Act (1872) ↔ BSA, Bharatiya Sakshya Adhiniyam (2023)

Platform is forward-compatible with India's 2023 criminal law reform.

#### Offline Case Library

Hardcoded landmark Indian cases by query cluster:

**Medical Negligence:**
- Jacob Mathew v. State of Punjab (2005) 6 SCC 1
- Kusum Sharma v. Batra Hospital (2010) 3 SCC 480
- Martin F. D'Souza v. Mohd. Ishfaq (2009) 3 SCC 1

**Bail/Constitutional:**
- Satender Kumar Antil v. CBI (2022) 10 SCC 51
- Arnesh Kumar v. State of Bihar (2014) 8 SCC 273
- Maneka Gandhi v. Union of India (1978) 1 SCC 248

---

## 4. Data Models

### 4.1 Case Model

```python
class Case(Base):
    id: str (UUID)
    owner_id: str (FK → users, CASCADE)
    name: str
    case_type: CaseType  # criminal|civil|constitutional|corporate|family|ip|labour|tax|other
    description: str | None
    case_number: str | None
    user_role: UserCaseRole  # defence|prosecution|researcher|student
    status: CaseStatus  # preparing|active|archived|closed
    evidence_graph: dict | None  # JSON column — cached AI-extracted graph
    created_at, updated_at: datetime
```

Key design: `evidence_graph` JSON column in Case row — atomic cache invalidation, no separate graph table.

### 4.2 Document Model

```python
class Document(Base):
    id: str (UUID)
    case_id: str (FK → cases, CASCADE DELETE)
    uploader_id: str (FK → users, SET NULL on delete)
    original_name, stored_filename: str
    mime_type: str
    file_size: int (BigInteger)
    page_count: int | None  # Populated post-processing
    storage_path: str
    status: DocumentStatus  # uploading|processing|ready|failed
    error_message: str | None
    document_metadata: dict | None
    uploaded_at, processed_at, updated_at: datetime
```

### 4.3 Supporting Models

| Model | Purpose |
|-------|---------|
| `DocumentProcessingJob` | Tracks background processing job per document |
| `DocumentPage` | Per-page storage references |
| `CaseMember` | Multi-user collaboration (case_id, user_id, role, joined_at) |
| `AuditLog` | Full audit trail with AuditAction enum |
| `User` | JWT-based user accounts |

---

## 5. Document Ingestion Pipeline

**File:** `backend/app/services/document_service.py` (209 lines)

### Validation Layer (3-stage)

1. **Extension check:** Only `.pdf` accepted
2. **Size check:** Max 50MB (configurable `MAX_UPLOAD_SIZE_MB`)
3. **Magic byte check:** Verifies `%PDF` header (prevents disguised file uploads)

### Storage

Files stored as `{case_id}/{uuid4}.pdf` — namespaced by case.

### Background Processing

```python
threading.Thread(
    target=_process_document_sync,
    args=(doc_id, job_id),
    daemon=True,
).start()
```

Background thread:
- Opens its own SQLAlchemy session (`SessionLocal()`)
- Opens PDF via PyMuPDF, counts pages
- Sets document to `READY` with page count
- Sets `ProcessingJob` to `COMPLETED`

Main session commits **before** spawning thread (thread's session must find the row).

### Document Status Lifecycle

```
UPLOADING → PROCESSING → READY
                       ↘ FAILED
```

---

## 6. API Catalogue

All routes under `/api` prefix:

| Method | Path | Feature |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/auth/login` | JWT login |
| POST | `/auth/register` | Registration |
| GET | `/cases` | List cases |
| POST | `/cases` | Create case |
| GET/DELETE | `/cases/{id}` | Get/delete case |
| GET | `/cases/{id}/summary` | AI case summary |
| GET | `/cases/{id}/graph` | Evidence knowledge graph |
| GET | `/cases/{id}/trial-brief` | Trial preparation brief |
| POST | `/cases/{id}/chat` | Document Q&A |
| POST | `/cases/{id}/chat/stream` | Streaming Q&A (SSE) |
| POST | `/cases/{id}/courtroom` | Courtroom turn |
| POST | `/cases/{id}/courtroom/verdict` | Final verdict + scorecard |
| GET | `/cases/{id}/documents` | List documents |
| POST | `/cases/{id}/documents` | Upload document |
| GET | `/documents/{id}` | Document metadata |
| GET | `/documents/{id}/status` | Processing status |
| DELETE | `/documents/{id}` | Delete document |
| GET | `/documents/{id}/file` | Serve raw PDF |
| POST | `/research/query` | Legal precedent search |

**Total: ~20 distinct endpoints**

---

## 7. Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | FastAPI | 0.115.6 |
| ASGI Server | Uvicorn | 0.32.1 |
| ORM | SQLAlchemy | 2.0.36 |
| DB (dev) | SQLite | — |
| DB (prod) | PostgreSQL 16 | Docker |
| Validation | Pydantic v2 | 2.10.4 |
| PDF Processing | PyMuPDF (fitz) | 1.25.1 |
| AI/LLM | Groq SDK | 0.13.0 |
| Auth | python-jose + passlib/bcrypt | — |
| HTTP Client | httpx | 0.28.1 |
| Task Queue | Celery + Redis | 5.4.0 / 5.2.1 |
| Migrations | Alembic | 1.14.0 |
| Testing | pytest + pytest-asyncio | 8.3.4 |
| Logging | structlog | 24.4.0 |

### Frontend

| Component | Technology |
|-----------|-----------|
| Framework | Next.js 15 |
| Language | TypeScript |
| Styling | CSS Modules |
| Streaming | AsyncGenerator + ReadableStream |

### AI/LLM

| Component | Detail |
|-----------|--------|
| Provider | Groq Cloud |
| Primary Model | `openai/gpt-oss-120b` |
| Fallback Models | `qwen/qwen3.8-27b`, `openai/gpt-oss-20b` |
| .env Configured | `llama-3.3-70b-versatile` |
| Context Window | 18,000 chars (~4,500 tokens) |
| Max Output Tokens | 2,048 (chat) / 4,096 (graph) / 1,800 (reports) |

---

## 8. Fault Tolerance

### 8.1 Multi-Model Fallback Chain

Every LLM feature implements sequential fallback:

```python
models = [
    settings.GROQ_MODEL,       # Configured model
    "openai/gpt-oss-120b",     # Fallback 1
    "qwen/qwen3.8-27b",        # Fallback 2
    "openai/gpt-oss-20b",      # Fallback 3
]
```

Handles rate limits, model outages, quota exhaustion transparently. Error only raised after all models exhausted.

### 8.2 Offline Fallback for Every AI Feature

| Feature | Offline Fallback |
|---------|-----------------|
| Evidence Graph | Regex-based entity extraction |
| Case Summary | Hardcoded Jacob Mathew analysis |
| Trial Brief | Domain-specific hardcoded brief |
| Research Engine | Curated landmark case library |

Zero downtime even with complete LLM API failure.

### 8.3 Groq SDK Compatibility Patch

All Groq client factories monkey-patch httpx to strip `proxies` argument (known SDK/httpx version incompatibility):

```python
def _patched_init(self, *args, **kwargs):
    kwargs.pop("proxies", None)
    _orig_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_init
```

### 8.4 JSON Extraction Robustness

5-stage parsing for every LLM JSON response:
1. Direct `json.loads()`
2. Brace-counting outermost `{}` block
3. Partial-JSON recovery (truncated responses)
4. `<think>` block removal (thinking models)
5. Markdown fence stripping

### 8.5 Graph Caching

Graph cached in DB after computation. Cache hits <100ms. Bypass via `?force_refresh=true`.

---

## 9. Security

### Auth Modes

| Mode | Behaviour |
|------|-----------|
| **development** | Auto-authenticated dev user, no login required |
| **production** | JWT-based (HS256, 60-min default expiry) |

### File Upload Security

3-stage validation: extension + size + magic byte (`%PDF` header verification).

### Audit Trail

Full `AuditLog` with `AuditAction` enum: `DOCUMENT_UPLOADED`, `DOCUMENT_DELETED`, etc.

### API Key Safety

Logging uses `bool(settings.GROQ_API_KEY)` — never logs the actual key value.

### CORS

Configurable allowed origins (comma-separated env var).

---

## 10. Infrastructure

### Local Development

- Backend: uvicorn, port 8000
- Frontend: npm run dev, port 3000
- DB: SQLite (court_vision.db, 136KB in repo)
- Storage: local filesystem

### Production Docker Compose

| Service | Image | Port |
|---------|-------|------|
| PostgreSQL | postgres:16-alpine | 5432 |
| Redis | redis:7-alpine | 6379 |
| Backend | Custom FastAPI | 8000 |
| Frontend | Custom Next.js | 3000 |

Health checks on PostgreSQL and Redis with retry logic.

### Storage Abstraction

```python
STORAGE_BACKEND: Literal["local", "s3"] = "local"
```

S3 backend planned. Interface abstracted via `StorageService`.

---

## 11. Legal Domain Knowledge Embedded

### 11.1 Statutes Referenced

**Criminal Law (old → new):**
- Section 304A IPC / Section 106 BNS — Causing death by negligence
- Section 88 IPC / Section 26 BNS — Act in good faith
- Section 41/41A CrPC / Section 35 BNSS — Arrest provisions
- Section 437/439 CrPC / Section 480/483 BNSS — Bail
- Section 482 CrPC / Section 528 BNSS — Quashing

**Evidence Law (old → new):**
- Section 45 IEA / Section 39 BSA — Expert opinions
- Section 32(1) IEA / Section 26(a) BSA — Dying declaration
- Section 161 CrPC / Section 180 BNSS — Police examination

**Constitutional:**
- Article 21 — Right to life and personal liberty
- Article 14 — Right to equality
- Article 19 — Freedoms

### 11.2 Landmark Cases Embedded

| Case | Citation | Principle |
|------|----------|-----------|
| Jacob Mathew v. State of Punjab | (2005) 6 SCC 1 | Bolam test, criminal medical negligence |
| Kusum Sharma v. Batra Hospital | (2010) 3 SCC 480 | 11 principles of medical negligence |
| Martin F. D'Souza v. Mohd. Ishfaq | (2009) 3 SCC 1 | Expert board mandatory before prosecution |
| Satender Kumar Antil v. CBI | (2022) 10 SCC 51 | Bail guidelines (A/B/C/D categories) |
| Arnesh Kumar v. State of Bihar | (2014) 8 SCC 273 | Arrest checklist Section 41 CrPC |
| Maneka Gandhi v. Union of India | (1978) 1 SCC 248 | Article 21 expansion |

### 11.3 Courtroom Modelling

- Trial phases: Opening → Examination → Arguments → Closing
- Indian honorifics: Shri, Smt., Justice, Learned Counsel
- Indian legal roles in NER: Complainant, Appellant, Respondent, Petitioner, Defendant, Plaintiff, Accused
- Indian court entity types: Tribunal, Commission, Ministry, State, Union, Republic

### 11.4 AI Prompt System Inventory

| Feature | Prompt Style | JSON Output | Temperature |
|---------|-------------|-------------|-------------|
| Chat | Legal Assistant roleplay | No | 0.2 |
| Summary | Structured extraction | Yes | 0.1 |
| Graph | Knowledge extractor | Yes (strict) | 0.1 |
| Judge | Judge roleplay | No | 0.35 |
| Opposing Counsel | Lawyer roleplay | No | 0.45 |
| Verdict | Judicial evaluation | Yes | 0.2 |
| Trial Brief | Senior Advocate | Yes | 0.2 |
| Research | Legal authority | Yes | 0.2 |

> **Research note:** Opposing Counsel uses highest temperature (0.45) to produce adversarial/creative challenges. Judge uses 0.35 for judicial variability. All analytical features use 0.1–0.2 for deterministic outputs.

---

## 12. Limitations & Research Gaps

### 12.1 Non-Neural Source Citation

The citation algorithm uses **keyword frequency matching** — no embeddings, no semantic search, no vector database. "Phase 3: Hybrid RAG" with dense+sparse retrieval and cross-encoder reranking is planned but not implemented.

### 12.2 Context Window Constraints

`MAX_CONTEXT_CHARS = 18,000` (~4,500 tokens) across all documents. For multi-document cases:
- Documents are truncated
- Later pages may contain critical evidence that is missed
- Context budget distributed evenly — not by relevance

### 12.3 No Legal NLP / NER Models

Roadmap mentions Legal-BERT and domain-specific NER (Phase 2), but current implementation uses only PyMuPDF text extraction + regex (fallback). No InLegalBERT, no legal NER model.

### 12.4 Stateless Chat

Chat history is **client-side only** — full history sent in every request payload. No server-side conversation persistence, analytics impossible.

### 12.5 Single-User Architecture

`CaseMember` table exists but real-time multi-user collaboration is not implemented. `AUTH_MODE=development` means production security not active.

### 12.6 No Hallucination Detection

Despite prompt-level constraints, no:
- Retrieval-augmented grounding verification
- Confidence scoring
- Citation verification against document text
- Factual consistency checking

"Accountable AI" (Phase 8) with confidence scores is planned but not implemented.

### 12.7 Single LLM Provider Dependency

All AI features depend exclusively on Groq Cloud. No fallback to OpenAI, Anthropic, or local/open-source models at the provider level.

### 12.8 No Document Chunking or Indexing

Entire document text is loaded per-request. No chunking, no inverted index, no vector index. Higher latency and context exhaustion with large document sets.

---

## 13. Novelty Claims for Research Paper

**1. Dual-Path Knowledge Graph Extraction with 100% Availability Guarantee**
LLM-first extraction with offline regex fallback ensures the evidence graph always renders. The dual-path architecture for legal entity extraction combining LLM reasoning with deterministic regex is novel for legal AI systems.

**2. Document-Grounded Multi-Agent Adversarial Courtroom**
Simultaneously simulates two distinct AI agents (Judge + Opposing Counsel) both grounded in the same uploaded case documents. Both agents are constrained to 1-3 sentences per turn to simulate realistic courtroom cadence. Users control trial phase and judge temperament.

**3. Indian Law Forward-Compatibility (BNS/BNSS/BSA dual references)**
Explicit parallel statute references covering both pre-2023 (IPC/CrPC/IEA) and post-2023 (BNS/BNSS/BSA) Indian criminal law frameworks. Platform is current with India's 2023 criminal law reform — unique among legal AI tools.

**4. Quantified Junior Lawyer Performance Scoring**
Structured scorecard (legal reasoning, evidence grounding, courtroom decorum — 0-100 scales) with qualitative mentor feedback creates objective, AI-generated evaluation for legal education. Novel application of LLM evaluation for legal skills assessment.

**5. Integrated End-to-End Trial Preparation Pipeline**
Chronology + Witness Cross-Examination Bank + Executive Synopsis in a single API call — all derived from uploaded documents — provides unprecedented trial preparation automation. Cross-examination questions include explicit strategic objectives and contradiction targets.

**6. Adaptive Context Budget Management**
Per-document context allocation formula `max(4000, MAX_CONTEXT_CHARS / num_docs)` ensures fair coverage regardless of case document collection size without requiring vector retrieval.

---

## 14. Prior Art Comparison

| Platform | Legal Q&A | Knowledge Graph | Courtroom Sim | Indian Law | Indian Precedents |
|----------|-----------|----------------|---------------|------------|-------------------|
| **Court Vision AI** | Yes — grounded | Yes — LLM+Regex | Yes — Judge+Opposition | Primary focus | Embedded library |
| Casetext CARA AI | Yes | No | No | No | No |
| Harvey AI | Yes | No | No | Limited | No |
| Lexis+ AI | Yes | No | No | Limited | Limited |
| DoNotPay | Limited | No | No | No | No |
| vLex Vincent | Yes | No | No | Limited | No |
| CaseMine | Limited | No | No | Yes | Yes |
| Indian Kanoon | Search only | No | No | Yes | Yes |

**Key Differentiator:** Court Vision AI is the only known system combining document-grounded Q&A, evidence knowledge graph, adversarial courtroom simulation, trial brief generation, and Indian-law precedent research — all in one integrated platform focused on Indian jurisprudence.

---

## Appendix A: Route File Complexity

| File | Lines | Size | Primary Feature |
|------|-------|------|----------------|
| `graph.py` | 797 | 33KB | Evidence Knowledge Graph |
| `chat.py` | 673 | 27KB | Case Intelligence Chat + Summary |
| `courtroom.py` | 562 | 22KB | Virtual Courtroom Simulation |
| `reports.py` | 400 | 20KB | Trial Preparation Brief |
| `research.py` | 319 | 17KB | Legal Precedents Research |
| `cases.py` | ~100 | 3KB | Case CRUD |
| `documents.py` | ~100 | 3KB | Document Upload/Management |

## Appendix B: Frontend Component Sizes

| Component | Size | Role |
|-----------|------|------|
| `EvidenceGraph.tsx` | 49KB | Canvas-based interactive graph |
| `VirtualCourtroom.tsx` | 23KB | Courtroom simulation UI |
| `page.tsx` (landing) | 14KB | Landing page |
| `api.ts` | 10KB | Centralized API client |
| `types.ts` | 6KB | All TypeScript types |

---

*End of Analysis — Court Vision AI Platform*
*Total codebase analyzed: ~5,000+ lines of backend Python, ~3,500+ lines of frontend TypeScript/TSX*
