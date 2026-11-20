"""
Court Vision AI — SQLAlchemy Model: Precedent (knowledge base)

Every uploaded judgment/case document is indexed here so that later precedent
searches can return it alongside AI-suggested authorities.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Precedent(Base):
    __tablename__ = "precedents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Content hash: the same judgment uploaded to several cases is stored once
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    source_case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    source_document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_name: Mapped[str] = mapped_column(String(500), nullable=False)

    case_title: Mapped[str] = mapped_column(String(500), nullable=False)
    citation: Mapped[str | None] = mapped_column(String(300), nullable=True)
    court: Mapped[str | None] = mapped_column(String(300), nullable=True)
    decision_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bench: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ratio_decidendi: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_principles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    statutory_provisions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Page-tagged full text: [{"page": 1, "text": "..."}]
    pages: Mapped[list] = mapped_column(JSON, nullable=False)
    extraction: Mapped[str] = mapped_column(String(20), nullable=False, default="ai")  # ai | heuristic | cited
    # For authorities cited inside an uploaded judgment: which judgment cited it
    cited_in_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    cited_in: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
