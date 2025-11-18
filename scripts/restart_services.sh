#!/bin/bash
# Перезапуск локальных сервисов (Backend, Celery, Frontend)
# Docker инфраструктура НЕ перезапускается

set -e

# Suppress warnings
export PYTHONWARNINGS="ignore::UserWarning:passlib"

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

echo ""
echo "=========================================="
echo "Перезапуск сервисов"
echo "=========================================="
echo ""

# Check directory
if [ ! -d "backend" ]; then
    print_error "Запустите скрипт из корневой директории проекта"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# ==========================================
# Stop services
# ==========================================
print_info "Остановка сервисов..."

# Stop backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null || true
        print_info "Backend остановлен (PID: $BACKEND_PID)"
    fi
    rm -f logs/backend.pid
fi

# Stop Celery
if [ -f logs/celery.pid ]; then
    CELERY_PID=$(cat logs/celery.pid)
    if ps -p $CELERY_PID > /dev/null 2>&1; then
        kill $CELERY_PID 2>/dev/null || true
        print_info "Celery остановлен (PID: $CELERY_PID)"
    fi
    rm -f logs/celery.pid
fi

# Stop frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_info "Frontend остановлен (PID: $FRONTEND_PID)"
    fi
    rm -f logs/frontend.pid
fi

# Kill any remaining processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "celery.*app.celery_app" 2>/dev/null || true

# Wait for processes to stop
sleep 2

# ==========================================
# Check infrastructure
# ==========================================
print_info "Проверка инфраструктуры..."

# Check Redis
if ! redis-cli ping > /dev/null 2>&1 && ! docker exec face_recognition_redis redis-cli ping > /dev/null 2>&1; then
    print_warn "Redis не запущен!"
    print_info "Запустите: ./scripts/start_infrastructure.sh"
fi

# Check Elasticsearch
if ! curl -s http://localhost:9200 > /dev/null 2>&1; then
    print_warn "Elasticsearch не запущен!"
    print_info "Запустите: ./scripts/start_infrastructure.sh"
fi

# ==========================================
# Start services
# ==========================================
print_info "Запуск сервисов..."

# Create log directory
mkdir -p logs

# Start backend
print_info "Запуск Backend..."
cd backend
$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 30000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
cd ..

sleep 3

# Start Celery worker
print_info "Запуск Celery Worker..."
cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=4 > ../logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > ../logs/celery.pid
cd ..

# Start frontend
if command -v npm &> /dev/null; then
    print_info "Запуск Frontend..."
    cd frontend
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
fi

sleep 2

# ==========================================
# Verify
# ==========================================
echo ""
print_info "Проверка сервисов..."

# Check backend
if curl -s http://localhost:30000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Backend работает на http://localhost:30000"
else
    echo -e "  ${YELLOW}⚠${NC} Backend запускается..."
fi

# Check Celery
if [ -f logs/celery.pid ]; then
    CELERY_PID=$(cat logs/celery.pid)
    if ps -p $CELERY_PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Celery Worker работает (PID: $CELERY_PID)"
    fi
fi

# Check frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Frontend работает на http://localhost:3003"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Сервисы перезапущены!${NC}"
echo "=========================================="
echo ""
echo "Логи:"
echo -e "  Backend:  ${BLUE}tail -f logs/backend.log${NC}"
echo -e "  Celery:   ${BLUE}tail -f logs/celery.log${NC}"
echo -e "  Frontend: ${BLUE}tail -f logs/frontend.log${NC}"
echo ""
