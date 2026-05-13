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
pip install --upgrade --prefer-binary -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo.
    echo Troubleshooting:
    echo - Ensure you have Python 3.10+ installed
    echo - Check your internet connection
    echo - Try: pip install numpy --prefer-binary
    echo.
    pause
    exit /b 1
)
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
