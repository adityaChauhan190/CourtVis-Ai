"""
Court Vision AI — page-aware text extraction and BM25 retrieval (CV-RAG).

Splits PDFs into page-tagged chunks so prompts can carry the most relevant parts of
the WHOLE case record (with page numbers) instead of only its first few pages.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.storage.local import StorageService

CHUNK_CHARS = 1000
CHUNK_OVERLAP = 200

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = set("""a an the of to in on for and or is are was were be by with as at from that this which what who whom
whose when where how did does do it its into than then there their they he she his her under according should must
can could would per not no any all been has have had will shall may such also said""".split())
# Running headers/footers from Indian Kanoon, SCC Online and similar PDF exports
_BOILERPLATE = re.compile(r"^(Indian Kanoon - http\S+|https?://\S+|Page \d+( of \d+)?|\d{1,3})\s*$", re.I)


@dataclass
class Chunk:
    doc_id: str
    doc_name: str
    page: int
    text: str


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


def pdf_pages(path: str) -> list[str]:
    """Clean text of every page (header/footer lines removed)."""
    import fitz
    pages = []
    with fitz.open(path) as pdf:
        for page in pdf:
            lines = [ln for ln in page.get_text().splitlines() if not _BOILERPLATE.match(ln.strip())]
            pages.append(re.sub(r"[ \t]+", " ", "\n".join(lines)).strip())
    # Drop a running title line repeated on most pages (e.g. "X vs Y on 5 August, 2005")
    first_lines = Counter(p.splitlines()[0] for p in pages if p)
    for line, n in first_lines.items():
        if n >= max(3, len(pages) // 2):
            pages = [p[len(line):].lstrip() if p.startswith(line) else p for p in pages]
    return pages


def chunk_pages(doc_id: str, doc_name: str, pages: list[str]) -> list[Chunk]:
    chunks = []
    for pno, text in enumerate(pages, start=1):
        flat = re.sub(r"\s+", " ", text)
        start = 0
        while start < len(flat):
            chunks.append(Chunk(doc_id, doc_name, pno, flat[start:start + CHUNK_CHARS]))
            if start + CHUNK_CHARS >= len(flat):
                break
            start += CHUNK_CHARS - CHUNK_OVERLAP
    return chunks


class BM25:
    """Okapi BM25 (k1 = 1.5, b = 0.75)."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.avgdl = (sum(self.len) / len(docs)) if docs else 1
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: list[str]) -> list[float]:
        out = []
        for tf, dl in zip(self.tf, self.len):
            s = 0.0
            for t in query:
                f = tf.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out.append(s)
        return out


def case_chunks(case_id: str, db: Session, store: StorageService) -> list[Chunk]:
    docs = (db.query(Document)
            .filter(Document.case_id == case_id, Document.status == DocumentStatus.READY)
            .order_by(Document.uploaded_at.asc()).all())
    chunks: list[Chunk] = []
    for d in docs:
        path = store.get_local_path(d.storage_path)
        if Path(path).exists():
            chunks += chunk_pages(d.id, d.original_name, pdf_pages(path))
    return chunks


def top_chunks(chunks: list[Chunk], query: str, k: int, min_score: float = 0.0) -> list[Chunk]:
    """Top-k chunks for the query, returned in document order."""
    if not chunks:
        return []
    sc = BM25([tokenize(c.text) for c in chunks]).scores(tokenize(query))
    best = sorted(range(len(chunks)), key=lambda i: -sc[i])[:k]
    return [chunks[i] for i in sorted(best) if sc[i] > min_score]


def format_excerpts(chunks: list[Chunk]) -> str:
    return "\n".join(f"[{c.doc_name}, p. {c.page}] {c.text}" for c in chunks)


def budgeted(chunks: list[Chunk], max_chars: int) -> list[Chunk]:
    out, total = [], 0
    for c in chunks:
        if total + len(c.text) > max_chars:
            break
        out.append(c)
        total += len(c.text)
    return out
