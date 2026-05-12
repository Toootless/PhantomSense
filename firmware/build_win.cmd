@echo off
REM PhantomSense Build Script for Windows with proper environment setup
setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Set required environment variables
set IDF_PATH=C:\Espressif\esp-idf
set IDF_TOOLS_PATH=C:\Users\%USERNAME%\.espressif

REM Add tools to PATH
set PATH=C:\Espressif\tools\python\v6.0.1\venv\Scripts;%PATH%
set PATH=C:\Espressif\tools\idf-exe\1.0.3;%PATH%
set PATH=C:\Espressif\tools\cmake\4.0.3\bin;%PATH%
set PATH=C:\Espressif\tools\ninja\1.12.1;%PATH%
set PATH=C:\Espressif\tools\xtensa-esp32s3-elf\esp-2022r1-11.2.0\bin;%PATH%

REM Run the build
echo IDF_PATH=%IDF_PATH%
echo.
echo Building project...
python.exe "%IDF_PATH%\tools\idf.py" build

pause
