@echo off
echo ================================================
echo   Installing Advanced Face Recognition (ArcFace)
echo ================================================
echo.
echo This will install InsightFace for high-accuracy
echo face recognition using ArcFace technology.
echo.
echo System will use fallback mode if installation fails.
echo.
pause

REM Activate virtual environment
call venv\Scripts\activate.bat

echo.
echo [1/2] Installing ONNX Runtime...
pip install onnxruntime

echo.
echo [2/2] Installing InsightFace...
pip install insightface

echo.
echo ================================================
echo   Installation Complete!
echo ================================================
echo.
echo Restart the backend to use advanced face recognition.
echo.
pause
