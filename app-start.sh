#!/bin/bash

# Wellbeing Monitor - App Quick Start Script
# Starts the Flask API backend and opens the dashboard

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Wellbeing Monitoring System - App Quick Start         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}» Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
echo ""

# Check dependencies
echo -e "${BLUE}» Checking Flask...${NC}"
if ! python3 -c "import flask" &> /dev/null; then
    echo -e "${YELLOW}! Flask not installed. Installing...${NC}"
    pip3 install flask flask-cors
    echo -e "${GREEN}✓ Flask installed${NC}"
else
    echo -e "${GREEN}✓ Flask available${NC}"
fi
echo ""

# Check if database exists
echo -e "${BLUE}» Checking database...${NC}"
if [ ! -f "database.py" ]; then
    echo -e "${RED}✗ database.py not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database module available${NC}"
echo ""

# Check if dashboard exists
echo -e "${BLUE}» Checking dashboard...${NC}"
if [ ! -f "app_dashboard.html" ]; then
    echo -e "${RED}✗ app_dashboard.html not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dashboard available${NC}"
echo ""

# Check if backend exists
echo -e "${BLUE}» Checking backend...${NC}"
if [ ! -f "app_backend.py" ]; then
    echo -e "${RED}✗ app_backend.py not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend available${NC}"
echo ""

# Check if port is available
echo -e "${BLUE}» Checking port 5000...${NC}"
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}! Port 5000 is already in use${NC}"
    echo "Options:"
    echo "  1. Kill existing process: lsof -i :5000 | tail -1 | awk '{print \$2}' | xargs kill -9"
    echo "  2. Use different port: python3 app_backend.py --port 8000"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Port 5000 is available${NC}"
fi
echo ""

# Create data directories
echo -e "${BLUE}» Creating data directories...${NC}"
mkdir -p data reports exports logs
echo -e "${GREEN}✓ Directories ready${NC}"
echo ""

# Initialize database if needed
echo -e "${BLUE}» Initializing database...${NC}"
python3 -c "from database import WellbeingDatabase; db = WellbeingDatabase(); print('✓ Database ready')" || echo -e "${YELLOW}! Database already initialized${NC}"
echo ""

# Show instructions
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🚀 READY TO START - Choose an option:          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "1. Start Backend API (Port 5000)"
echo "2. Open Dashboard in Browser"
echo "3. Both (Backend + Dashboard)"
echo "4. Exit"
echo ""
read -p "Choose option (1-4): " option

case $option in
    1)
        echo ""
        echo -e "${BLUE}Starting Flask Backend...${NC}"
        echo ""
        python3 app_backend.py
        ;;
    2)
        echo ""
        echo -e "${BLUE}Opening Dashboard...${NC}"
        if command -v open &> /dev/null; then
            # macOS
            open "app_dashboard.html"
        elif command -v xdg-open &> /dev/null; then
            # Linux
            xdg-open "app_dashboard.html"
        elif command -v start &> /dev/null; then
            # Windows
            start "app_dashboard.html"
        else
            echo "Browser could not be opened automatically."
            echo "Please open: file://$(pwd)/app_dashboard.html"
        fi
        echo -e "${YELLOW}Note: API server still not running!${NC}"
        echo "In another terminal, run: python3 app_backend.py"
        ;;
    3)
        echo ""
        echo -e "${BLUE}Starting Flask Backend in background...${NC}"
        python3 app_backend.py &
        sleep 2
        echo ""
        echo -e "${BLUE}Opening Dashboard...${NC}"
        if command -v open &> /dev/null; then
            open "app_dashboard.html"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "app_dashboard.html"
        elif command -v start &> /dev/null; then
            start "app_dashboard.html"
        else
            echo "Browser could not be opened automatically."
            echo "Please open: file://$(pwd)/app_dashboard.html"
        fi
        wait
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac
