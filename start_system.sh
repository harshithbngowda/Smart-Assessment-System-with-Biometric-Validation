#!/bin/bash

# AI Assessment Platform - Linux/Mac Startup Script

echo "========================================"
echo "AI Assessment Platform - Starting System"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: Node.js/npm is not installed or not in PATH${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites check passed!${NC}"
echo ""

# Step 1: Backend Setup
echo -e "${YELLOW}[1/4] Installing Backend Dependencies...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt
echo -e "${GREEN}Backend dependencies installed!${NC}"
echo ""

# Step 2: Start Backend Server
echo -e "${YELLOW}[2/4] Starting Backend Server...${NC}"
# Start backend in background
nohup python app.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
echo -e "${GREEN}Backend server starting on http://localhost:5000${NC}"
echo ""

# Step 3: Frontend Setup
echo -e "${YELLOW}[3/4] Installing Frontend Dependencies...${NC}"
cd ../frontend

# Install Node.js dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${GREEN}Installing Node.js dependencies...${NC}"
    npm install
fi
echo -e "${GREEN}Frontend dependencies installed!${NC}"
echo ""

# Step 4: Start Frontend Server
echo -e "${YELLOW}[4/4] Starting Frontend Development Server...${NC}"
# Start frontend in background
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
echo -e "${GREEN}Frontend server starting on http://localhost:5173${NC}"
echo ""

# Wait a moment for servers to start
sleep 3

# Check if servers are running
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend server is running (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}✗ Backend server failed to start${NC}"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend server is running (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}✗ Frontend server failed to start${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}System Started Successfully!${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}Backend API: http://localhost:5000${NC}"
echo -e "${BLUE}Frontend App: http://localhost:5173${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend: tail -f backend.log"
echo -e "  Frontend: tail -f frontend.log"
echo ""
echo -e "${YELLOW}To stop the system:${NC}"
echo -e "  ./stop_system.sh"
echo ""
echo -e "${YELLOW}Press Ctrl+C to exit this script (servers will continue running)${NC}"

# Keep script running and show logs
tail -f backend.log frontend.log
