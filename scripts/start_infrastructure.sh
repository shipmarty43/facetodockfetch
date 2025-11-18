#!/bin/bash
# Start infrastructure services (Redis + Elasticsearch) in Docker
# For use with native (non-Docker) backend/frontend installation

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

echo "=========================================="
echo "Face Recognition Infrastructure Services"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    print_error "docker-compose is not available!"
    echo "Install docker-compose or use Docker with compose plugin"
    exit 1
fi

print_info "Using: $COMPOSE_CMD"

# Stop existing containers if running
print_step "Stopping existing infrastructure containers..."
$COMPOSE_CMD -f docker-compose.infrastructure.yml down 2>/dev/null || true

# Start infrastructure services
print_step "Starting Redis and Elasticsearch..."
$COMPOSE_CMD -f docker-compose.infrastructure.yml up -d

# Wait for services to be ready
echo ""
print_step "Waiting for services to be ready..."

# Wait for Redis
print_info "Checking Redis..."
for i in {1..30}; do
    if docker exec face_recognition_redis redis-cli ping > /dev/null 2>&1; then
        print_info "✓ Redis is ready"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Wait for Elasticsearch
print_info "Checking Elasticsearch..."
for i in {1..60}; do
    if curl -s http://localhost:9200 > /dev/null 2>&1; then
        print_info "✓ Elasticsearch is ready"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Show status
echo ""
echo "=========================================="
echo -e "${GREEN}Infrastructure services started!${NC}"
echo "=========================================="
echo ""
echo "Services:"
echo -e "  - ${BLUE}Redis:${NC} localhost:6379"
echo -e "  - ${BLUE}Elasticsearch:${NC} http://localhost:9200"
echo ""
echo "Check status:"
echo -e "  ${GREEN}$COMPOSE_CMD -f docker-compose.infrastructure.yml ps${NC}"
echo ""
echo "View logs:"
echo -e "  ${GREEN}$COMPOSE_CMD -f docker-compose.infrastructure.yml logs -f${NC}"
echo ""
echo "Stop services:"
echo -e "  ${GREEN}./scripts/stop_infrastructure.sh${NC}"
echo ""

# Test connections
print_step "Testing connections..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Redis connection: OK"
else
    echo -e "  ${YELLOW}⚠${NC} Cannot connect to Redis (redis-cli not installed?)"
    echo "    Install: sudo apt-get install redis-tools"
fi

if curl -s http://localhost:9200 > /dev/null 2>&1; then
    ES_VERSION=$(curl -s http://localhost:9200 | grep -o '"number" : "[^"]*"' | cut -d'"' -f4)
    echo -e "  ${GREEN}✓${NC} Elasticsearch connection: OK"
    echo -e "    Version: ${BLUE}$ES_VERSION${NC}"
else
    echo -e "  ${RED}✗${NC} Cannot connect to Elasticsearch"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Ready for native backend/frontend!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo -e "  1. ${GREEN}conda activate face-recognition-system${NC}"
echo -e "  2. ${GREEN}./scripts/start_services.sh${NC}"
echo ""
