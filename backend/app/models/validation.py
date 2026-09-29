import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

LEGAL_DISCLAIMER = "advisory, not legal advice"


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    rule_id = Column(String(100), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warn, error, critical
    status = Column(String(20), nullable=False)  # passed, failed, skipped
    message = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict)  # field paths, compared values, calculations
    disclaimer = Column(String(100), default=LEGAL_DISCLAIMER)

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="validation_results")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            "evidence": self.evidence or {},
            "disclaimer": self.disclaimer or LEGAL_DISCLAIMER,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
