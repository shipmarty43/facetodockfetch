#!/bin/bash
# Stop infrastructure services (Redis + Elasticsearch)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "Stopping Infrastructure Services"
echo "=========================================="
echo ""

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

print_info "Stopping Redis and Elasticsearch..."
$COMPOSE_CMD -f docker-compose.infrastructure.yml down

echo ""
echo "=========================================="
echo -e "${GREEN}Infrastructure services stopped${NC}"
echo "=========================================="
echo ""
echo "To start again:"
echo -e "  ${GREEN}./scripts/start_infrastructure.sh${NC}"
echo ""
