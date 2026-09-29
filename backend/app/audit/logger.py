import logging
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.audit import AuditLog

logger = logging.getLogger("bhusetu.audit")
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def log_event(
    db: Session,
    action: str,
    document_id: Optional[str] = None,
    user_id: Optional[str] = "system",
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Persists an immutable audit log entry chained cryptographically via SHA-256.
    Every entry includes the hash of the preceding audit entry.
    """
    # 1. Fetch latest audit log for previous hash
    last_log = db.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).first()
    prev_hash = last_log.current_hash if (last_log and last_log.current_hash) else GENESIS_HASH

    import uuid
    from datetime import datetime

    entry_id = str(uuid.uuid4())
    entry_time = datetime.utcnow()

    # 2. Instantiate new entry
    entry = AuditLog(
        id=entry_id,
        document_id=document_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type or "document",
        entity_id=entity_id or document_id,
        details=details or {},
        ip_address=ip_address or "127.0.0.1",
        timestamp=entry_time,
        previous_hash=prev_hash
    )
    # Compute current hash
    entry.current_hash = entry.compute_hash(prev_hash)

    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info(f"[AUDIT CHAIN] action={action} doc={document_id} hash={entry.current_hash[:12]}...")
    return entry


def verify_audit_chain_integrity(db: Session) -> Dict[str, Any]:
    """
    Traverses the complete audit log sequence and cryptographically verifies
    hash-chain continuity. Detects any unauthorized modification or deletion.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()).all()
    if not logs:
        return {
            "chain_valid": True,
            "total_blocks": 0,
            "message": "Audit trail is empty (Genesis state)."
        }

    expected_prev = GENESIS_HASH
    for idx, entry in enumerate(logs):
        # 1. Check previous hash continuity
        if idx == 0 and not entry.previous_hash:
            # First log entry
            pass
        elif entry.previous_hash and entry.previous_hash != expected_prev:
            return {
                "chain_valid": False,
                "total_blocks": len(logs),
                "broken_at_index": idx,
                "broken_at_block_id": entry.id,
                "expected_previous_hash": expected_prev,
                "actual_previous_hash": entry.previous_hash,
                "message": f"Cryptographic audit chain broken at block #{idx} (ID: {entry.id}). Previous hash mismatch!"
            }

        # 2. Check current hash self-consistency
        expected_curr = entry.compute_hash(entry.previous_hash or expected_prev)
        if entry.current_hash and entry.current_hash != expected_curr:
            return {
                "chain_valid": False,
                "total_blocks": len(logs),
                "broken_at_index": idx,
                "broken_at_block_id": entry.id,
                "message": f"Tampering detected within block #{idx} (ID: {entry.id}). Record contents modified!"
            }

        expected_prev = entry.current_hash or expected_curr

    return {
        "chain_valid": True,
        "total_blocks": len(logs),
        "genesis_hash": GENESIS_HASH,
        "latest_block_hash": expected_prev,
        "message": f"Cryptographic integrity verified across {len(logs)} audit blocks. Zero tampering detected."
    }
