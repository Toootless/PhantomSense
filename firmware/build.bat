@echo off
REM PhantomSense Firmware Build Script for Windows
REM Supports building and flashing for multiple units

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Default values
set UNIT_ID=1
set ACTION=build
set PORT=

:parse_args
if "%1"=="" goto start_build
if "%1"=="-u" (
    set UNIT_ID=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--unit" (
    set UNIT_ID=%2
    shift
    shift
    goto parse_args
)
if "%1"=="-a" (
    set ACTION=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--action" (
    set ACTION=%2
    shift
    shift
    goto parse_args
)
if "%1"=="-p" (
    set PORT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--port" (
    set PORT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help
goto start_build

:show_help
echo PhantomSense Firmware Build Script
echo.
echo Usage: %0 [OPTIONS]
echo.
echo OPTIONS:
echo     -u, --unit UNIT_ID      Unit ID to build for (1 or 2, default: 1)
echo     -a, --action ACTION     Action: build, flash, monitor, fullbuild (default: build)
echo     -p, --port PORT         Serial port for flashing (default: auto-detect)
echo     -h, --help              Show this help message
echo.
echo EXAMPLES:
echo     %0 -u 1
echo     %0 -u 2 -a fullbuild
echo     %0 -u 1 -a monitor
exit /b 0

:start_build
echo ========================================
echo Configuring for Unit %UNIT_ID%
echo ========================================

REM Validate unit ID
if not "%UNIT_ID%"=="1" if not "%UNIT_ID%"=="2" (
    echo ERROR: Invalid unit ID: %UNIT_ID% (must be 1 or 2)
    exit /b 1
)

REM Update unit selection
set UNIT_MACRO=UNIT_ID_%UNIT_ID%
echo Updating CURRENT_UNIT_ID to %UNIT_MACRO%

REM Set IDF target
echo Setting IDF target to esp32s3
call idf.py set-target esp32s3
if errorlevel 1 exit /b 1

REM Handle actions
if "%ACTION%"=="build" (
    echo ========================================
    echo Building firmware for Unit %UNIT_ID%
    echo ========================================
    call idf.py build
    if errorlevel 1 exit /b 1
) else if "%ACTION%"=="fullbuild" (
    echo ========================================
    echo Full rebuild and flash for Unit %UNIT_ID%
    echo ========================================
    call idf.py fullclean
    call idf.py build
    if errorlevel 1 exit /b 1
    if "%PORT%"=="" (
        call idf.py flash
    ) else (
        call idf.py -p %PORT% flash
    )
    if errorlevel 1 exit /b 1
) else if "%ACTION%"=="flash" (
    echo ========================================
    echo Flashing firmware for Unit %UNIT_ID%
    echo ========================================
    if "%PORT%"=="" (
        call idf.py flash
    ) else (
        call idf.py -p %PORT% flash
    )
    if errorlevel 1 exit /b 1
) else if "%ACTION%"=="monitor" (
    echo ========================================
    echo Monitoring Unit %UNIT_ID%
    echo ========================================
    if "%PORT%"=="" (
        call idf.py monitor
    ) else (
        call idf.py -p %PORT% monitor
    )
) else (
    echo ERROR: Unknown action: %ACTION%
    exit /b 1
)

echo ========================================
echo Done!
echo ========================================
endlocal
