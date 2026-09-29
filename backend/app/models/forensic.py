import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ForensicFlag(Base):
    __tablename__ = "forensic_flags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("pages.id", ondelete="CASCADE"), nullable=True, index=True)

    flag_type = Column(String(50), nullable=False)  # overwritten_digits, pasted_stamp_date, font_inconsistency, seam_detected, noise_inconsistency
    severity = Column(String(20), default="warn")  # info, warn, error, critical
    bbox = Column(JSON, default=list)  # [ymin, xmin, ymax, xmax] normalized
    confidence = Column(Float, default=0.0)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="forensic_flags")
