@echo off
title BhuSetu Single-Container Docker Launcher
echo ==============================================================================
echo        Building and Launching BhuSetu Unified Docker Container
echo               Frontend + Backend + API in ONE Container
echo ==============================================================================
echo.
cd /d "%~dp0"

echo [1/2] Building single unified Docker image (this may take a couple of minutes)...
docker build -t bhusetu:latest .
if %errorlevel% neq 0 (
    echo Docker build failed! Please check if Docker Desktop is running.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/2] Running BhuSetu container on http://localhost:8000 ...
docker rm -f bhusetu_app >nul 2>&1
docker run -d -p 8000:8000 --name bhusetu_app bhusetu:latest

echo.
echo ==============================================================================
echo  BhuSetu is now live in ONE container!
echo  - Interactive Web App: http://localhost:8000
echo  - Swagger API Docs:    http://localhost:8000/docs
echo ==============================================================================
echo.
start http://localhost:8000
pause
