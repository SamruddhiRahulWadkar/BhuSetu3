import os
import time
import json
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.config import settings
from backend.app.database import engine, Base, get_db
from backend.app.api.router import api_router
from backend.app.auth.rate_limit import RateLimitMiddleware

start_time = time.time()

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Ensure storage directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "originals"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "processed"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "pages"), exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BhuSetu: Intelligent Land Record Digitization and Validation System for SIH Problem Statement 26018 (Dept of Land Resources, Govt of India)",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=240)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for document image viewing
if os.path.exists(settings.STORAGE_DIR):
    app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint providing DB connectivity and service status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "uptime_seconds": round(time.time() - start_time, 2),
        "mock_ocr_mode": settings.MOCK_OCR_MODE,
        "timestamp": time.time(),
    }


# Include API Routers under both /api and /api/v1
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


def export_openapi_json(output_path: str = "docs/openapi.json"):
    """Exports OpenAPI specification schema to static JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    schema = app.openapi()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    return output_path


# Single-Port Unified Production Deployment Support
# If the React frontend has been built into frontend/dist, serve it directly
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    from fastapi.responses import FileResponse
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Don't intercept api or docs calls
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("storage"):
            return None
        candidate = os.path.join(frontend_dist, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"service": "BhuSetu API", "status": "online"}

