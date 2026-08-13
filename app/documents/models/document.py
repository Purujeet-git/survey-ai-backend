"""
SurveyAI Backend

Module:
Document Model

Purpose:
Defines database model for uploaded claim documents, photos, and versioned revisions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    """
    Represents a claim document or evidence photo with metadata, versioning, classification, and OCR.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="other",
        server_default="other",
        index=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    parent_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    processing_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
        index=True,
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    classification_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    doc_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    claim: Mapped["Claim"] = relationship("Claim")
    user: Mapped["User"] = relationship("User")
    organization: Mapped["Organization | None"] = relationship("Organization")

    parent_document: Mapped["Document | None"] = relationship(
        "Document",
        remote_side=[id],
        back_populates="versions",
    )

    versions: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="parent_document",
        cascade="all, delete-orphan",
    )
