import uuid
import hashlib
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)

    action = Column(String(100), nullable=False, index=True)  # UPLOAD, PREPROCESS, OCR_EXTRACT, NORMALIZE, VALIDATE, REVIEW_ACCEPT, REVIEW_REJECT, RULE_UPDATE, LOGIN, VIEW, EXPORT
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(36), nullable=True)

    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Cryptographic Hash Chaining for Immutable Audit Integrity
    previous_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=True, index=True)

    document = relationship("Document", back_populates="audit_logs")

    def compute_hash(self, prev_hash: str = "GENESIS_BLOCK_BHUSETU_SIH_26018") -> str:
        """Computes SHA-256 hash chaining over audit record contents."""
        payload = {
            "prev_hash": prev_hash,
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else ""
        }
        raw_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
