@echo off
echo ===============================================
echo   AI Assessment Platform - Complete System
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16 or higher from nodejs.org
    pause
    exit /b 1
)

echo [1/6] Setting up Backend...
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/Update dependencies
echo Installing backend dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create database if it doesn't exist
echo Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"

REM Start backend in a new window
echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate.bat && python app.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

cd ..

echo.
echo [2/6] Setting up Frontend...
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
) else (
    echo Frontend dependencies already installed.
)

REM Start frontend in a new window
echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && npm run dev"

cd ..

echo.
echo ===============================================
echo   System Started Successfully!
echo ===============================================
echo.
echo Backend API:  http://localhost:5000
echo Frontend App: http://localhost:5173
echo.
echo IMPORTANT NOTES:
echo - Keep both terminal windows open
echo - Access the app at http://localhost:5173
echo - Admin login: admin / admin123
echo - Press Ctrl+C in each window to stop servers
echo.
echo Waiting 3 seconds before opening browser...
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:5173

echo.
echo Press any key to exit this setup window...
echo (The backend and frontend will continue running)
pause >nul
