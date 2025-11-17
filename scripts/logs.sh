#!/bin/bash
# View logs for all services or specific service

COMPOSE_FILE="docker-compose.yml"

# Check if GPU compose file exists and is being used
if [ -f "docker-compose.gpu.yml" ] && docker ps | grep -q "face_recognition"; then
    # Check which containers are running
    if docker ps --format '{{.Names}}' | grep -q "face_recognition_backend"; then
        # Determine which compose file is in use
        NETWORK=$(docker inspect face_recognition_backend --format '{{range .NetworkSettings.Networks}}{{.NetworkMode}}{{end}}' 2>/dev/null || echo "")
        if [ ! -z "$NETWORK" ]; then
            COMPOSE_FILE="docker-compose.yml"
        fi
    fi
fi

# Parse arguments
SERVICE=""
FOLLOW="-f"

while [[ $# -gt 0 ]]; do
    case $1 in
        gpu|--gpu)
            COMPOSE_FILE="docker-compose.gpu.yml"
            shift
            ;;
        --no-follow)
            FOLLOW=""
            shift
            ;;
        backend|celery|celery_worker|frontend|redis|elasticsearch)
            SERVICE=$1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [gpu] [backend|celery_worker|frontend|redis|elasticsearch] [--no-follow]"
            exit 1
            ;;
    esac
done

echo "Viewing logs from: $COMPOSE_FILE"
echo "Press Ctrl+C to stop"
echo ""

if [ -z "$SERVICE" ]; then
    docker-compose -f $COMPOSE_FILE logs $FOLLOW
else
    docker-compose -f $COMPOSE_FILE logs $FOLLOW $SERVICE
fi
