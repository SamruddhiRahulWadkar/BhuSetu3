import pytest
from backend.app.confidence.scorer import DamageAwareConfidenceScorer
from backend.app.confidence.routing import route_document
from backend.app.extraction.schemas import FieldItem


@pytest.fixture
def scorer():
    return DamageAwareConfidenceScorer()


def test_confidence_breakdown_clean_field(scorer):
    field = FieldItem(
        value="101/A",
        raw_text="101/A",
        confidence=0.95,
        bbox=[0.1, 0.1, 0.2, 0.3],
        source_engine="gemini"
    )

    breakdown = scorer.score_field(
        field_name="survey_no",
        field_item=field,
        agreement_score=1.0,
        quality_metrics={"blur_score": 250.0, "fade_score": 0.05, "stain_coverage": 0.02}
    )

    assert hasattr(breakdown, "ocr")
    assert hasattr(breakdown, "agreement")
    assert hasattr(breakdown, "damage_penalty")
    assert hasattr(breakdown, "format")
    assert hasattr(breakdown, "consistency")
    assert hasattr(breakdown, "final")

    assert breakdown.damage_penalty == 0.0
    assert breakdown.final >= 0.90
    assert field.confidence == breakdown.final


def test_confidence_penalty_on_damage(scorer):
    field = FieldItem(
        value="Ramesh Patil",
        raw_text="Ramesh Patil",
        confidence=0.92,
        bbox=[0.1, 0.1, 0.2, 0.3],
        source_engine="gemini"
    )

    # Blurry and stained tile metrics
    quality = {
        "blur_score": 30.0,
        "fade_score": 0.65,
        "stain_coverage": 0.40,
        "tile_metrics": [
            {"bbox": [0.0, 0.0, 0.5, 0.5], "blur": 25.0, "fade": 0.70, "stain": 0.45, "tear": 0.0}
        ]
    }

    breakdown = scorer.score_field(
        field_name="owner_name",
        field_item=field,
        agreement_score=0.8,
        quality_metrics=quality
    )

    assert breakdown.damage_penalty > 0.08
    assert breakdown.final < 0.90
    assert any("damage_penalty_applied" in flag for flag in field.flags)


def test_routing_policy():
    fields_clean = {
        "owner_name": FieldItem(value="Ramesh", confidence=0.96),
        "survey_no": FieldItem(value="101", confidence=0.95),
        "plot_area_value": FieldItem(value=40.0, confidence=0.94)
    }
    status, reasons, priority = route_document(fields_clean, overall_confidence=0.95)
    assert status == "auto_accepted"

    # Single non-critical low confidence field -> field_review
    fields_medium = {
        "owner_name": FieldItem(value="Ramesh", confidence=0.96),
        "survey_no": FieldItem(value="101", confidence=0.95),
        "remarks": FieldItem(value="some note", confidence=0.72)
    }
    status, reasons, priority = route_document(fields_medium, overall_confidence=0.88)
    assert status == "field_review"

    # Critical field uncertain -> full document review
    fields_critical_low = {
        "owner_name": FieldItem(value="Ramesh", confidence=0.45),
        "survey_no": FieldItem(value="101", confidence=0.95)
    }
    status, reasons, priority = route_document(fields_critical_low, overall_confidence=0.70)
    assert status == "document_review"
    assert priority == "high"
