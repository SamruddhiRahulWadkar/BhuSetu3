# BhuSetu: Intelligent Land Record Digitization and Validation System

**Smart India Hackathon (SIH) Problem Statement 26018**  
*Department of Land Resources (DoLR), Ministry of Rural Development, Government of India*

---

## Overview

**BhuSetu** ("Bridge of Land") is an end-to-end AI-powered system designed to modernize and secure India's land administration. It digitizes multilingual physical records (Khatauni / 7-12 extract, Mutation Register, and Sale Deed summaries in Hindi, Marathi, and English), normalizes regional revenue terminology, assesses document damage, applies calibrated confidence scoring, cross-validates records with legal/cadastral logic, and detects document forgery.

---

## Architectural Pipeline

```
1. INGESTION & STORAGE
   ├── Bulk PDF / PNG / JPG Upload
   ├── SHA-256 Immutable Content Hashing
   └── Audit Log Event Generation

2. PREPROCESSING & DAMAGE ASSESSMENT
   ├── Deskew, Denoise, CLAHE Contrast Normalization
   ├── Adaptive Binarization & Border Removal
   ├── Per-Tile Quality Metrics (Blur, Fade, Contrast, Stains, Tears)
   └── Document & Layout Classification (Tables vs Handwritten)

3. MULTILINGUAL OCR & EXTRACTION
   ├── Engine A: Google Gemini 2.5 Flash Vision (Strict Pydantic JSON Schema)
   ├── Engine B: Local Pytesseract (Hindi, Marathi, English)
   ├── Cross-Engine Agreement Analysis
   └── Mock Mode fallback for offline operation

4. REGIONAL NORMALIZATION
   ├── Synonym Mapping (Khasra / Gata / Survey No / गट क्रमांक -> Canonical)
   ├── Land Classification Taxonomies (सिंचित, जिरायत, बंजर, etc.)
   ├── State-Aware Area Unit Conversion (Bigha, Guntha, Acre -> Sqm & Hectares)
   ├── Indic Numeral Normalization (Devanagari/Gujarati -> ASCII)
   └── RapidFuzz Latin & Devanagari Name Matching

5. DAMAGE-AWARE CONFIDENCE SCORING
   ├── Calibration (OCR confidence, engine agreement, format, local damage penalty)
   └── Intelligent Routing Policy:
       ├── Score >= 0.90 -> Auto-Accept
       ├── Score 0.60 - 0.89 -> Flagged Field Human Review
       └── Score < 0.60 or Critical Failure -> Full Document Review

6. LEGAL LOGIC & FORENSIC VALIDATION
   ├── Configurable YAML Rules Engine (Advisory Legal Rules)
   ├── Share sum = 1.0 (100%) validation
   ├── Temporal ordering: Registration Date <= Mutation Date
   ├── Post-mortem transaction block & Minor guardian checks
   ├── Land ceiling limits & Agricultural -> NA conversion permits
   ├── Spatial Area Cross-check (Cadastral GeoJSON vs Textual Area)
   └── Forensics: Overwritten digits, font mismatch, pasted stamps

7. INTERACTIVE REPOSITORIES & HUMAN REVIEW
   ├── Side-by-Side Document Image Viewer with Bounding Box overlays
   ├── Interactive Cadastral Leaflet Map with ULPIN polygons
   ├── Ownership Mutation Timeline & Ancestral Chain Graph
   └── Executive SIH Analytics Dashboard & Tamper-evident Audit Trails
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Tesseract OCR installed with Indic language packs

### Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Start backend server:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Check backend health:
   ```
   http://localhost:8000/health
   http://localhost:8000/docs
   ```

### Frontend Setup
1. Navigate to `/frontend` and install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Run development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:3000` in your browser.

---

## Disclaimer
All legal and revenue validation rules implemented within BhuSetu are illustrative and advisory, not legal advice. They assist revenue officers and land registry personnel in accelerating verification while preserving rigorous human-in-the-loop oversight.
