from typing import Dict, Any, List, Tuple
from backend.app.extraction.schemas import FieldItem
from backend.app.config import settings

CRITICAL_FIELDS = ["owner_name", "survey_no", "khasra_no", "plot_area_value", "owner_0_share", "owner_0_name", "share"]


def route_document(
    fields: Dict[str, FieldItem],
    overall_confidence: float,
    failed_critical_rules: bool = False
) -> Tuple[str, List[str], str]:
    """
    Evaluates routing policy based on confidence scores and critical field thresholds:
    - Status: 'auto_accepted', 'field_review', 'document_review'
    - Returns: (status, review_reasons, priority)
    """
    review_reasons = []
    has_flagged_field = False
    has_critical_uncertainty = False

    if failed_critical_rules:
        review_reasons.append("Critical legal-logic validation rule failure")
        has_critical_uncertainty = True

    for field_name, field in fields.items():
        conf = field.confidence
        is_critical = any(crit in field_name.lower() for crit in ["owner", "survey", "khasra", "area", "share"])

        if is_critical and conf < settings.FIELD_REVIEW_THRESHOLD:
            has_critical_uncertainty = True
            review_reasons.append(
                f"Critical field '{field_name}' confidence {conf:.2f} below threshold {settings.FIELD_REVIEW_THRESHOLD}"
            )
        elif conf < settings.AUTO_ACCEPT_THRESHOLD:
            has_flagged_field = True
            review_reasons.append(f"Field '{field_name}' requires verification (confidence: {conf:.2f})")

    if overall_confidence < settings.FIELD_REVIEW_THRESHOLD or has_critical_uncertainty:
        return "document_review", review_reasons, "high"
    elif has_flagged_field:
        return "field_review", review_reasons, "medium"
    else:
        return "auto_accepted", ["All fields met >=0.90 confidence and legal rules passed"], "low"
