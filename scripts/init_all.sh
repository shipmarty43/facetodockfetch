#!/bin/bash
# Initialize all services - database, elasticsearch, and create default admin user
# This script runs all initialization steps with default settings

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Default admin credentials
DEFAULT_USERNAME="admin"
DEFAULT_PASSWORD="admin123"

echo "=========================================="
echo "Face Recognition System - Full Initialization"
echo "=========================================="
echo ""

# Check if conda environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "face-recognition-system" ]]; then
    print_warn "Conda environment not activated!"
    echo "Please run: conda activate face-recognition-system"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    print_error "Must be run from project root directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Step 0: Quick dependency check (optional)
echo ""
print_step "Checking critical dependencies..."
cd backend
if python -c "import passlib, bcrypt, sqlalchemy" 2>/dev/null; then
    print_info "✓ Core dependencies available"
else
    print_warn "⚠ Some core dependencies may be missing"
    echo "  Run: python scripts/check_dependencies.py for details"
fi
cd ..

# Step 1: Check infrastructure services
print_step "Checking infrastructure services..."

# Check Redis
if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    print_info "✓ Redis is running"
elif docker ps | grep face_recognition_redis > /dev/null 2>&1; then
    print_info "✓ Redis container is running"
else
    print_warn "✗ Redis is not running"
    echo ""
    echo "Start Redis with:"
    echo -e "  ${GREEN}./scripts/start_infrastructure.sh${NC}"
    echo ""
    read -p "Continue without Redis? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Elasticsearch
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    print_info "✓ Elasticsearch is running"
elif docker ps | grep face_recognition_elasticsearch > /dev/null 2>&1; then
    print_warn "⚠ Elasticsearch container is starting (may take 10-30s)"
else
    print_warn "✗ Elasticsearch is not running"
    echo ""
    echo "Start Elasticsearch with:"
    echo -e "  ${GREEN}./scripts/start_infrastructure.sh${NC}"
    echo ""
    read -p "Continue without Elasticsearch? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Create directories
print_step "Creating necessary directories..."
mkdir -p data/uploads data/db data/cache logs models
print_info "✓ Directories created"

# Step 2.5: Create .env file if not exists
echo ""
print_step "Checking .env file..."
if [ ! -f ".env" ]; then
    print_info "Creating .env file from .env.example..."
    cp .env.example .env
    print_info "✓ .env file created"
    echo ""
    echo -e "${YELLOW}⚠ IMPORTANT: Review and update .env file with your settings!${NC}"
    echo "  Location: $(pwd)/.env"
    echo ""
else
    print_info "✓ .env file already exists"
fi

# Step 3: Initialize SQLite database
echo ""
print_step "Initializing SQLite database..."
cd backend
python scripts/init_db.py
if [ $? -eq 0 ]; then
    print_info "✓ Database initialized"
else
    print_error "✗ Failed to initialize database"
    exit 1
fi

# Step 4: Initialize Elasticsearch
echo ""
print_step "Initializing Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    python scripts/init_elasticsearch.py
    if [ $? -eq 0 ]; then
        print_info "✓ Elasticsearch initialized"
    else
        print_warn "⚠ Elasticsearch initialization failed (not critical)"
    fi
else
    print_warn "⚠ Skipping Elasticsearch initialization (not running)"
fi

# Step 5: Create default admin user
echo ""
print_step "Creating default admin user..."
python scripts/create_admin.py --username "$DEFAULT_USERNAME" --password "$DEFAULT_PASSWORD"
if [ $? -eq 0 ]; then
    print_info "✓ Admin user created/verified"
else
    print_warn "⚠ Admin user creation failed (may already exist)"
fi

cd ..

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}Initialization complete!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}Default Admin Credentials:${NC}"
echo -e "  Username: ${GREEN}${DEFAULT_USERNAME}${NC}"
echo -e "  Password: ${GREEN}${DEFAULT_PASSWORD}${NC}"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Change the default password in production!${NC}"
echo ""
echo "Next steps:"
echo -e "  1. Start services: ${GREEN}./scripts/start_services.sh${NC}"
echo -e "  2. Access API docs: ${BLUE}http://localhost:30000/docs${NC}"
echo -e "  3. Access frontend: ${BLUE}http://localhost:3003${NC}"
echo ""
echo "To reset admin password:"
echo -e "  ${GREEN}cd backend && python scripts/create_admin.py --force${NC}"
echo ""
