#!/bin/bash
# Rebuild Docker containers - пересоздание контейнеров

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "=========================================="
echo "Docker Containers Rebuild"
echo "=========================================="
echo ""

# Determine which compose file to use
COMPOSE_FILE="docker-compose.yml"

if [ "$1" == "gpu" ] || [ "$1" == "--gpu" ]; then
    COMPOSE_FILE="docker-compose.gpu.yml"
    print_info "Using GPU configuration"
else
    print_info "Using CPU configuration (add 'gpu' argument for GPU version)"
fi

# Ask for confirmation
print_warn "This will stop and rebuild all containers."
read -p "Continue? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Stop containers
print_step "Stopping containers..."
docker-compose -f $COMPOSE_FILE down

# Remove old images (optional)
read -p "Remove old images? This will free up space but increase rebuild time [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Removing old images..."
    docker-compose -f $COMPOSE_FILE down --rmi all
fi

# Build with no cache
print_step "Building containers (no cache)..."
docker-compose -f $COMPOSE_FILE build --no-cache --pull

# Start containers
print_step "Starting containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
print_step "Waiting for services to start..."
sleep 10

# Check health
print_step "Checking service health..."
docker-compose -f $COMPOSE_FILE ps

# Check backend health
echo ""
print_info "Checking backend health endpoint..."
max_retries=30
counter=0
while [ $counter -lt $max_retries ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_info "Backend is healthy!"
        curl -s http://localhost:8000/health | python3 -m json.tool || echo ""
        break
    fi
    counter=$((counter+1))
    echo -n "."
    sleep 2
done

if [ $counter -eq $max_retries ]; then
    print_warn "Backend health check timeout - check logs manually"
fi

echo ""
print_info "=========================================="
print_info "Rebuild completed!"
print_info "=========================================="
echo ""
echo "Services:"
echo "  - Backend: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "View logs:"
echo "  docker-compose -f $COMPOSE_FILE logs -f"
echo ""
