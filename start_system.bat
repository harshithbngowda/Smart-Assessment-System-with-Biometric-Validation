@echo off
echo ========================================
echo AI Assessment Platform - Starting System
echo ========================================
echo.

echo [1/4] Installing Backend Dependencies...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
echo Backend dependencies installed!
echo.

echo [2/4] Starting Backend Server...
start "Backend Server" cmd /k "cd backend && call venv\Scripts\activate && python app.py"
echo Backend server starting on http://localhost:5000
echo.

echo [3/4] Installing Frontend Dependencies...
cd ..\frontend
if not exist node_modules (
    echo Installing Node.js dependencies...
    npm install
)
echo Frontend dependencies installed!
echo.

echo [4/4] Starting Frontend Development Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"
echo Frontend server starting on http://localhost:5173
echo.

echo ========================================
echo System Started Successfully!
echo ========================================
echo.
echo Backend API: http://localhost:5000
echo Frontend App: http://localhost:5173
echo.
echo Press any key to exit...
pause > nul
