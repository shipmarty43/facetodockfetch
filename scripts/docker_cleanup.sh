#!/bin/bash
# Clean Docker resources - очистка Docker ресурсов

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "=========================================="
echo "Docker Cleanup"
echo "=========================================="
echo ""

print_info "Current Docker disk usage:"
docker system df
echo ""

print_warn "This will clean up:"
echo "  - Stopped containers"
echo "  - Unused networks"
echo "  - Dangling images"
echo "  - Build cache"
echo ""

read -p "Continue? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Stop our containers first
print_info "Stopping face recognition containers..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.gpu.yml down 2>/dev/null || true

# Clean up
print_info "Removing stopped containers..."
docker container prune -f

print_info "Removing unused networks..."
docker network prune -f

print_info "Removing dangling images..."
docker image prune -f

# Ask about build cache
read -p "Remove build cache? This will increase next build time [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Removing build cache..."
    docker builder prune -f
fi

# Ask about volumes
read -p "Remove unused volumes? WARNING: This may delete data! [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warn "Removing unused volumes..."
    docker volume prune -f
fi

echo ""
print_info "Cleanup completed!"
echo ""
print_info "New disk usage:"
docker system df
