#!/bin/bash
# Complete installation and setup script for Wellbeing Monitoring System with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main script
main() {
    print_header "WELLBEING MONITORING SYSTEM - INSTALLATION & SETUP"
    
    echo ""
    echo "This script will:"
    echo "  1. Check system requirements"
    echo "  2. Verify Docker installation"
    echo "  3. Create environment configuration"
    echo "  4. Build Docker image"
    echo "  5. Start services"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi
    
    # Step 1: Check system requirements
    print_info "Step 1: Checking system requirements..."
    check_system_requirements
    
    # Step 2: Check Docker installation
    print_info "Step 2: Verifying Docker installation..."
    check_docker_installation
    
    # Step 3: Create environment configuration
    print_info "Step 3: Setting up environment..."
    setup_environment
    
    # Step 4: Create necessary directories
    print_info "Step 4: Creating data directories..."
    create_directories
    
    # Step 5: Build Docker image
    print_info "Step 5: Building Docker image..."
    print_warning "This may take several minutes..."
    build_docker_image
    
    # Step 6: Run demo
    print_info "Step 6: Running verification demo..."
    run_demo
    
    # Success
    print_header "🎉 INSTALLATION COMPLETE!"
    
    echo ""
    print_success "System is ready to use!"
    echo ""
    
    print_info "Quick start commands:"
    echo "  • Start monitoring:   docker-compose run --rm wellbeing-monitor monitor"
    echo "  • Query data:         docker-compose run --rm wellbeing-monitor query"
    echo "  • Run demo:           docker-compose run --rm wellbeing-monitor demo"
    echo "  • Show help:          make help"
    echo ""
    
    print_info "Or use Makefile for easier commands:"
    echo "  • make monitor        Start real-time monitoring"
    echo "  • make query          Launch query tool"
    echo "  • make demo           Run demo"
    echo "  • make help           Show all available commands"
    echo ""
    
    print_info "For detailed documentation:"
    echo "  • DOCKER_GUIDE.md     Complete Docker guide"
    echo "  • DOCKER_COMMANDS.md  Command reference"
    echo "  • DATABASE_SETUP.md   Database documentation"
    echo ""
}

check_system_requirements() {
    print_info "Checking OS..."
    
    case "$(uname -s)" in
        Linux*)
            print_success "Linux detected"
            OS="Linux"
            ;;
        Darwin*)
            print_success "macOS detected"
            OS="Mac"
            ;;
        MINGW*)
            print_success "Windows (Git Bash) detected"
            OS="Windows"
            ;;
        *)
            print_error "Unsupported operating system"
            exit 1
            ;;
    esac
    
    print_info "Checking disk space..."
    available=$(df . | tail -1 | awk '{print $4}')
    
    if [ "$available" -lt 2000000 ]; then
        print_warning "Low disk space (less than 2GB available)"
    else
        print_success "Sufficient disk space available"
    fi
    
    print_info "Checking RAM..."
    case "$(uname -s)" in
        Linux*)
            total_ram=$(free -m | awk 'NR==2{print $2}')
            ;;
        Darwin*)
            total_ram=$(vm_stat | grep "Pages free" | awk '{print $3 * 4096 / 1024 / 1024}' | cut -d. -f1)
            ;;
        *)
            total_ram="unknown"
            ;;
    esac
    
    if [ "$total_ram" != "unknown" ] && [ "$total_ram" -lt 2048 ]; then
        print_warning "System has less than 2GB RAM (may affect performance)"
    else
        print_success "Sufficient RAM available"
    fi
}

check_docker_installation() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"
    docker --version
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Install from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"
    docker-compose --version
    
    print_info "Checking Docker daemon..."
    if ! docker ps &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Start Docker and try again"
        exit 1
    fi
    print_success "Docker daemon is running"
    
    print_info "Checking Docker resources..."
    docker system df | head -3
}

setup_environment() {
    if [ ! -f ".env" ]; then
        print_info "Creating .env file from template..."
        
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env file created from template"
        else
            print_warning ".env.example not found, creating new .env"
            cat > .env << 'EOF'
# Environment Variables
POSTGRES_USER=wellbeing
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_DB=wellbeing_monitor
TZ=UTC
PYTHONUNBUFFERED=1
EOF
        fi
        
        echo ""
        print_warning "Please edit .env with your custom settings (optional)"
        echo "Edit with: nano .env"
        echo ""
    else
        print_success ".env file already exists"
    fi
}

create_directories() {
    mkdir -p data
    mkdir -p reports
    mkdir -p exports
    mkdir -p logs
    mkdir -p backups
    
    print_success "Directories created:"
    echo "  • data/       (for databases)"
    echo "  • reports/    (for session reports)"
    echo "  • exports/    (for JSON exports)"
    echo "  • logs/       (for application logs)"
    echo "  • backups/    (for database backups)"
}

build_docker_image() {
    print_info "Building Docker image..."
    
    if docker-compose build; then
        print_success "Docker image built successfully"
    else
        print_error "Docker build failed"
        exit 1
    fi
}

run_demo() {
    print_info "Running verification demo..."
    echo ""
    
    if docker-compose run --rm wellbeing-monitor python -c "
print('Testing imports...')
import cv2
import mediapipe
import librosa
import numpy as np
from database import WellbeingDatabase
print('✅ All imports successful')
print('')
print('Testing database...')
db = WellbeingDatabase('/app/data/test.db')
session_id = db.create_session('test', 'test')
print(f'✅ Database test successful (session {session_id})')
db.close()
"; then
        print_success "Verification demo passed"
    else
        print_error "Verification demo failed"
        print_warning "Installation may have issues, check logs above"
    fi
}

# Run main function
main

exit 0
