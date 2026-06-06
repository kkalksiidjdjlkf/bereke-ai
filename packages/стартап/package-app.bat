@echo off
REM Wellbeing Monitor - Quick Package Creator (Windows Version)
REM Creates a distributable package in seconds

cls

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║       Wellbeing Monitor - Quick Package Creator           ║
echo ║                   Windows Version                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Get current date
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set DATE=%%c-%%a-%%b)
set VERSION=2.0

echo Choose packaging method:
echo.
echo 1. ZIP File (Easiest - 1 min)
echo 2. Exit
echo.
set /p choice="Select (1-2): "

if "%choice%"=="1" (
    echo.
    echo Creating ZIP file...
    
    REM Create packages directory
    if not exist packages mkdir packages
    
    REM Create ZIP file using Windows built-in compress
    REM Note: Windows might not have 7z, so we use PowerShell
    set ZIP_NAME=packages\wellbeing-monitor-%VERSION%-%DATE%.zip
    
    powershell -Command "Compress-Archive -Path @('app*.py', '*.html', '*.md', '*.sh', '*.bat', '*.txt', '*.yml', 'Dockerfile', 'Makefile', '*_analyzer.py', 'database*.py', 'wellbeing_monitor.py', 'config.py', 'examples.py', 'validate_setup.py', 'query_database.py') -DestinationPath '%ZIP_NAME%' -Force"
    
    echo.
    echo ✓ ZIP created successfully!
    echo.
    echo File: %ZIP_NAME%
    echo.
    echo Ready to share! You can:
    echo   - Email it to friends
    echo   - Upload to Google Drive
    echo   - Put on USB drive
    echo   - Share via WeTransfer
    echo.
    echo To use:
    echo   1. Extract ZIP file
    echo   2. Double-click app-start.sh (or run in command prompt)
    echo   3. Select option 3
    echo   4. Wait for dashboard to open
    
) else if "%choice%"=="2" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid option
    exit /b 1
)

echo.
echo ═════════════════════════════════════════════════════════════
echo.
echo For more options (Docker, etc), see: HOW_TO_DOWNLOAD_AS_APP.md
echo.

pause
