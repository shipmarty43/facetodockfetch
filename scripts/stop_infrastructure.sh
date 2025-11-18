#!/bin/bash
# Stop infrastructure services (Redis + Elasticsearch)

set -e

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
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
    echo "Error: docker-compose is not available!"
    exit 1
fi

print_info "Stopping Redis and Elasticsearch..."
$COMPOSE_CMD -f docker-compose.infrastructure.yml down

echo ""
print_info "Infrastructure services stopped"
echo ""
echo "To start again:"
echo "  ${GREEN}./scripts/start_infrastructure.sh${NC}"
echo ""
