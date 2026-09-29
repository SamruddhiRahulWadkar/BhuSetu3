import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class FieldRecord(Base):
    __tablename__ = "fields"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("pages.id", ondelete="CASCADE"), nullable=True, index=True)

    field_name = Column(String(100), nullable=False, index=True)
    canonical_name = Column(String(100), nullable=True, index=True)

    # Core object fields
    value = Column(JSON, nullable=True)  # Structured value or string
    raw_text = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    bbox = Column(JSON, default=list)  # [ymin, xmin, ymax, xmax] normalized (0.0 to 1.0)
    source_engine = Column(String(50), default="gemini")  # gemini, tesseract, ensemble, mock
    flags = Column(JSON, default=list)  # list of explainability flags

    # Confidence breakdown: {ocr, agreement, damage_penalty, format, consistency, final}
    confidence_breakdown = Column(JSON, default=dict)

    # Human review overrides
    is_reviewed = Column(Boolean, default=False)
    reviewed_value = Column(JSON, nullable=True)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="fields")
    page = relationship("Page", back_populates="fields")

    def to_dict(self):
        """Always return the strict BhuSetu field object representation:
        {value, raw_text, confidence, bbox, source_engine, flags, confidence_breakdown}
        """
        val = self.reviewed_value if self.is_reviewed and self.reviewed_value is not None else self.value
        return {
            "id": self.id,
            "field_name": self.field_name,
            "canonical_name": self.canonical_name or self.field_name,
            "value": val,
            "raw_text": self.raw_text or "",
            "confidence": round(self.confidence, 4) if self.confidence is not None else 0.0,
            "bbox": self.bbox or [],
            "source_engine": self.source_engine or "unknown",
            "flags": self.flags or [],
            "confidence_breakdown": self.confidence_breakdown or {},
            "is_reviewed": self.is_reviewed,
        }
