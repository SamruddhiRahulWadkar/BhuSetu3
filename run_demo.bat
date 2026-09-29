@echo off
TITLE BhuSetu - Intelligent Land Record Digitization & Validation System
COLOR 0A

echo ===========================================================================
echo    BHUSETU: Intelligent Land Record Digitization and Validation System
echo    Smart India Hackathon Problem Statement 26018 (Dept of Land Resources)
echo ===========================================================================
echo.

if not exist .venv (
    echo [!] Virtual environment not found. Please create .venv first.
    exit /b 1
)

echo [*] Initializing demo users and verifying cryptographic audit chain...
.venv\Scripts\python demo.py

echo.
echo [*] Launching FastAPI Backend on http://localhost:8000 ...
start "BhuSetu Backend" cmd /k ".venv\Scripts\uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [*] Launching React Vite Frontend on http://localhost:5173 ...
cd frontend
start "BhuSetu Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ===========================================================================
echo [SUCCESS] Both servers are running!
echo   Frontend URL:  http://localhost:5173
echo   API Docs URL:  http://localhost:8000/docs
echo   Demo Script:   docs/DEMO_SCRIPT.md
echo ===========================================================================
echo Press any key to exit this launcher window (servers will continue in separate windows).
pause > nul
