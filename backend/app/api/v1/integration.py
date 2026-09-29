from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.integration.dilrmp_mis_adapter import DILRMPMISAdapter
from backend.app.integration.lrms_adapter import LRMSAdapter
from backend.app.integration.webhook_service import WebhookService, WebhookSubscribeRequest
from backend.app.auth.security import get_current_user, AuthenticatedUser, ROLE_ADMIN, ROLE_SUPERVISOR

router = APIRouter(prefix="/integration", tags=["Government Integrations & Webhooks"])
lrms_adapter = LRMSAdapter()


@router.get("/dilrmp-dashboard")
def get_dilrmp_mis_dashboard(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns live Digital India Land Records Modernization Programme (DILRMP) metrics
    for monitoring digitization progress, cadastral integration, and legal consistency.
    """
    return DILRMPMISAdapter.generate_mis_dashboard_report(db)


@router.post("/dilrmp-sync")
def sync_to_dilrmp_portal(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Pushes local BhuSetu progress and validation compliance report to the National DILRMP MIS.
    Requires Supervisor or Admin privileges.
    """
    if not current_user.has_role(ROLE_ADMIN, ROLE_SUPERVISOR):
        raise HTTPException(status_code=403, detail="Forbidden: only Supervisor or Admin can trigger national DILRMP sync")

    report = DILRMPMISAdapter.generate_mis_dashboard_report(db)
    ack = DILRMPMISAdapter.sync_to_central_portal(report)
    return ack


@router.get("/lrms-verify")
def verify_lrms_hierarchy(
    state: str = Query(..., description="State name (e.g. Maharashtra, Uttar Pradesh)"),
    district: str = Query(..., description="District name"),
    tehsil: str = Query(..., description="Tehsil / Taluka name"),
    village: str = Query(..., description="Village name"),
    survey_no: Optional[str] = Query(None, description="Optional Survey / Khasra number")
):
    """
    Validates revenue administrative hierarchy against the National LRMS Master Directory.
    """
    if survey_no:
        return lrms_adapter.fetch_survey_status(state, district, tehsil, village, survey_no)
    return lrms_adapter.check_hierarchy(state, district, tehsil, village)


@router.get("/webhooks")
def list_webhooks(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Lists registered external webhook subscriptions."""
    return WebhookService.list_subscriptions()


@router.post("/webhooks/subscribe")
def subscribe_webhook(
    req: WebhookSubscribeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Registers a new webhook subscriber with HMAC-SHA256 signature support."""
    if not current_user.has_role(ROLE_ADMIN, ROLE_SUPERVISOR):
        raise HTTPException(status_code=403, detail="Forbidden: Admin or Supervisor role required to register webhooks")
    return WebhookService.register_subscription(req)


@router.post("/webhooks/test-dispatch")
def test_webhook_dispatch(
    event: str = Body("RECORD_PUBLISHED", embed=True),
    document_id: str = Body("doc-sample-01", embed=True),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Sends a test webhook event across active subscribers and returns delivery receipts."""
    test_data = {
        "document_id": document_id,
        "event_trigger": event,
        "initiated_by": current_user.username,
        "verified_ulpin": "27HA1001000101",
        "action": "Automated Webhook Test"
    }
    deliveries = WebhookService.dispatch_event(event, test_data)
    return {
        "event": event,
        "dispatched_count": len(deliveries),
        "deliveries": deliveries
    }
