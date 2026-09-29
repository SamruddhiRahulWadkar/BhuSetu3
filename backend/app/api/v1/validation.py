from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.validation import ValidationResult
from backend.app.validation.engine import LegalLogicValidationEngine

router = APIRouter(prefix="/validation", tags=["Validation"])
engine = LegalLogicValidationEngine()


@router.get("/rules")
def list_rules():
    """Lists all configured legal validation rules."""
    engine.load_all_rules()
    return list(engine.rules.values())


@router.get("/results/{document_id}")
def get_validation_results(document_id: str, db: Session = Depends(get_db)):
    """Retrieves all validation rule executions and evidence for a document."""
    results = db.query(ValidationResult).filter(ValidationResult.document_id == document_id).all()
    return [r.to_dict() for r in results]
