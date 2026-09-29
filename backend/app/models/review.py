import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ReviewTask(Base):
    """
    Human Review Task with Maker-Checker (Double-Review) workflow
    and Uncertainty-Priority Queueing.
    Status flow: Uploaded -> Processing -> Needs review -> Verified -> Published
    """
    __tablename__ = "review_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(50), default="needs_review", index=True)  # needs_review, maker_reviewed, verified, published, rejected, escalated
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    reason = Column(Text, nullable=True)  # e.g. "Low confidence in owner name (0.54); share sum mismatch"
    assigned_to = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    changes_made = Column(JSON, default=dict)

    # Uncertainty Queue Score (higher = more uncertain = prioritize first)
    uncertainty_score = Column(Float, default=0.5)

    # Double-Review (Maker-Checker)
    double_review_required = Column(Boolean, default=False)
    maker_id = Column(String(36), nullable=True)
    maker_completed_at = Column(DateTime, nullable=True)
    checker_id = Column(String(36), nullable=True)
    checker_completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="review_tasks")
