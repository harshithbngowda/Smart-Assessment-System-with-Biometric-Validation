# AI Assessment Platform - PowerShell Startup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Assessment Platform - Starting System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check prerequisites
if (-not (Test-Command "python")) {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

if (-not (Test-Command "npm")) {
    Write-Host "Error: Node.js/npm is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Installing Backend Dependencies..." -ForegroundColor Yellow
Set-Location backend

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv venv
}

# Activate virtual environment and install dependencies
& "venv\Scripts\Activate.ps1"
pip install -r requirements.txt
Write-Host "Backend dependencies installed!" -ForegroundColor Green
Write-Host ""

Write-Host "[2/4] Starting Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; python app.py"
Write-Host "Backend server starting on http://localhost:5000" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] Installing Frontend Dependencies..." -ForegroundColor Yellow
Set-Location ..\frontend

# Install Node.js dependencies if node_modules doesn't exist
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Green
    npm install
}
Write-Host "Frontend dependencies installed!" -ForegroundColor Green
Write-Host ""

Write-Host "[4/4] Starting Frontend Development Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
Write-Host "Frontend server starting on http://localhost:5173" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "System Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: http://localhost:5000" -ForegroundColor White
Write-Host "Frontend App: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
