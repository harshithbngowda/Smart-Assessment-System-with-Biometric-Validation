@echo off
echo ========================================
echo Starting Backend Server...
echo ========================================
echo.

cd backend
call venv\Scripts\activate
echo Backend running on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
