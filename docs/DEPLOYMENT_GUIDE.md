# BhuSetu: Complete Deployment & Networking Architecture Guide

This guide explains how **BhuSetu**'s frontend, backend, and API connect together across development and production environments, and provides step-by-step instructions for deploying to cloud providers and Docker.

---

## 1. System Architecture: How Frontend, Backend & API Connect

```
                        ┌────────────────────────────────────────────────────────┐
                        │                      Client Browser                    │
                        └───────────────────────────┬────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           Networking & Routing Layer                                           │
│                                                                                                                │
│   DEVELOPMENT MODE:                                    PRODUCTION (SINGLE CONTAINER):                          │
│   ┌───────────────────────────────────┐               ┌────────────────────────────────────────────────────┐   │
│   │ Vite Dev Server (port 5173)       │               │ FastAPI Unified Server (port 8000 / $PORT)         │   │
│   │ - Serves React TSX with HMR       │               │                                                    │   │
│   │ - Proxies /api/*   ──┐            │               │ - Serves React SPA (dist/index.html) on /          │   │
│   │ - Proxies /storage ─┐│            │               │ - Serves Static Assets on /assets/*                │   │
│   └─────────────────────┼┼────────────┘               │ - Handles API routes on /api and /api/v1           │   │
│                         ││                            │ - Handles Swagger Docs on /docs                    │   │
│                         ││                            │ - Serves Scans on /storage/*                       │   │
│                         ▼▼                            └─────────────────────────┬──────────────────────────┘   │
│               ┌───────────────────┐                                             │                              │
│               │ FastAPI (port 8000│◄────────────────────────────────────────────┘                              │
│               └─────────┬─────────┘                                                                            │
└─────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                BhuSetu Services                                                │
│                                                                                                                │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────────────┐  │
│  │ Dual OCR Engine      │  │ Cadastral GIS        │  │ Forensics Engine     │  │ Legal Validation Engine   │  │
│  │ (Gemini 2.5/Tesseract│  │ (40 Parcels GeoJSON) │  │ (ELA + Clone Mask)   │  │ (10 Configurable Rules)   │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  └───────────────────────────┘  │
│                                                   │                                                            │
│                                                   ▼                                                            │
│                                  ┌───────────────────────────────────┐                                         │
│                                  │ SQLite / PostgreSQL (PostGIS)     │                                         │
│                                  │ + SHA-256 Tamper Audit Chain      │                                         │
│                                  └───────────────────────────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Why BhuSetu Has Zero CORS Issues
In traditional multi-host setups, a frontend on `https://myfrontend.com` calling an API on `https://myapi.com` requires cross-origin headers (CORS) and preflight `OPTIONS` requests that often fail.

BhuSetu eliminates this by supporting **same-origin proxying**:
- In **Development**: The Vite frontend at `localhost:5173` forwards any request beginning with `/api/` or `/storage/` internally to `localhost:8000` via Vite's built-in proxy in `vite.config.ts`.
- In **Production (Single Container)**: The React app is compiled into `frontend/dist/`. FastAPI serves the React HTML/JS at `/` and the API at `/api/` on the exact same port. The browser never leaves the same host and port!
- In **Production (Docker Compose / Nginx)**: Nginx listens on port 80, serves the static HTML/JS directly, and reverse-proxies `/api/` to the FastAPI backend container.

---

## 2. Quick-Start Deployment Options

### Option A: Unified Single-Container Deployment (Recommended for Cloud)
This method builds the React frontend and packages it into a single Docker container with FastAPI. You only have to run **one** container on **one** port!

#### 1. Build and Run via Docker:
```bash
# Build the unified image
docker build -t bhusetu:latest .

# Run container on port 8000
docker run -d -p 8000:8000 \
  -e GEMINI_API_KEY="your_api_key_here" \
  -e MOCK_OCR_MODE="false" \
  --name bhusetu_app \
  bhusetu:latest
```
Now open:
- **Web Application**: `http://localhost:8000`
- **Swagger API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

### Option B: Multi-Container Deployment via Docker Compose
This method runs frontend (Nginx) and backend (FastAPI) as isolated services with Docker Compose.

```bash
# Start all services in the background
docker compose up --build -d

# View service logs
docker compose logs -f

# Stop all services
docker compose down
```
Ports:
- **Frontend (Nginx)**: `http://localhost:80` (or `http://localhost:3000`)
- **Backend API**: `http://localhost:8000/api`
- **API Documentation**: `http://localhost:8000/docs`

