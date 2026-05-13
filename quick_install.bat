@echo off
REM PhantomSense Quick Install - Uses pre-built binaries only
REM For Windows systems without C compiler/build tools

setlocal enabledelayedexpansion

echo ================================================================
echo PhantomSense - Quick Install (Pre-built Binaries Only)
echo ================================================================
echo.
echo This script uses only pre-built Python wheels (no compilation needed)
echo.

cd /d "%~dp0"

set "HUB_VENV=%~dp0hub\venv"

if not exist "hub" (
    echo ERROR: hub directory not found.
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

call "%HUB_VENV%\Scripts\activate.bat"

echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 echo WARNING: pip upgrade had issues, continuing...

cd hub

echo.
echo Installing pre-built dependencies (this may take 2-3 minutes)...
echo.

REM Install packages one by one with --only-binary to avoid source compilation
pip install --only-binary=:all: numpy 2>/nul
pip install --only-binary=:all: paho-mqtt 2>/nul
pip install --only-binary=:all: matplotlib 2>/nul
pip install --only-binary=:all: PyQt6 2>/nul
pip install --only-binary=:all: fastapi 2>/nul
pip install --only-binary=:all: uvicorn 2>/nul
pip install --only-binary=:all: requests 2>/nul
pip install --only-binary=:all: psutil 2>/nul

echo.
echo Installing remaining dependencies...
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo.
    echo WARNING: Some packages may have failed to install.
    echo.
    echo Continuing anyway - core functionality may work.
    echo.
)

echo.
echo ================================================================
echo Installation Complete!
echo ================================================================
echo.
echo To start the hub:
echo   .\start_hub.bat
echo.
echo To start the GUI:
echo   .\start_gui.bat
echo.
echo To start everything:
echo   .\start_all.bat
echo.
pause
