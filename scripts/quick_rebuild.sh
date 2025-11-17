#!/bin/bash
# Quick rebuild without cache - быстрое пересоздание

set -e

COMPOSE_FILE="docker-compose.yml"
if [ "$1" == "gpu" ]; then
    COMPOSE_FILE="docker-compose.gpu.yml"
fi

echo "Quick rebuild (no cache)..."

# Stop and rebuild
docker-compose -f $COMPOSE_FILE down
docker-compose -f $COMPOSE_FILE build --no-cache
docker-compose -f $COMPOSE_FILE up -d

echo "Done! Check status: docker-compose -f $COMPOSE_FILE ps"
