#!/bin/bash

# Wellbeing Monitoring App - Installation & Dependencies Check
# Verifies all required packages are installed

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    Wellbeing Monitor - Dependency Verification Tool      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
installed=0
missing=0

# Python packages for app
packages=(
    "flask"
    "flask_cors"
    "requests"
    "numpy"
    "opencv-python"
    "librosa"
    "scipy"
    "scikit-learn"
)

echo -e "${BLUE}Checking Python Package Dependencies...${NC}\n"

for package in "${packages[@]}"; do
    # Convert underscores to hyphens for pip check
    pip_name=${package//_/-}
    
    if pip show "$pip_name" &> /dev/null; then
        version=$(pip show "$pip_name" | grep Version | cut -d' ' -f2)
        echo -e "${GREEN}✓${NC} $package (v$version)"
        ((installed++))
    else
        echo -e "${RED}✗${NC} $package - NOT INSTALLED"
        ((missing++))
    fi
done

echo ""
echo "Summary: $installed installed, $missing missing"
echo ""

if [ $missing -gt 0 ]; then
    echo -e "${YELLOW}Missing packages detected. Install with:${NC}"
    echo ""
    echo "  pip install flask flask-cors requests numpy opencv-python librosa scipy scikit-learn"
    echo ""
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install flask flask-cors requests numpy opencv-python librosa scipy scikit-learn
        echo -e "${GREEN}✓ Installation complete${NC}"
    fi
else
    echo -e "${GREEN}✓ All dependencies installed!${NC}"
fi

echo ""
echo "Checking system tools..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    py_version=$(python3 --version)
    echo -e "${GREEN}✓${NC} $py_version"
else
    echo -e "${RED}✗${NC} Python 3 not found"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip is available"
else
    echo -e "${RED}✗${NC} pip not found"
fi

# Check git (optional)
if command -v git &> /dev/null; then
    echo -e "${GREEN}✓${NC} git available (optional)"
else
    echo -e "${YELLOW}○${NC} git not found (optional)"
fi

# Check ffmpeg (optional, for audio processing)
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓${NC} ffmpeg available (for audio)"
else
    echo -e "${YELLOW}○${NC} ffmpeg not found (optional)"
fi

# Check Docker (optional)
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${GREEN}✓${NC} Docker v$docker_version available"
else
    echo -e "${YELLOW}○${NC} Docker not found (optional, for containerization)"
fi

echo ""
echo "Checking project files..."
echo ""

files=(
    "app_backend.py"
    "app_dashboard.html"
    "app_api_client.py"
    "database.py"
    "main.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file - MISSING"
    fi
done

echo ""
echo "═════════════════════════════════════════════════════════════"
echo ""

# Final status
if [ $missing -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to use.${NC}"
    echo ""
    echo "Start with: ./app-start.sh"
else
    echo -e "${YELLOW}⚠ Some packages missing. Install and try again.${NC}"
fi

echo ""
