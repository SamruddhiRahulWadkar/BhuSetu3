import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.user import User
from backend.app.models.document import Document, Page
from backend.app.models.field import FieldRecord
from backend.app.models.review import ReviewTask
from backend.app.models.audit import AuditLog
from backend.app.auth.security import (
    ROLE_ADMIN,
    ROLE_SUPERVISOR,
    ROLE_VERIFIER,
    ROLE_OPERATOR,
    ROLE_AUDITOR,
    ROLE_READONLY_API,
    get_role_permissions,
    mask_name,
    mask_id_number,
    mask_field_value,
    mask_document_fields,
    create_access_token,
    decode_access_token,
    AuthenticatedUser
)
from backend.app.audit.logger import log_event, verify_audit_chain_integrity
from backend.app.review.service import ReviewService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_rbac_permission_matrix():
    admin_perms = get_role_permissions(ROLE_ADMIN)
    supervisor_perms = get_role_permissions(ROLE_SUPERVISOR)
    verifier_perms = get_role_permissions(ROLE_VERIFIER)
    operator_perms = get_role_permissions(ROLE_OPERATOR)
    auditor_perms = get_role_permissions(ROLE_AUDITOR)
    api_perms = get_role_permissions(ROLE_READONLY_API)

    # Admin has all permissions
    assert "VALIDATION_RULES_MANAGE" in admin_perms
    assert "DOCUMENT_DELETE" in admin_perms
    assert "VIEW_PII" in admin_perms

    # Supervisor can check and certify, but cannot manage validation rules
    assert "REVIEW_TASK_CHECKER" in supervisor_perms
    assert "VALIDATION_RULES_MANAGE" not in supervisor_perms

    # Verifier has maker rights, but not checker
    assert "REVIEW_TASK_MAKER" in verifier_perms
    assert "REVIEW_TASK_CHECKER" not in verifier_perms

    # Operator cannot verify tasks or see PII
    assert "DOCUMENT_UPLOAD" in operator_perms
    assert "VIEW_PII" not in operator_perms
    assert "REVIEW_TASK_CHECKER" not in operator_perms

    # Auditor has read-only audit log and chain verification
    assert "AUDIT_CHAIN_VERIFY" in auditor_perms
    assert "AUDIT_LOG_READ" in auditor_perms
    assert "DOCUMENT_UPLOAD" not in auditor_perms

    # Readonly API client has restricted API access
    assert "API_INTEGRATION_ACCESS" in api_perms
    assert "VIEW_PII" not in api_perms


def test_pii_masking_helpers():
    # Names
    assert mask_name("Ramesh") == "R****h"
    assert mask_name("Ramesh Kumar") == "R****h K***r"
    assert mask_name("Anand") == "A***d"

    # Aadhaar (12 digits)
    assert mask_id_number("1234 5678 9012") == "XXXX-XXXX-9012"
    assert mask_id_number("123456789012") == "XXXX-XXXX-9012"

    # Mobile (10 digits)
    assert mask_id_number("9876543210") == "XXXXXX3210"

    # PAN
    assert mask_id_number("ABCDE1234F") == "XXXXXX234F"


def test_document_pii_masking():
    doc_payload = {
        "id": "doc-123",
        "fields": [
            {"field_name": "survey_no", "value": "142/1", "raw_text": "142/1", "flags": []},
            {"field_name": "owner_name", "value": "Suresh Patil", "raw_text": "सुरेश पाटील", "flags": []},
            {"field_name": "aadhaar_number", "value": "999988887777", "raw_text": "999988887777", "flags": []}
        ],
        "owner_shares": [
            {"owner_name": "Suresh Patil", "share": 1.0}
        ]
    }

    # Masked view (for Public/Readonly API)
    masked = mask_document_fields(doc_payload, has_pii_perm=False)
    assert masked["fields"][0]["value"] == "142/1"
    assert masked["fields"][1]["value"] == "S****h P***l"
    assert "pii_masked:restricted_access" in masked["fields"][1]["flags"]
    assert masked["fields"][2]["value"] == "XXXX-XXXX-7777"
    assert masked["owner_shares"][0]["owner_name"] == "S****h P***l"

    # Unmasked view (for Revenue Officer)
    unmasked = mask_document_fields(doc_payload, has_pii_perm=True)
    assert unmasked["fields"][1]["value"] == "Suresh Patil"
    assert unmasked["fields"][2]["value"] == "999988887777"


