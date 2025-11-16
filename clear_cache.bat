@echo off
echo Clearing Python cache files...
del /s /q mptrial\__pycache__\*.pyc 2>nul
del /s /q backend\__pycache__\*.pyc 2>nul
rmdir /s /q mptrial\__pycache__ 2>nul
rmdir /s /q backend\__pycache__ 2>nul
echo Cache cleared!
echo.
echo Now restart the backend:
echo   python backend\app.py
pause
