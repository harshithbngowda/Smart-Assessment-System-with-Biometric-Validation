@echo off
echo ============================================================
echo   Biometric Anti-Cheating Assessment System
echo ============================================================
echo.
echo Starting application...
echo.

cd /d "%~dp0"
python main.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Failed to start application
    echo ============================================================
    echo.
    echo Possible solutions:
    echo 1. Make sure Python is installed
    echo 2. Install requirements: pip install -r requirements.txt
    echo 3. Check if camera is connected
    echo.
    pause
)
