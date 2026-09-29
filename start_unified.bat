@echo off
title BhuSetu Unified Single-Port Application Launcher
echo ==============================================================================
echo                BHUSETU (भू-सेतु) - UNIFIED LAUNCHER
echo    Smart India Hackathon 2024 - Problem Statement 26018 (Dept of Land Resources)
echo ==============================================================================
echo.
cd /d "%~dp0"

echo [1/3] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo Error: .venv not found. Please create it or install requirements.
    pause
    exit /b 1
)

echo [2/3] Checking frontend production build...
if not exist "frontend\dist\index.html" (
    echo Frontend build not found. Compiling React + Vite bundle...
    cd frontend
    call npm ci
    call npm run build
    cd ..
) else (
    echo Frontend bundle found in frontend\dist.
)

echo [3/3] Launching BhuSetu Unified Server on http://localhost:8000 ...
echo.
echo ==============================================================================
echo  UNIFIED ACCESS URLs (ALL IN ONE ON PORT 8000):
echo  - Interactive Web App (UI): http://localhost:8000
echo  - Interactive Swagger API:  http://localhost:8000/docs
echo  - System Health Check:      http://localhost:8000/health
echo ==============================================================================
echo.

start http://localhost:8000

.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
pause
