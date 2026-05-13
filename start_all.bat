@echo off
REM PhantomSense - Start Hub + Desktop GUI + LLM Processing
REM This script launches all components needed for the system to run

setlocal enabledelayedexpansion

echo ================================================================
echo PhantomSense - Starting All Services
echo ================================================================
echo.
echo This will start:
echo  1. Hub Server (REST API on port 5000)
echo  2. Desktop GUI (PyQt6 visualization)
echo  3. LLM Processing Service (via Ollama)
echo.

cd /d "%~dp0"

set "HUB_VENV=%~dp0hub\venv"

REM Check if we're in the right directory
if not exist "hub" (
    echo ERROR: hub directory not found. Please run from PhantomSense root.
    exit /b 1
)

REM Kill any existing processes on port 5000 (hub)
echo Cleaning up existing processes on port 5000...
powershell -Command "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1

REM Create virtual environment if it doesn't exist
if not exist "%HUB_VENV%" (
    echo Creating Python virtual environment in hub/venv...
    python -m venv "%HUB_VENV%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install dependencies
echo.
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
pip install --only-binary=:all: PyQt6 --quiet 2>nul

REM Install remaining dependencies with preferred binary wheels
REM This will skip numpy, matplotlib, PyQt6 since they're already installed
pip install --prefer-binary -r requirements.txt --quiet 2>nul

cd ..

REM Start Hub Server in a new terminal window
echo.
echo ================================================================
echo Starting Hub Server on http://localhost:5000
echo ================================================================
start "PhantomSense Hub" cmd /k "cd hub && ""%HUB_VENV%\Scripts\activate.bat"" && python hub.py"

REM Give hub time to start
timeout /t 3 /nobreak

REM Start Desktop GUI in a new terminal window
echo.
echo ================================================================
echo Starting Desktop GUI Application
echo ================================================================
start "PhantomSense Desktop GUI" cmd /k "cd hub && ""%HUB_VENV%\Scripts\activate.bat"" && python phantomsense_desktop.py"

REM Display system info
echo.
echo ================================================================
echo System Started!
echo ================================================================
echo.
echo Hub Server:        http://localhost:5000
echo GUI:               Running in separate window
echo Ollama LLM:        http://localhost:11434 (if running)
echo.
echo To monitor devices:
echo   http://localhost:5000/devices
echo.
echo To check hub metrics:
echo   http://localhost:5000/metrics
echo.
echo Press Ctrl+C in any window to stop that service
echo.
pause
