import pytest
from backend.app.validation.engine import LegalLogicValidationEngine
from backend.app.extraction.schemas import (
    FieldItem, PlotAreaItem, OwnerShareItem,
    MutationRecordItem, RegistrationDetailItem, LandRecordExtraction
)
from backend.app.models.validation import LEGAL_DISCLAIMER


@pytest.fixture
def engine():
    eng = LegalLogicValidationEngine()
    eng.load_all_rules()
    return eng


def make_clean_extraction() -> LandRecordExtraction:
    return LandRecordExtraction(
        document_type=FieldItem(value="khatauni_7_12", confidence=0.98),
        state=FieldItem(value="Maharashtra", confidence=0.98),
        district=FieldItem(value="Pune", confidence=0.98),
        tehsil=FieldItem(value="Haveli", confidence=0.98),
        village=FieldItem(value="Wagholi", confidence=0.98),
        survey_no=FieldItem(value="101", confidence=0.95),
        khata_no=FieldItem(value="55", confidence=0.95),
        sub_division=FieldItem(value="1", confidence=0.95),
        ulpin=FieldItem(value="27HA1001000101", confidence=0.98),
        plot_area=PlotAreaItem(
            value=FieldItem(value=40.0, confidence=0.95),
            unit=FieldItem(value="guntha", confidence=0.95),
            area_sqm=FieldItem(value=4046.86, confidence=0.95),
            area_hectares=FieldItem(value=0.4047, confidence=0.95)
        ),
        land_classification=FieldItem(value="irrigated", confidence=0.95),
        ownership_type=FieldItem(value="freehold", confidence=0.95),
        landowners=[
            OwnerShareItem(
                name=FieldItem(value="Ramesh Patil", confidence=0.95),
                share=FieldItem(value=0.5, raw_text="1/2", confidence=0.95),
                is_minor=FieldItem(value=False),
                is_deceased=FieldItem(value=False)
            ),
            OwnerShareItem(
                name=FieldItem(value="Suresh Patil", confidence=0.95),
                share=FieldItem(value=0.5, raw_text="1/2", confidence=0.95),
                is_minor=FieldItem(value=False),
                is_deceased=FieldItem(value=False)
            )
        ],
        mutation_entries=[
            MutationRecordItem(
                mutation_no=FieldItem(value="M-801", confidence=0.95),
                mutation_date=FieldItem(value="2021-09-15", confidence=0.95),
                registration_date=FieldItem(value="2021-05-10", confidence=0.95),
                from_party=FieldItem(value="Ramesh Patil", confidence=0.95),
                to_party=FieldItem(value="Suresh Patil", confidence=0.95),
                transferred_area=FieldItem(value=2000.0, confidence=0.95)
            )
        ],
        registration=RegistrationDetailItem(
            reg_no=FieldItem(value="REG-2021-3001", confidence=0.95),
            reg_date=FieldItem(value="2021-05-10", confidence=0.95)
        )
    )


def test_clean_document_passes_validation(engine):
    ext = make_clean_extraction()
    results, score, failed = engine.validate_document("DOC-CLEAN-01", ext)

    assert score >= 0.90
    assert len(failed) == 0
    for r in results:
        assert r.disclaimer == LEGAL_DISCLAIMER


def test_fault_share_sum_discrepancy(engine):
    ext = make_clean_extraction()
    # Invalidate shares (0.4 + 0.4 = 0.8 != 1.0)
    ext.landowners[0].share.value = 0.4
    ext.landowners[1].share.value = 0.4

    results, score, failed = engine.validate_document("DOC-FAULT-SHARE", ext)
    assert "RULE_SHARE_SUM_100" in failed
    failed_result = next(r for r in results if r.rule_id == "RULE_SHARE_SUM_100")
    assert failed_result.status == "failed"
    assert failed_result.severity == "critical"
    assert "discrepancy" in failed_result.evidence


def test_fault_area_exceeding_holding(engine):
    ext = make_clean_extraction()
    # Transferred area 8000 sqm > holding 4046.86 sqm
    ext.mutation_entries[0].transferred_area.value = 8000.0

    results, score, failed = engine.validate_document("DOC-FAULT-AREA", ext)
    assert "RULE_AREA_HOLDING_LIMIT" in failed
    res = next(r for r in results if r.rule_id == "RULE_AREA_HOLDING_LIMIT")
    assert res.status == "failed"
    assert "exceeds parcel holding" in res.message


def test_fault_mutation_before_registration(engine):
    ext = make_clean_extraction()
    # Mutation earlier than deed
    ext.mutation_entries[0].mutation_date.value = "2020-01-10"
    ext.mutation_entries[0].registration_date.value = "2020-08-20"

    results, score, failed = engine.validate_document("DOC-FAULT-CHRONO", ext)
    assert "RULE_MUTATION_CHRONOLOGY" in failed
    res = next(r for r in results if r.rule_id == "RULE_MUTATION_CHRONOLOGY")
    assert res.status == "failed"


def test_fault_party_acting_after_death(engine):
    ext = make_clean_extraction()
    # Ramesh is deceased
    ext.landowners[0].is_deceased.value = True
    # But Ramesh is executing a mutation transfer
    ext.mutation_entries[0].from_party.value = "Ramesh Patil"

    results, score, failed = engine.validate_document("DOC-FAULT-DECEASED", ext)
    assert "RULE_PARTY_LEGAL_CAPACITY" in failed
    res = next(r for r in results if r.rule_id == "RULE_PARTY_LEGAL_CAPACITY")
    assert res.status == "failed"


def test_fault_na_conversion_without_order(engine):
    ext = make_clean_extraction()
    ext.land_classification.value = "commercial non_agricultural"
    ext.na_conversion_order_ref = None

    results, score, failed = engine.validate_document("DOC-FAULT-NA", ext)
    assert "RULE_LAND_CLASS_CONVERSION_ORDER" in failed


def test_fault_restricted_tenure_without_permission(engine):
    ext = make_clean_extraction()
    ext.ownership_type.value = "tribal_restricted"
    ext.restricted_tenure_permission_ref = None

    results, score, failed = engine.validate_document("DOC-FAULT-TENURE", ext)
    assert "RULE_RESTRICTED_TENURE_TRANSFER" in failed


def test_fault_duplicate_registration_number(engine):
    ext = make_clean_extraction()
    existing_docs = [{"id": "PRIOR_DOC_999", "reg_no": "REG-2021-3001"}]

    results, score, failed = engine.validate_document("DOC-NEW-01", ext, existing_documents=existing_docs)
    assert "RULE_DUPLICATE_REGISTRY_DETECTION" in failed


def test_fault_invalid_ulpin_format(engine):
    ext = make_clean_extraction()
    ext.ulpin.value = "INVALID_ULPIN_TOO_LONG_1234567"

    results, score, failed = engine.validate_document("DOC-FAULT-ULPIN", ext)
    assert "RULE_IDENTIFIER_FORMAT_CHECK" in failed


def test_fault_invalid_lrms_hierarchy(engine):
    ext = make_clean_extraction()
    # Fictitious village not in Maharashtra Pune Haveli
    ext.village.value = "AtlantisVillage"

    results, score, failed = engine.validate_document("DOC-FAULT-HIERARCHY", ext)
    assert "RULE_ADMIN_HIERARCHY_VALIDITY" in failed
