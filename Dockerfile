# ==============================================================================
# BhuSetu Unified Single-Container Production Dockerfile
# Serves React Frontend SPA + FastAPI Backend on a Single Port ($PORT / 8000)
# Perfect for: Render, Railway, Fly.io, AWS App Runner, Google Cloud Run
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React + Vite Frontend
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Python 3.11 Runtime + FastAPI Backend
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install OCR & image system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

# Copy backend code, data, and configs
COPY backend /app/backend
COPY data /app/data
COPY .env.example /app/.env

# Copy compiled React frontend bundle from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Ensure storage directories exist
RUN mkdir -p /app/data/storage/originals /app/data/storage/processed /app/data/storage/pages

EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
