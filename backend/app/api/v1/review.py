from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.review import ReviewTask
from backend.app.models.document import Document
from backend.app.review.service import ReviewService
from backend.app.auth.security import (
    get_current_user,
    AuthenticatedUser,
    ROLE_SUPERVISOR,
    ROLE_ADMIN,
    ROLE_VERIFIER
)

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("/tasks")
def list_review_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    order_by_uncertainty: bool = True,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Lists review queue tasks. Supports prioritizing by uncertainty score for active learning.
    """
    if not current_user.has_permission("REVIEW_TASK_VIEW"):
        raise HTTPException(status_code=403, detail="Forbidden: missing REVIEW_TASK_VIEW permission")

    if order_by_uncertainty and not status and not priority:
        tasks = ReviewService.get_uncertainty_priority_queue(db, limit=limit)
    else:
        query = db.query(ReviewTask)
        if status:
            query = query.filter(ReviewTask.status == status)
        if priority:
            query = query.filter(ReviewTask.priority == priority)
        tasks = query.order_by(ReviewTask.uncertainty_score.desc(), ReviewTask.created_at.desc()).limit(limit).all()

    results = []
    for t in tasks:
        doc = db.query(Document).filter(Document.id == t.document_id).first()
        results.append({
            "id": t.id,
            "document_id": t.document_id,
            "filename": doc.filename if doc else "Unknown",
            "doc_type": doc.doc_type if doc else "unknown",
            "status": t.status,
            "priority": t.priority,
            "uncertainty_score": t.uncertainty_score,
            "double_review_required": t.double_review_required,
            "reason": t.reason,
            "assigned_to": t.assigned_to,
            "notes": t.notes,
            "maker_id": t.maker_id,
            "checker_id": t.checker_id,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return results


@router.post("/tasks/{task_id}/resolve")
def resolve_review_task(
    task_id: str,
    action: str = Body(..., embed=True),  # "approved" or "rejected"
    field_updates: Dict[str, Any] = Body(default_factory=dict),
    notes: Optional[str] = Body(""),
    reviewer_id: Optional[str] = Body(None),
    is_checker: Optional[bool] = Body(None),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Submits human verification decision, updates fields, active learning alias memory,
    and advances Maker-Checker stage:
    - Verifier role submits Maker stage (maker_reviewed)
    - Supervisor / Admin role certifies and publishes (Checker stage)
    """
    user_role = current_user.role
    effective_reviewer = reviewer_id or current_user.username

    # Enforce RBAC permissions
    if not current_user.has_permission("REVIEW_TASK_MAKER") and not current_user.has_permission("REVIEW_TASK_CHECKER"):
        raise HTTPException(status_code=403, detail="Forbidden: missing review permissions")

    # Determine whether checker stage applies
    if is_checker is True:
        if not current_user.has_permission("REVIEW_TASK_CHECKER"):
            raise HTTPException(status_code=403, detail="Forbidden: only Supervisor/Admin can perform Checker verification")
        effective_is_checker = True
    elif is_checker is False:
        effective_is_checker = False
    else:
        # Auto-detect: if supervisor/admin, treat as checker; else maker
        effective_is_checker = current_user.has_role(ROLE_SUPERVISOR, ROLE_ADMIN)

    try:
        updated_task = ReviewService.apply_human_override(
            db=db,
            task_id=task_id,
            field_updates=field_updates,
            reviewer_id=effective_reviewer,
            action=action,
            notes=notes or "",
            is_checker=effective_is_checker
        )
        return {
            "success": True,
            "task_id": updated_task.id,
            "status": updated_task.status,
            "is_checker_stage": effective_is_checker,
            "completed_at": updated_task.completed_at.isoformat() if updated_task.completed_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export-finetuning")
def export_finetuning_data(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Exports all human feedback corrections as a fine-tuning dataset formatted
    in JSON Lines (JSONL) with OCR inputs and ground truth human corrections.
    """
    if not current_user.has_permission("EXPORT_FINETUNING"):
        raise HTTPException(status_code=403, detail="Forbidden: insufficient privileges to export fine-tuning data")

    jsonl_content = ReviewService.export_finetuning_jsonl(db)
    return PlainTextResponse(
        content=jsonl_content,
        media_type="application/x-jsonlines",
        headers={"Content-Disposition": "attachment; filename=bhusetu_corrections_finetuning.jsonl"}
    )
