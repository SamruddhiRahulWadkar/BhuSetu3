import io
import csv
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.document import Document
from backend.app.models.field import FieldRecord
from backend.app.models.parcel import ParcelRecord
from backend.app.integration.cadastral_adapter import CadastralGISAdapter
from backend.app.auth.security import get_current_user, AuthenticatedUser, mask_name, mask_id_number

router = APIRouter(prefix="/records", tags=["Records & Export"])
cadastral_adapter = CadastralGISAdapter()


@router.get("/export")
def export_land_records(
    format: str = Query("json", pattern="^(json|csv|geojson)$", description="Export format: json, csv, or geojson"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. published, needs_review)"),
    doc_type: Optional[str] = Query(None, description="Filter by doc_type"),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Exports digitized land records in JSON, CSV, or GeoJSON formats.
    Complies with DoLR data sharing protocols: automatically masks PII for unauthorized users.
    """
    query = db.query(Document)
    if status:
        query = query.filter(Document.status == status)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)

    docs = query.order_by(Document.created_at.desc()).all()
    has_pii = current_user.has_permission("VIEW_PII")

    # Assemble structured records
    records: List[Dict[str, Any]] = []
    for d in docs:
        fields = db.query(FieldRecord).filter(FieldRecord.document_id == d.id).all()
        f_map = {f.field_name: f.value for f in fields}

        owner = f_map.get("owner_name") or f_map.get("khatadar_name") or "Unknown"
        if not has_pii and owner != "Unknown":
            owner = mask_name(str(owner))

        survey_no = f_map.get("survey_or_khasra_no") or f_map.get("survey_no") or f_map.get("khasra_no") or ""
        ulpin = f_map.get("ulpin") or ""
        village = f_map.get("village") or ""
        area_sqm = f_map.get("area_sqm") or f_map.get("plot_area_sqm") or ""
        land_type = f_map.get("land_type") or f_map.get("land_class") or ""

        rec = {
            "document_id": d.id,
            "filename": d.filename,
            "doc_type": d.doc_type,
            "status": d.status,
            "overall_confidence": d.overall_confidence,
            "ulpin": ulpin,
            "survey_no": survey_no,
            "village": village,
            "owner_name": owner,
            "area_sqm": area_sqm,
            "land_type": land_type,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        records.append(rec)

    # 1. Format: CSV
    if format == "csv":
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
            writer.writeheader()
            for r in records:
                writer.writerow(r)
        return PlainTextResponse(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=bhusetu_land_records.csv"}
        )

    # 2. Format: GeoJSON
    elif format == "geojson":
        features = []
        all_parcels = cadastral_adapter.get_all_parcels().get("features", [])
        for r in records:
            matched_geom = None
            survey = str(r["survey_no"]).strip()
            # Match parcel geometry from cadastral layer
            for p in all_parcels:
                props = p.get("properties", {})
                if str(props.get("survey_no", "")).strip() == survey or (r["ulpin"] and props.get("ulpin") == r["ulpin"]):
                    matched_geom = p.get("geometry")
                    break

            feat = {
                "type": "Feature",
                "properties": r,
                "geometry": matched_geom or {
                    "type": "Point",
                    "coordinates": [73.9785, 18.5795]  # Default cadastral reference centroid
                }
            }
            features.append(feat)

        geojson_coll = {
            "type": "FeatureCollection",
            "name": "BhuSetu_Digitized_Records_GIS",
            "features": features
        }
        return Response(
            content=json.dumps(geojson_coll, indent=2, ensure_ascii=False),
            media_type="application/geo+json",
            headers={"Content-Disposition": "attachment; filename=bhusetu_land_records.geojson"}
        )

    # 3. Format: JSON (Default)
    return {
        "total_records": len(records),
        "exported_at": docs[0].created_at.isoformat() if docs else None,
        "pii_masked": not has_pii,
        "records": records
    }
