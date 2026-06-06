#!/bin/bash

# Quick Package Creator for Wellbeing Monitor App
# Creates a distributable package in seconds

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Wellbeing Monitor - Quick Package Creator           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Get current date for versioning
DATE=$(date +%Y-%m-%d)
VERSION="2.0"

echo "Choose packaging method:"
echo ""
echo "1. ZIP File (Easiest - 1 min)"
echo "2. Docker Image (Most reliable - 5 min)"
echo "3. Both (Recommended - 10 min)"
echo "4. Exit"
echo ""
read -p "Select (1-4): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}Creating ZIP file...${NC}"
        
        # Create packages directory
        mkdir -p packages
        
        # Create ZIP excluding unnecessary files
        ZIP_NAME="packages/wellbeing-monitor-${VERSION}-${DATE}.zip"
        zip -r "$ZIP_NAME" . \
            -x "*/\.*" \
            "*/data/*" \
            "*/__pycache__/*" \
            "*.pyc" \
            "*/.git/*" \
            "*/packages/*" \
            "*.egg-info/*" \
            "*/.DS_Store" \
            "*/Thumbs.db" \
            2>/dev/null
        
        SIZE=$(du -h "$ZIP_NAME" | cut -f1)
        
        echo -e "${GREEN}✓ ZIP created successfully!${NC}"
        echo ""
        echo "File: $ZIP_NAME"
        echo "Size: $SIZE"
        echo ""
        echo "Ready to share! You can:"
        echo "  • Email it to friends"
        echo "  • Upload to Google Drive"
        echo "  • Put on USB drive"
        echo "  • Share via WeTransfer"
        ;;
    
    2)
        echo ""
        echo -e "${BLUE}Creating Docker image...${NC}"
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo -e "${YELLOW}Docker is not installed!${NC}"
            echo "Install from: docker.com"
            exit 1
        fi
        
        # Build image
        docker build -t wellbeing-monitor:${VERSION} .
        
        echo -e "${GREEN}✓ Docker image created!${NC}"
        echo ""
        echo "Image: wellbeing-monitor:${VERSION}"
        echo ""
        echo "To run:"
        echo "  $ docker run -p 5000:5000 wellbeing-monitor:${VERSION}"
        echo ""
        echo "To share:"
        echo "  $ docker save wellbeing-monitor:${VERSION} -o wellbeing.tar.gz"
        echo "  Then send wellbeing.tar.gz to others"
        echo ""
        echo "Others can load with:"
        echo "  $ docker load -i wellbeing.tar.gz"
        echo "  $ docker run -p 5000:5000 wellbeing-monitor:${VERSION}"
        ;;
    
    3)
        echo ""
        echo -e "${BLUE}Creating ZIP file...${NC}"
        
        mkdir -p packages
        ZIP_NAME="packages/wellbeing-monitor-${VERSION}-${DATE}.zip"
        zip -r "$ZIP_NAME" . \
            -x "*/\.*" \
            "*/data/*" \
            "*/__pycache__/*" \
            "*.pyc" \
            "*/.git/*" \
            "*/packages/*" \
            "*.egg-info/*" \
            "*/.DS_Store" \
            "*/Thumbs.db" \
            2>/dev/null
        
        SIZE=$(du -h "$ZIP_NAME" | cut -f1)
        
        echo -e "${GREEN}✓ ZIP created: $ZIP_NAME ($SIZE)${NC}"
        echo ""
        
        echo -e "${BLUE}Creating Docker image...${NC}"
        
        if ! command -v docker &> /dev/null; then
            echo -e "${YELLOW}⚠ Docker not found - skipping${NC}"
        else
            docker build -t wellbeing-monitor:${VERSION} .
            echo -e "${GREEN}✓ Docker image created: wellbeing-monitor:${VERSION}${NC}"
        fi
        
        echo ""
        echo -e "${GREEN}✓ Both packages ready!${NC}"
        echo ""
        echo "ZIP File: $ZIP_NAME"
        echo "  For easy sharing to friends"
        echo ""
        echo "Docker Image: wellbeing-monitor:${VERSION}"
        echo "  For server deployment"
        ;;
    
    4)
        echo "Exiting..."
        exit 0
        ;;
    
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "═════════════════════════════════════════════════════════════"
echo ""
echo "For more options, see: HOW_TO_DOWNLOAD_AS_APP.md"
echo ""
