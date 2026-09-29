import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.app.models.review import ReviewTask
from backend.app.models.document import Document
from backend.app.models.field import FieldRecord
from backend.app.models.feedback import FeedbackCorrection, CorrectionAlias
from backend.app.audit.logger import log_event


class ReviewService:
    @staticmethod
    def create_task(
        db: Session,
        document_id: str,
        priority: str = "medium",
        reason: str = "",
        uncertainty_score: float = 0.5,
        double_review_required: bool = False
    ) -> ReviewTask:
        task = ReviewTask(
            document_id=document_id,
            status="needs_review",
            priority=priority,
            reason=reason,
            uncertainty_score=uncertainty_score,
            double_review_required=double_review_required
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        log_event(
            db,
            action="REVIEW_TASK_CREATED",
            document_id=document_id,
            details={
                "priority": priority,
                "reason": reason,
                "uncertainty_score": uncertainty_score,
                "double_review": double_review_required
            }
        )
        return task

    @staticmethod
    def apply_human_override(
        db: Session,
        task_id: str,
        field_updates: Dict[str, Any],
        reviewer_id: str = "officer_1",
        action: str = "approved",  # approved, rejected
        notes: str = "",
        is_checker: bool = False
    ) -> ReviewTask:
        """
        Applies human reviewer modifications, updates active learning memory,
        and manages maker-checker double-review status flow:
        Uploaded -> Processing -> Needs review -> Verified -> Published.
        """
        task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task:
            raise ValueError("Review task not found")

        doc = db.query(Document).filter(Document.id == task.document_id).first()
        if not doc:
            raise ValueError("Document not found")

        # Update specific fields & log feedback corrections
        for field_id, new_value in field_updates.items():
            field_rec = db.query(FieldRecord).filter(
                FieldRecord.document_id == doc.id,
                (FieldRecord.id == field_id) | (FieldRecord.field_name == field_id)
            ).first()
            if field_rec:
                old_val = field_rec.value
                field_rec.is_reviewed = True
                field_rec.reviewed_value = new_value
                field_rec.reviewed_by = reviewer_id
                field_rec.reviewed_at = datetime.utcnow()
                field_rec.confidence = 1.0  # Certified by human reviewer
                field_rec.flags.append(f"human_certified_by:{reviewer_id}")

                # 1. Store FeedbackCorrection for active learning
                correction = FeedbackCorrection(
                    document_id=doc.id,
                    field_name=field_rec.field_name,
                    raw_text=field_rec.raw_text,
                    model_value=old_val,
                    corrected_value=new_value,
                    reviewer_id=reviewer_id
                )
                db.add(correction)

                # 2. Update CorrectionAlias memory
                if field_rec.raw_text:
                    alias = db.query(CorrectionAlias).filter(CorrectionAlias.raw_text == field_rec.raw_text).first()
                    if alias:
                        alias.preferred_value = new_value
                        alias.usage_count += 1
                        alias.updated_at = datetime.utcnow()
                    else:
                        db.add(CorrectionAlias(
                            raw_text=field_rec.raw_text,
                            canonical_field=field_rec.canonical_name or field_rec.field_name,
                            preferred_value=new_value,
                            usage_count=1
                        ))

        now = datetime.utcnow()
        task.changes_made = field_updates
        task.notes = notes

        # Double-Review (Maker-Checker) Flow Logic
        if task.double_review_required and not is_checker:
            # Maker stage completed
            task.status = "maker_reviewed"
            task.maker_id = reviewer_id
            task.maker_completed_at = now
            doc.status = "maker_reviewed"
            log_event(
                db,
                action="REVIEW_MAKER_COMPLETED",
                document_id=doc.id,
                user_id=reviewer_id,
                details={"status": "maker_reviewed", "changes": len(field_updates)}
            )
        else:
            # Final approval / Checker verification
            if is_checker:
                task.checker_id = reviewer_id
                task.checker_completed_at = now
                task.status = "verified"
                doc.status = "published"
            else:
                task.status = action
                doc.status = "published" if action == "approved" else "rejected"

            task.completed_at = now
            doc.overall_confidence = max(doc.overall_confidence, 0.99)

            log_event(
                db,
                action=f"REVIEW_{task.status.upper()}",
                document_id=doc.id,
                user_id=reviewer_id,
                details={"status": doc.status, "notes": notes}
            )

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_uncertainty_priority_queue(db: Session, limit: int = 50) -> List[ReviewTask]:
        """Returns review tasks prioritized by uncertainty score (highest first)."""
        return db.query(ReviewTask).filter(
            ReviewTask.status.in_(["needs_review", "maker_reviewed", "pending"])
        ).order_by(ReviewTask.uncertainty_score.desc(), ReviewTask.created_at.desc()).limit(limit).all()

    @staticmethod
    def export_finetuning_jsonl(db: Session) -> str:
        """Exports all human corrections as fine-tuning JSONL dataset."""
        corrections = db.query(FeedbackCorrection).order_by(FeedbackCorrection.created_at.asc()).all()
        lines = []
        for c in corrections:
            lines.append(json.dumps(c.to_finetuning_dict(), ensure_ascii=False))
        return "\n".join(lines)
