from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.audit import AuditLog
from backend.app.audit.logger import verify_audit_chain_integrity

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("/")
def get_audit_trail(
    document_id: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Retrieves immutable audit event log history for pipeline transparency."""
    query = db.query(AuditLog)
    if document_id:
        query = query.filter(AuditLog.document_id == document_id)
    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": l.id,
            "document_id": l.document_id,
            "user_id": l.user_id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "details": l.details,
            "ip_address": l.ip_address,
            "previous_hash": l.previous_hash,
            "current_hash": l.current_hash,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None
        }
        for l in logs
    ]


@router.get("/verify-chain")
def verify_audit_chain(db: Session = Depends(get_db)):
    """
    Cryptographically verifies the SHA-256 hash chaining of all audit records.
    Returns status, block count, and confirms zero tampering across the audit log.
    """
    return verify_audit_chain_integrity(db)
