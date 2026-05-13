@echo off
REM PhantomSense - Start Desktop GUI Only
REM Launches the PyQt6 visualization and data monitoring interface

setlocal enabledelayedexpansion

echo ================================================================
echo PhantomSense Desktop GUI
echo ================================================================
echo.

cd /d "%~dp0"

set "HUB_VENV=%~dp0hub\venv"

REM Check if we're in the right directory
if not exist "hub" (
    echo ERROR: hub directory not found. Please run from PhantomSense root.
    exit /b 1
)

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
pip install --only-binary=:all: PyQt6 --quiet 2>nul

REM Install remaining dependencies with preferred binary wheels
REM This will skip numpy, matplotlib, PyQt6 since they're already installed
pip install --prefer-binary -r requirements.txt --quiet 2>nul

cd ..

REM Start Desktop GUI
echo.
echo ================================================================
echo Launching Desktop GUI...
echo ================================================================
echo.
echo The PyQt6 application window will open.
echo Make sure the Hub Server is running first (use start_hub.bat)
echo.
echo Connecting to Hub on http://localhost:5000...
echo Press Ctrl+C to stop
echo.

python phantomsense_desktop.py
