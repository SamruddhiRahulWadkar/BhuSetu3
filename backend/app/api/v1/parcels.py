from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.document import Document
from backend.app.models.field import FieldRecord
from backend.app.integration.cadastral_adapter import CadastralGISAdapter
from backend.app.auth.security import get_current_user, AuthenticatedUser, mask_name

router = APIRouter(prefix="/parcels", tags=["Parcels & ULPIN"])
cadastral_adapter = CadastralGISAdapter()


@router.get("/{ulpin}")
def get_parcel_by_ulpin(
    ulpin: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Looks up a cadastral parcel by its 14-digit ULPIN (Bhu-Aadhaar).
    Returns GeoJSON polygon geometry, boundary attributes, and linked digitized record status.
    Applies PII masking on owner names for unauthorized roles.
    """
    parcel = cadastral_adapter.get_parcel_by_ulpin(ulpin)
    if not parcel:
        raise HTTPException(
            status_code=404,
            detail=f"Parcel with ULPIN '{ulpin}' not found in cadastral GIS registry"
        )

    props = dict(parcel.get("properties", {}))
    survey_no = props.get("survey_no")
    village = props.get("village")

    # Cross-reference with digitized database records
    matched_doc = None
    if survey_no and village:
        # Search documents with matching survey_no
        field_match = db.query(FieldRecord).filter(
            FieldRecord.field_name.in_(["survey_or_khasra_no", "survey_no", "khasra_no"]),
            FieldRecord.value == str(survey_no)
        ).first()
        if field_match:
            doc = db.query(Document).filter(Document.id == field_match.document_id).first()
            if doc:
                # Find owner name in document
                owner_field = db.query(FieldRecord).filter(
                    FieldRecord.document_id == doc.id,
                    FieldRecord.field_name.in_(["owner_name", "khatadar_name"])
                ).first()
                owner_name = owner_field.value if owner_field else "Government / Unknown"

                has_pii = current_user.has_permission("VIEW_PII")
                if not has_pii and owner_name:
                    owner_name = mask_name(str(owner_name))

                matched_doc = {
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status,
                    "overall_confidence": doc.overall_confidence,
                    "doc_type": doc.doc_type,
                    "recorded_owner": owner_name
                }

    response_feature = {
        "type": "Feature",
        "properties": {
            **props,
            "digitized_record": matched_doc,
            "verification_status": matched_doc["status"] if matched_doc else "unlinked",
            "bhu_aadhaar_standard": "ISO 19152 LADM / DoLR"
        },
        "geometry": parcel.get("geometry")
    }

    return response_feature


@router.get("/")
def list_parcels(
    village: Optional[str] = Query(None, description="Filter parcels by village name"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Lists cadastral parcels in GeoJSON format, optionally filtered by village."""
    if village:
        return cadastral_adapter.query_parcels_by_village(village)
    return cadastral_adapter.get_all_parcels()
