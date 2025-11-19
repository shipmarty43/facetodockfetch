#!/bin/bash
# Остановка всех локальных сервисов (Backend, Celery, Frontend)
# Docker инфраструктура НЕ останавливается (используйте stop_infrastructure.sh)

# Colors
RED='\033[0;31m'
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

echo ""
echo "=========================================="
echo "Остановка локальных сервисов"
echo "=========================================="
echo ""

STOPPED_COUNT=0

# Stop backend
print_info "Остановка Backend..."
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
                break
            fi
            sleep 0.5
        done
        # Force kill if still running
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null
        fi
        echo -e "  ${GREEN}✓${NC} Backend остановлен (PID: $BACKEND_PID)"
        ((STOPPED_COUNT++))
    else
        echo -e "  ${YELLOW}⚠${NC} Backend не был запущен (PID файл устарел)"
    fi
    rm -f logs/backend.pid
else
    # Check for any running uvicorn processes
    if pgrep -f "uvicorn app.main:app" > /dev/null 2>&1; then
        pkill -f "uvicorn app.main:app"
        echo -e "  ${GREEN}✓${NC} Backend процессы остановлены"
        ((STOPPED_COUNT++))
    else
        echo -e "  ${BLUE}○${NC} Backend не был запущен"
    fi
fi

# Stop Celery
print_info "Остановка Celery Worker..."
if [ -f logs/celery.pid ]; then
    CELERY_PID=$(cat logs/celery.pid)
    if ps -p $CELERY_PID > /dev/null 2>&1; then
        # Send SIGTERM first for graceful shutdown
        kill $CELERY_PID 2>/dev/null
        # Wait for graceful shutdown
        for i in {1..15}; do
            if ! ps -p $CELERY_PID > /dev/null 2>&1; then
                break
            fi
            sleep 0.5
        done
        # Force kill if still running
        if ps -p $CELERY_PID > /dev/null 2>&1; then
            kill -9 $CELERY_PID 2>/dev/null
        fi
        echo -e "  ${GREEN}✓${NC} Celery остановлен (PID: $CELERY_PID)"
        ((STOPPED_COUNT++))
    else
        echo -e "  ${YELLOW}⚠${NC} Celery не был запущен (PID файл устарел)"
    fi
    rm -f logs/celery.pid
else
    # Check for any running celery processes
    if pgrep -f "celery.*app.celery_app" > /dev/null 2>&1; then
        pkill -f "celery.*app.celery_app"
        sleep 1
        # Force kill remaining
        pkill -9 -f "celery.*app.celery_app" 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} Celery процессы остановлены"
        ((STOPPED_COUNT++))
    else
        echo -e "  ${BLUE}○${NC} Celery не был запущен"
    fi
fi

# Stop frontend
print_info "Остановка Frontend..."
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null
        # Wait for shutdown
        for i in {1..5}; do
            if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
                break
            fi
            sleep 0.5
        done
        echo -e "  ${GREEN}✓${NC} Frontend остановлен (PID: $FRONTEND_PID)"
        ((STOPPED_COUNT++))
    else
        echo -e "  ${YELLOW}⚠${NC} Frontend не был запущен (PID файл устарел)"
    fi
    rm -f logs/frontend.pid
else
    # Check for any running vite/node processes from frontend
    if pgrep -f "vite" > /dev/null 2>&1; then
        pkill -f "vite"
        echo -e "  ${GREEN}✓${NC} Frontend процессы остановлены"
        ((STOPPED_COUNT++))
    else
        echo -e "  ${BLUE}○${NC} Frontend не был запущен"
    fi
fi

# Clean up any orphaned processes
print_info "Очистка остаточных процессов..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "celery.*app.celery_app" 2>/dev/null || true

echo ""
echo "=========================================="
if [ $STOPPED_COUNT -gt 0 ]; then
    echo -e "${GREEN}Остановлено сервисов: $STOPPED_COUNT${NC}"
else
    echo -e "${BLUE}Все сервисы уже были остановлены${NC}"
fi
echo "=========================================="
echo ""
echo "Docker инфраструктура (Redis, ES) продолжает работать."
echo "Для её остановки используйте:"
echo -e "  ${GREEN}./scripts/stop_infrastructure.sh${NC}"
echo ""
echo "Для перезапуска сервисов:"
echo -e "  ${GREEN}./scripts/restart_services.sh${NC}"
echo ""
