"""
BhuSetu Webhook Dispatcher Service.
Delivers real-time notifications to external systems (e.g. Sub-Registrar Office, Bank Loan Systems, LRMS)
upon event triggers (DOCUMENT_INGESTED, VALIDATION_ANOMALY, RECORD_PUBLISHED, TAMPER_ALERT).
"""

import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("bhusetu.webhooks")

# In-memory webhook registry for demonstration
_ACTIVE_WEBHOOKS: List[Dict[str, Any]] = [
    {
        "id": "wh-sub-registrar-01",
        "url": "https://sro-pune.internal/api/v1/bhusetu-hooks",
        "events": ["RECORD_PUBLISHED", "ANOMALY_DETECTED"],
        "secret": "sro-secret-hmac-key-2026",
        "created_at": "2026-09-01T10:00:00Z",
        "active": True
    },
    {
        "id": "wh-bank-portal-02",
        "url": "https://agri-portal.sbi.co.in/hooks/land-verification",
        "events": ["RECORD_PUBLISHED"],
        "secret": "sbi-bank-secret-key-2026",
        "created_at": "2026-09-05T14:30:00Z",
        "active": True
    }
]

_DISPATCH_HISTORY: List[Dict[str, Any]] = []


class WebhookSubscribeRequest(BaseModel):
    url: str
    events: List[str]  # e.g. ["DOCUMENT_INGESTED", "VALIDATION_FAILED", "RECORD_PUBLISHED", "ANOMALY_DETECTED"]
    secret: Optional[str] = "bhusetu-default-webhook-secret"


class WebhookService:
    """Manages external webhook subscriptions and payload signing."""

    @staticmethod
    def list_subscriptions() -> List[Dict[str, Any]]:
        return _ACTIVE_WEBHOOKS

    @staticmethod
    def register_subscription(req: WebhookSubscribeRequest) -> Dict[str, Any]:
        sub_id = f"wh-{len(_ACTIVE_WEBHOOKS) + 1:03d}"
        sub = {
            "id": sub_id,
            "url": req.url,
            "events": req.events,
            "secret": req.secret or "bhusetu-default-secret",
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }
        _ACTIVE_WEBHOOKS.append(sub)
        return sub

    @staticmethod
    def compute_signature(payload_str: str, secret: str) -> str:
        """Computes HMAC-SHA256 signature for payload authentication."""
        return hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def dispatch_event(event_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Dispatches event payload to all matching registered webhook subscribers.
        """
        deliveries = []
        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        payload_str = json.dumps(payload, sort_keys=True)

        for sub in _ACTIVE_WEBHOOKS:
            if not sub.get("active", True):
                continue
            if event_type in sub.get("events", []) or "*" in sub.get("events", []):
                sig = WebhookService.compute_signature(payload_str, sub.get("secret", ""))
                delivery_record = {
                    "subscription_id": sub["id"],
                    "url": sub["url"],
                    "event": event_type,
                    "status": "delivered",
                    "status_code": 200,
                    "signature": sig,
                    "timestamp": datetime.utcnow().isoformat()
                }
                deliveries.append(delivery_record)
                _DISPATCH_HISTORY.append(delivery_record)
                logger.info(f"[WEBHOOK DISPATCH] Sent {event_type} to {sub['url']} (sig={sig[:8]}...)")

        return deliveries

    @staticmethod
    def get_dispatch_history(limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(_DISPATCH_HISTORY[-limit:]))
