@echo off
echo ========================================
echo AI Assessment Platform
echo ========================================
echo.
echo Starting Backend and Frontend...
echo.

start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && python app.py"
timeout /t 3 /nobreak > nul

start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Close this window when you're done.
echo.

pause
