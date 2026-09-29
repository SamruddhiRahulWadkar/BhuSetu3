import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text
from backend.app.database import Base


class FeedbackCorrection(Base):
    """
    Active Learning Feedback: Stores human corrections for model fine-tuning and active memory.
    """
    __tablename__ = "feedback_corrections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    raw_text = Column(Text, nullable=True)
    model_value = Column(JSON, nullable=True)
    corrected_value = Column(JSON, nullable=True)
    reviewer_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_finetuning_dict(self):
        return {
            "messages": [
                {"role": "system", "content": "Extract standardized land record field."},
                {"role": "user", "content": f"Extract field '{self.field_name}' from raw text: '{self.raw_text}'"},
                {"role": "assistant", "content": str(self.corrected_value)}
            ]
        }


class CorrectionAlias(Base):
    """
    Alias / Correction Memory: Auto-applies human corrections to identical raw_text.
    """
    __tablename__ = "correction_aliases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raw_text = Column(String(255), unique=True, index=True, nullable=False)
    canonical_field = Column(String(100), nullable=False)
    preferred_value = Column(JSON, nullable=False)
    usage_count = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
