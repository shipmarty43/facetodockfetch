#!/bin/bash
# Start all services for local development (Conda)

set -e

# Suppress bcrypt version warnings globally
export PYTHONWARNINGS="ignore::UserWarning:passlib"

echo "=========================================="
echo "Starting Face Recognition System Services"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if conda environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "face-recognition-system" ]]; then
    print_warn "Conda environment not activated!"
    echo "Please run: conda activate face-recognition-system"
    exit 1
fi

# Check Redis (Docker container)
print_info "Checking Redis..."
if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    print_info "✓ Redis is running"
elif docker ps | grep face_recognition_redis > /dev/null 2>&1; then
    print_info "✓ Redis container is running"
else
    print_warn "✗ Redis is not running!"
    echo ""
    echo "Start infrastructure services with:"
    echo "  ${GREEN}./scripts/start_infrastructure.sh${NC}"
    echo ""
    echo "Or manually:"
    echo "  docker run -d --name face_recognition_redis -p 6379:6379 redis:7-alpine"
    echo ""
    exit 1
fi

# Check Elasticsearch (Docker container)
print_info "Checking Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    print_info "✓ Elasticsearch is running"
elif docker ps | grep face_recognition_elasticsearch > /dev/null 2>&1; then
    print_warn "⚠ Elasticsearch container is running but not ready yet (wait 10-30s)"
    sleep 5
else
    print_warn "✗ Elasticsearch is not running!"
    echo ""
    echo "Start infrastructure services with:"
    echo "  ${GREEN}./scripts/start_infrastructure.sh${NC}"
    echo ""
    echo "Or manually:"
    echo "  docker run -d --name face_recognition_elasticsearch \\"
    echo "    -p 9200:9200 -p 9300:9300 \\"
    echo "    -e \"discovery.type=single-node\" \\"
    echo "    -e \"xpack.security.enabled=false\" \\"
    echo "    docker.elastic.co/elasticsearch/elasticsearch:8.10.0"
    echo ""
    exit 1
fi

# Create log directory
mkdir -p logs

# Start backend
print_info "Starting backend on http://localhost:30000..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 30000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
cd ..

# Wait for backend to start
sleep 3

# Start Celery worker
print_info "Starting Celery worker..."
cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=4 > ../logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > ../logs/celery.pid
cd ..

# Start frontend (if npm is available)
if command -v npm &> /dev/null; then
    print_info "Starting frontend on http://localhost:3003..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install
    fi
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
else
    print_warn "npm not found - skipping frontend"
fi

echo ""
print_info "=========================================="
print_info "All services started!"
print_info "=========================================="
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:30000"
echo "  - API Docs: http://localhost:30000/docs"
echo "  - Frontend: http://localhost:3003"
echo ""
echo "Logs:"
echo "  - Backend: tail -f logs/backend.log"
echo "  - Celery: tail -f logs/celery.log"
echo "  - Frontend: tail -f logs/frontend.log"
echo ""
echo "To stop services:"
echo "  ./scripts/stop_services.sh"
echo ""
