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
pip install --upgrade --prefer-binary -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo.
    echo Troubleshooting:
    echo - Ensure you have Python 3.10+ installed
    echo - Check your internet connection
    echo - Try: pip install PyQt6 --prefer-binary
    echo.
    pause
    exit /b 1
)
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
