@echo off
REM PhantomSense - Start Hub Server Only
REM Starts the REST API hub on port 5000

setlocal enabledelayedexpansion

echo ================================================================
echo PhantomSense Hub Server
echo ================================================================
echo.

cd /d "%~dp0"

set "HUB_VENV=%~dp0hub\venv"

REM Check if we're in the right directory
if not exist "hub" (
    echo ERROR: hub directory not found. Please run from PhantomSense root.
    exit /b 1
)

REM Kill any existing processes on port 5000
echo Cleaning up existing processes on port 5000...
powershell -Command "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1

REM Create virtual environment if it doesn't exist
if not exist "%HUB_VENV%" (
    echo Creating Python virtual environment...
    python -m venv "%HUB_VENV%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call "%HUB_VENV%\Scripts\activate.bat"

echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo WARNING: pip upgrade failed, continuing anyway...
)

cd hub
echo Installing requirements from requirements.txt...
echo.
echo Installing pre-built packages (no compilation needed)...
echo.

REM Install critical packages with --only-binary to force pre-built wheels
pip install --only-binary=:all: numpy --quiet 2>nul
pip install --only-binary=:all: matplotlib --quiet 2>nul

REM Install remaining dependencies with preferred binary wheels
REM This will skip numpy, matplotlib since they're already installed
pip install --prefer-binary -r requirements.txt --quiet 2>nul

cd ..

REM Start Hub Server
echo.
echo ================================================================
echo Starting Hub Server...
echo ================================================================
echo.
echo Hub is running on: http://localhost:5000
echo API Endpoints:
echo   - http://localhost:5000/devices       (list connected devices)
echo   - http://localhost:5000/metrics       (aggregated metrics)
echo   - http://localhost:5000/reasoning     (LLM activity analysis)
echo   - http://localhost:5000/timeline      (activity timeline)
echo.
echo Press Ctrl+C to stop
echo.

python hub.py
