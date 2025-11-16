@echo off
echo ========================================
echo AI Assessment Platform - Setup Script
echo ========================================
echo.

echo Step 1: Setting up Backend...
echo.
cd backend

echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing Python dependencies...
pip install Flask Flask-CORS Flask-SQLAlchemy Flask-JWT-Extended Werkzeug
pip install google-generativeai google-auth requests
pip install opencv-python numpy Pillow
pip install nltk pdfplumber python-docx

echo.
echo Downloading NLTK data...
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

echo.
echo Creating database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created successfully!')"

cd ..

echo.
echo Step 2: Setting up Frontend...
echo.
cd frontend

echo Installing Node dependencies...
call npm install

cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo 1. Run 'start_backend.bat' in one terminal
echo 2. Run 'start_frontend.bat' in another terminal
echo 3. Open http://localhost:3000 in your browser
echo.
echo Press any key to exit...
pause > nul
