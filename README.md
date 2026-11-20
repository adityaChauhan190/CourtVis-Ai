# Court Vision AI

**AI-Powered Case Intelligence & Trial Preparation**

An AI system for legal professionals, researchers, and students to upload case documents, ask questions, and receive grounded, cited answers — powered by Groq (llama-3.3-70b-versatile).

---

## Quick Start

You need **two terminals** — one for the backend, one for the frontend.

### 1. Backend (FastAPI)

```bash
cd backend

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

API runs at → http://localhost:8000  
Swagger docs → http://localhost:8000/api/docs

### 2. Frontend (Next.js)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

App runs at → http://localhost:3000

---

## Features (Phase 1 — Live)

| Feature | Status |
|---|---|
| Create & manage cases | ✅ Live |
| Upload PDF documents (up to 50 MB) | ✅ Live |
| Document viewer (in-browser PDF) | ✅ Live |
| **Case Intelligence AI chat** | ✅ Live |
| Evidence Graph | 🔜 Phase 5 |
| Virtual Courtroom | 🔜 Phase 7 |

---

## Project Structure

```
court-vision-ai/
├── backend/          # FastAPI + SQLite + Groq
│   ├── app/
│   │   ├── api/routes/   # cases, documents, chat, health
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── services/     # Business logic
│   │   ├── storage/      # Local file storage
│   │   └── core/         # Config, DB, security
│   └── .env              # Environment variables (inc. GROQ_API_KEY)
├── frontend/         # Next.js 15 + CSS Modules
│   ├── src/app/      # Pages (landing, workspace, cases)
│   ├── src/components/   # Reusable components
│   └── src/lib/      # API client, TypeScript types
└── docker-compose.yml  # PostgreSQL (for production use)
```

---

## Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=sqlite:///./court_vision.db
AUTH_MODE=development
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Disclaimer

Court Vision AI is an **educational and research assistance tool**. It does not provide legal advice and should not replace qualified legal counsel. All AI-generated insights must be independently verified.
