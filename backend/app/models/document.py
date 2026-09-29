import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_sha256 = Column(String(64), nullable=False, unique=True, index=True)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    processed_path = Column(String(512), nullable=True)
    uploader_id = Column(String(36), nullable=True)

    doc_type = Column(String(50), default="unknown")  # khatauni_7_12, mutation_register, sale_deed, cadastre_map, unknown
    doc_type_confidence = Column(Float, default=0.0)
    status = Column(String(50), default="uploaded", index=True)  # uploaded, preprocessed, extracted, validated, auto_accepted, pending_review, rejected
    overall_confidence = Column(Float, default=0.0)
    metadata_info = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan", order_by="Page.page_number")
    fields = relationship("FieldRecord", back_populates="document", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="document", cascade="all, delete-orphan")
    review_tasks = relationship("ReviewTask", back_populates="document", cascade="all, delete-orphan")
    forensic_flags = relationship("ForensicFlag", back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="document", cascade="all, delete-orphan")
    mutation_events = relationship("MutationEvent", back_populates="document", cascade="all, delete-orphan")
    owner_shares = relationship("OwnerShare", back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(512), nullable=False)
    processed_image_path = Column(String(512), nullable=True)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)

    # Per-page and per-tile quality metrics
    quality_metrics = Column(JSON, default=dict)
    # Layout detection: table regions, handwritten areas, stamp positions
    layout_data = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="pages")
    fields = relationship("FieldRecord", back_populates="page", cascade="all, delete-orphan")
