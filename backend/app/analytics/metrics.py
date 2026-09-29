from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.document import Document
from backend.app.models.validation import ValidationResult
from backend.app.models.review import ReviewTask
from backend.app.models.audit import AuditLog


def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """Computes executive SIH analytics dashboard metrics."""
    total_docs = db.query(Document).count()
    auto_accepted = db.query(Document).filter(Document.status.in_(["auto_accepted", "certified"])).count()
    pending_review = db.query(Document).filter(Document.status.in_(["pending_review", "uploaded", "preprocessed"])).count()
    rejected = db.query(Document).filter(Document.status == "rejected").count()

    # Average confidence
    avg_conf = db.query(func.avg(Document.overall_confidence)).scalar() or 0.0

    # Validation stats
    total_validations = db.query(ValidationResult).count()
    failed_validations = db.query(ValidationResult).filter(ValidationResult.status == "failed").count()
    critical_flags = db.query(ValidationResult).filter(
        ValidationResult.status == "failed",
        ValidationResult.severity.in_(["critical", "error"])
    ).count()

    # Doc types
    type_counts = db.query(Document.doc_type, func.count(Document.id)).group_by(Document.doc_type).all()
    doc_type_distribution = {t: count for t, count in type_counts}

    # Recent activity
    recent_audits = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    activity = [
        {
            "id": a.id,
            "action": a.action,
            "document_id": a.document_id,
            "user_id": a.user_id,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "details": a.details
        }
        for a in recent_audits
    ]

    auto_accept_rate = round((auto_accepted / max(1, total_docs)) * 100.0, 1)

    return {
        "total_documents": total_docs,
        "auto_accepted_count": auto_accepted,
        "auto_accept_rate_pct": auto_accept_rate,
        "pending_review_count": pending_review,
        "rejected_count": rejected,
        "average_confidence": round(float(avg_conf), 3),
        "total_validations_run": total_validations,
        "failed_validations": failed_validations,
        "critical_flags_detected": critical_flags,
        "doc_type_distribution": doc_type_distribution,
        "recent_activity": activity
    }
