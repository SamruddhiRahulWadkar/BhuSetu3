from fastapi import APIRouter
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.validation import router as validation_router
from backend.app.api.v1.ownership import router as ownership_router
from backend.app.api.v1.geo import router as geo_router
from backend.app.api.v1.forensics import router as forensics_router
from backend.app.api.v1.review import router as review_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.parcels import router as parcels_router
from backend.app.api.v1.records import router as records_router
from backend.app.api.v1.integration import router as integration_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(validation_router)
api_router.include_router(ownership_router)
api_router.include_router(geo_router)
api_router.include_router(parcels_router)
api_router.include_router(records_router)
api_router.include_router(integration_router)
api_router.include_router(forensics_router)
api_router.include_router(review_router)
api_router.include_router(audit_router)
api_router.include_router(analytics_router)
api_router.include_router(admin_router)
