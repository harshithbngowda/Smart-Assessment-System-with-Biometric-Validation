@echo off
echo ========================================
echo Restarting Backend with Correct Database
echo ========================================
echo.
echo Step 1: Stopping any running Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Copying database from instance folder...
python backend\copy_db.py

echo.
echo Step 3: Starting backend...
cd backend
start cmd /k python app.py

echo.
echo ✅ Backend restarted!
echo.
pause
