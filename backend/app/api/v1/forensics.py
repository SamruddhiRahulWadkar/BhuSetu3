from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.forensic import ForensicFlag

router = APIRouter(prefix="/forensics", tags=["Forensics"])


@router.get("/document/{document_id}")
def get_document_forensic_flags(document_id: str, db: Session = Depends(get_db)):
    """Retrieves all forensic tampering flags detected for a document."""
    flags = db.query(ForensicFlag).filter(ForensicFlag.document_id == document_id).all()
    return [
        {
            "id": f.id,
            "document_id": f.document_id,
            "flag_type": f.flag_type,
            "severity": f.severity,
            "bbox": f.bbox,
            "confidence": f.confidence,
            "description": f.description,
            "evidence": f.evidence,
            "created_at": f.created_at.isoformat() if f.created_at else None
        }
        for f in flags
    ]