---

### Option C: Local Development Setup (Without Docker)

#### Step 1: Open PowerShell and navigate to the project directory
```powershell
cd C:\Users\angwa\.gemini\antigravity\scratch\bhusetu
```

#### Step 2: Start Backend (Terminal 1)
```powershell
# Activate virtual environment and launch Uvicorn
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Step 3: Start Frontend (Terminal 2)
```powershell
cd frontend
npm run dev -- --port 5173
```
- Frontend will open at: `http://localhost:5173`
- Backend API will run at: `http://localhost:8000`

---

## 3. Deploying to Cloud Platforms

### Deploying to Render.com (Free Tier / Starter)
1. Push your repository to GitHub or GitLab.
2. In Render Dashboard, click **New +** -> **Web Service**.
3. Connect your repository.
4. Select **Docker** as the Environment (Render detects root `Dockerfile`).
5. Set Environment Variables:
   - `MOCK_OCR_MODE` = `false`
   - `GEMINI_API_KEY` = `your_gemini_api_key`
   - `PORT` = `8000`
6. Click **Create Web Service**. Render builds the React frontend, sets up Python 3.11, and deploys the entire application on a single secure HTTPS URL (e.g. `https://bhusetu.onrender.com`).

---

### Deploying to Railway.app / Fly.io
1. Install Railway CLI: `npm i -g @railway/cli`
2. Run:
   ```bash
   railway login
   railway init
   railway up
   ```
Railway automatically discovers the root `Dockerfile` and binds to `$PORT`.

---

### Deploying to Google Cloud Run (Serverless Container)
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build container with Google Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bhusetu:latest

# Deploy to Cloud Run
gcloud run deploy bhusetu \
  --image gcr.io/YOUR_PROJECT_ID/bhusetu:latest \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your_key",MOCK_OCR_MODE="false"
```

---

### Deploying to AWS EC2 or Ubuntu VPS
1. SSH into your server:
   ```bash
   ssh ubuntu@your-server-ip
   ```
2. Clone repository & install Docker:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   git clone https://github.com/your-org/bhusetu.git
   cd bhusetu
   ```
3. Run with Docker Compose:
   ```bash
   sudo docker-compose up --build -d
   ```

---

## 4. Environment Variables Reference (`.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./bhusetu.db` | Database connection string. Use `postgresql://user:pass@host/db` for PostGIS. |
| `MOCK_OCR_MODE` | `true` | When `true`, uses synthetic golden OCR extractions. Set to `false` in production for live Gemini Vision & Tesseract. |
| `GEMINI_API_KEY` | *(empty)* | Google GenAI API key for live multimodal vision extraction. |
| `SECRET_KEY` | `bhusetu-secret-key-...` | Secret used for HMAC-SHA256 audit chaining and session signing. |
| `STORAGE_DIR` | `./data/storage` | Directory where uploaded scanned PDFs and PNGs are immutably stored. |
| `CADASTRE_GEOJSON_PATH` | `./data/cadastre/parcels.geojson` | GeoJSON file containing cadastral GIS parcel boundaries. |
| `PORT` | `8000` | Port on which the FastAPI application listens. |

---

## 5. Troubleshooting & FAQ

### Q1: "Cannot find path in PowerShell"
**Cause:** PowerShell command was executed from your home directory (`C:\Users\angwa`) instead of the project directory.
**Fix:** Always ensure your terminal is in the project directory before running commands:
```powershell
cd C:\Users\angwa\.gemini\antigravity\scratch\bhusetu
```

### Q2: "Failed to upload or digitize documents (500 Internal Server Error)"
**Fixed in current version:**
1. PIL EXIF metadata `IFDRational` objects are now automatically converted to Python native numbers before database storage.
2. Forensic flags list unpacking bug resolved in `documents.py`.
3. High-resolution PDF rendering is powered by `pypdfium2`.

### Q3: "How do I switch between Mock OCR mode and Real Gemini Vision?"
Open `.env` and set:
```ini
MOCK_OCR_MODE=false
GEMINI_API_KEY=AIzaSy...your-gemini-key
```
When `MOCK_OCR_MODE=false`, BhuSetu invokes Google Gemini 2.5 Flash for Marathi/Hindi bilingual OCR and entity extraction, with local Tesseract as fallback.
