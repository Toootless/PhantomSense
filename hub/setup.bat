@echo off
REM PhantomSense Hub - Setup Script for Franklin (Windows)

setlocal enabledelayedexpansion

echo ==============================================================
echo PhantomSense Hub Setup (Franklin - Windows)
echo ==============================================================

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python version: %PYTHON_VERSION%

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

REM Setup environment
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env
    echo ⚠ Please edit .env with your configuration
)

REM Create data directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo ==============================================================
echo Setup Complete!
echo ==============================================================
echo.
echo Next steps:
echo 1. Edit .env with your configuration
echo 2. Ensure MQTT broker is running:
echo    - Local: mosquitto -d (or use Mosquitto installer)
echo    - Remote: Update MQTT_BROKER_HOST in .env
echo 3. Ensure Ollama is running:
echo    - Start Ollama application
echo 4. Start the hub:
echo    - venv\Scripts\activate.bat
echo    - python hub.py
echo.
echo API will be available at: http://localhost:5000
echo Swagger docs at: http://localhost:5000/docs
echo.