def test_token_creation_and_decoding():
    token = create_access_token({"sub": "patwari_gaikwad", "role": "operator"})
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "patwari_gaikwad"
    assert decoded["role"] == ROLE_OPERATOR

    user = AuthenticatedUser(decoded["sub"], decoded["role"])
    assert user.has_permission("DOCUMENT_UPLOAD")
    assert not user.has_permission("VIEW_PII")


def test_maker_checker_workflow(db_session):
    # 1. Setup Document and Task
    doc = Document(
        id="doc-test-1",
        filename="khasra.png",
        original_sha256="test_sha256_mock_hash",
        mime_type="image/png",
        file_size=10240,
        storage_path="data/storage/test.png",
        status="needs_review"
    )
    db_session.add(doc)
    field = FieldRecord(
        id="f1",
        document_id=doc.id,
        field_name="owner_name",
        value="Ram Lal",
        raw_text="राम लाल",
        confidence=0.55
    )
    db_session.add(field)
    db_session.commit()

    task = ReviewService.create_task(
        db_session,
        document_id=doc.id,
        priority="high",
        reason="Low OCR confidence on owner name",
        double_review_required=True
    )
    assert task.status == "needs_review"
    assert task.double_review_required is True

    # 2. Stage 1: Maker review submitted by Verifier
    maker_res = ReviewService.apply_human_override(
        db=db_session,
        task_id=task.id,
        field_updates={"owner_name": "Ramesh Lal"},
        reviewer_id="verifier_pooja",
        is_checker=False
    )
    assert maker_res.status == "maker_reviewed"
    assert maker_res.maker_id == "verifier_pooja"
    assert doc.status == "maker_reviewed"
    assert field.reviewed_value == "Ramesh Lal"

    # 3. Stage 2: Checker review certified by Supervisor
    checker_res = ReviewService.apply_human_override(
        db=db_session,
        task_id=task.id,
        field_updates={},
        reviewer_id="sdm_sharma",
        action="approved",
        is_checker=True
    )
    assert checker_res.status == "verified"
    assert checker_res.checker_id == "sdm_sharma"
    assert doc.status == "published"
    assert doc.overall_confidence >= 0.99


def test_cryptographic_audit_hash_chain(db_session):
    # 1. Generate chained audit events
    log1 = log_event(db_session, action="INGESTION_STARTED", document_id="doc-101")
    log2 = log_event(db_session, action="OCR_COMPLETED", document_id="doc-101")
    log3 = log_event(db_session, action="VALIDATION_FAILED", document_id="doc-101")
    log4 = log_event(db_session, action="REVIEW_SUBMITTED", document_id="doc-101")

    assert log1.previous_hash == "0000000000000000000000000000000000000000000000000000000000000000"
    assert log2.previous_hash == log1.current_hash
    assert log3.previous_hash == log2.current_hash
    assert log4.previous_hash == log3.current_hash

    # 2. Verification on unaltered chain should pass
    report = verify_audit_chain_integrity(db_session)
    assert report["chain_valid"] is True
    assert report["total_blocks"] == 4

    # 3. Tamper detection: simulate unauthorized alteration of log2
    log2.action = "UNAUTHORIZED_TAMPER"
    db_session.commit()

    tampered_report = verify_audit_chain_integrity(db_session)
    assert tampered_report["chain_valid"] is False
    assert tampered_report["broken_at_block_id"] == log2.id
    assert "Record contents modified" in tampered_report["message"]
