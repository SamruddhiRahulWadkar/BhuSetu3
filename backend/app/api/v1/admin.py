from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.validation.engine import LegalLogicValidationEngine
from backend.app.audit.logger import log_event
from backend.app.auth.security import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/admin", tags=["Admin"])
engine = LegalLogicValidationEngine()


@router.get("/rules")
def get_admin_rules(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Lists all configurable validation rules with status and editable thresholds."""
    engine.load_all_rules()
    return list(engine.rules.values())


@router.put("/rules/{rule_id}")
def update_rule(
    rule_id: str,
    enabled: bool = Body(..., embed=True),
    updates: Dict[str, Any] = Body(default_factory=dict),
    user_id: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Admin endpoint to enable/disable validation rules or tune thresholds with audit trail."""
    if not current_user.has_permission("VALIDATION_RULES_MANAGE"):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: role '{current_user.role}' cannot modify validation rules. Admin privilege required."
        )

    rule = engine.rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    payload = updates or {}
    payload["enabled"] = enabled

    success = engine.update_rule_config(rule_id, payload)
    if not success:
        raise HTTPException(status_code=400, detail="Could not update rule")

    effective_user = user_id or current_user.username
    log_event(
        db,
        action="RULE_UPDATED",
        user_id=effective_user,
        entity_type="validation_rule",
        entity_id=rule_id,
        details={"enabled": enabled, "updates": payload}
    )

    return {"success": True, "rule": engine.rules[rule_id]}
