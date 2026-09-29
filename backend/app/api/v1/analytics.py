from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.analytics.metrics import get_dashboard_metrics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard_stats(db: Session = Depends(get_db)):
    """Provides high-level operational SIH metrics for executive dashboard."""
    return get_dashboard_metrics(db)
