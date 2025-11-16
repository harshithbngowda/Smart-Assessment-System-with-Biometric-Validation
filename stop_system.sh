#!/bin/bash

# AI Assessment Platform - Stop System Script

echo "========================================"
echo "AI Assessment Platform - Stopping System"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop Backend Server
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo -e "${YELLOW}Stopping backend server (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        echo -e "${GREEN}✓ Backend server stopped${NC}"
    else
        echo -e "${YELLOW}Backend server was not running${NC}"
    fi
    rm -f backend.pid
else
    echo -e "${YELLOW}No backend PID file found${NC}"
fi

# Stop Frontend Server
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${YELLOW}Stopping frontend server (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        echo -e "${GREEN}✓ Frontend server stopped${NC}"
    else
        echo -e "${YELLOW}Frontend server was not running${NC}"
    fi
    rm -f frontend.pid
else
    echo -e "${YELLOW}No frontend PID file found${NC}"
fi

# Kill any remaining processes on the ports
echo -e "${YELLOW}Cleaning up any remaining processes...${NC}"

# Kill processes on port 5000 (backend)
if lsof -ti:5000 > /dev/null 2>&1; then
    echo -e "${YELLOW}Killing processes on port 5000...${NC}"
    lsof -ti:5000 | xargs kill -9
fi

# Kill processes on port 5173 (frontend)
if lsof -ti:5173 > /dev/null 2>&1; then
    echo -e "${YELLOW}Killing processes on port 5173...${NC}"
    lsof -ti:5173 | xargs kill -9
fi

echo ""
echo "========================================"
echo -e "${GREEN}System Stopped Successfully!${NC}"
echo "========================================"
echo ""
echo -e "${YELLOW}Log files preserved:${NC}"
echo -e "  backend.log"
echo -e "  frontend.log"
echo ""
echo -e "${YELLOW}To start the system again:${NC}"
echo -e "  ./start_system.sh"
echo ""
