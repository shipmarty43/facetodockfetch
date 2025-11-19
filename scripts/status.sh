#!/bin/bash
# Проверка статуса всех компонентов системы

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "Статус системы Face Recognition & OCR"
echo "=========================================="
echo ""

# ==========================================
# Docker Infrastructure
# ==========================================
echo -e "${CYAN}Docker инфраструктура:${NC}"
echo ""

# Redis
if docker ps 2>/dev/null | grep -q face_recognition_redis; then
    if docker exec face_recognition_redis redis-cli ping > /dev/null 2>&1; then
        REDIS_INFO=$(docker exec face_recognition_redis redis-cli info server 2>/dev/null | grep redis_version | cut -d: -f2 | tr -d '\r')
        echo -e "  ${GREEN}●${NC} Redis          ${GREEN}работает${NC} (v$REDIS_INFO)"
    else
        echo -e "  ${YELLOW}●${NC} Redis          ${YELLOW}контейнер запущен, но не отвечает${NC}"
    fi
elif redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}●${NC} Redis          ${GREEN}работает${NC} (локально)"
else
    echo -e "  ${RED}●${NC} Redis          ${RED}не запущен${NC}"
fi

# Elasticsearch
if docker ps 2>/dev/null | grep -q face_recognition_elasticsearch; then
    if curl -s http://localhost:9200 > /dev/null 2>&1; then
        ES_VERSION=$(curl -s http://localhost:9200 | grep -o '"number" : "[^"]*"' | cut -d'"' -f4)
        ES_STATUS=$(curl -s http://localhost:9200/_cluster/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo -e "  ${GREEN}●${NC} Elasticsearch  ${GREEN}работает${NC} (v$ES_VERSION, status: $ES_STATUS)"
    else
        echo -e "  ${YELLOW}●${NC} Elasticsearch  ${YELLOW}контейнер запущен, но не отвечает${NC}"
    fi
elif curl -s http://localhost:9200 > /dev/null 2>&1; then
    ES_VERSION=$(curl -s http://localhost:9200 | grep -o '"number" : "[^"]*"' | cut -d'"' -f4)
    echo -e "  ${GREEN}●${NC} Elasticsearch  ${GREEN}работает${NC} (локально, v$ES_VERSION)"
else
    echo -e "  ${RED}●${NC} Elasticsearch  ${RED}не запущен${NC}"
fi

echo ""

# ==========================================
# Local Services
# ==========================================
echo -e "${CYAN}Локальные сервисы:${NC}"
echo ""

# Backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        if curl -s http://localhost:30000/health > /dev/null 2>&1; then
            echo -e "  ${GREEN}●${NC} Backend        ${GREEN}работает${NC} (PID: $BACKEND_PID, port: 30000)"
        else
            echo -e "  ${YELLOW}●${NC} Backend        ${YELLOW}процесс запущен, но не отвечает${NC} (PID: $BACKEND_PID)"
        fi
    else
        echo -e "  ${RED}●${NC} Backend        ${RED}не запущен${NC} (PID файл устарел)"
    fi
elif pgrep -f "uvicorn app.main:app" > /dev/null 2>&1; then
    BACKEND_PID=$(pgrep -f "uvicorn app.main:app" | head -1)
    echo -e "  ${GREEN}●${NC} Backend        ${GREEN}работает${NC} (PID: $BACKEND_PID)"
else
    echo -e "  ${RED}●${NC} Backend        ${RED}не запущен${NC}"
fi

# Celery
if [ -f logs/celery.pid ]; then
    CELERY_PID=$(cat logs/celery.pid)
    if ps -p $CELERY_PID > /dev/null 2>&1; then
        WORKERS=$(pgrep -f "celery.*app.celery_app" | wc -l)
        echo -e "  ${GREEN}●${NC} Celery Worker  ${GREEN}работает${NC} (PID: $CELERY_PID, workers: $WORKERS)"
    else
        echo -e "  ${RED}●${NC} Celery Worker  ${RED}не запущен${NC} (PID файл устарел)"
    fi
elif pgrep -f "celery.*app.celery_app" > /dev/null 2>&1; then
    CELERY_PID=$(pgrep -f "celery.*app.celery_app" | head -1)
    WORKERS=$(pgrep -f "celery.*app.celery_app" | wc -l)
    echo -e "  ${GREEN}●${NC} Celery Worker  ${GREEN}работает${NC} (PID: $CELERY_PID, workers: $WORKERS)"
else
    echo -e "  ${RED}●${NC} Celery Worker  ${RED}не запущен${NC}"
fi

# Frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}●${NC} Frontend       ${GREEN}работает${NC} (PID: $FRONTEND_PID, port: 3003)"
    else
        echo -e "  ${RED}●${NC} Frontend       ${RED}не запущен${NC} (PID файл устарел)"
    fi
elif pgrep -f "vite" > /dev/null 2>&1; then
    FRONTEND_PID=$(pgrep -f "vite" | head -1)
    echo -e "  ${GREEN}●${NC} Frontend       ${GREEN}работает${NC} (PID: $FRONTEND_PID)"
else
    echo -e "  ${YELLOW}●${NC} Frontend       ${YELLOW}не запущен${NC}"
fi

echo ""

# ==========================================
# Database
# ==========================================
echo -e "${CYAN}База данных:${NC}"
echo ""

if [ -f "data/db/face_recognition.db" ]; then
    DB_SIZE=$(du -h data/db/face_recognition.db 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}●${NC} SQLite         ${GREEN}доступна${NC} ($DB_SIZE)"
else
    echo -e "  ${YELLOW}●${NC} SQLite         ${YELLOW}не создана${NC}"
fi

echo ""

# ==========================================
# Resources
# ==========================================
echo -e "${CYAN}Ресурсы:${NC}"
echo ""

# Memory
MEM_TOTAL=$(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || echo "N/A")
MEM_USED=$(free -h 2>/dev/null | awk '/^Mem:/ {print $3}' || echo "N/A")
echo -e "  Память:       ${BLUE}$MEM_USED / $MEM_TOTAL${NC}"

# Disk
DISK_USED=$(df -h . 2>/dev/null | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}' || echo "N/A")
echo -e "  Диск:         ${BLUE}$DISK_USED${NC}"

# GPU
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo "N/A")
    GPU_MEM=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null | head -1 || echo "N/A")
    echo -e "  GPU:          ${BLUE}$GPU_NAME${NC}"
    echo -e "  GPU память:   ${BLUE}$GPU_MEM${NC}"
else
    echo -e "  GPU:          ${YELLOW}не обнаружен${NC}"
fi

echo ""

# ==========================================
# URLs
# ==========================================
echo -e "${CYAN}URLs:${NC}"
echo ""
echo -e "  Backend API:  ${BLUE}http://localhost:30000${NC}"
echo -e "  API Docs:     ${BLUE}http://localhost:30000/docs${NC}"
echo -e "  Frontend:     ${BLUE}http://localhost:3003${NC}"
echo -e "  Elasticsearch: ${BLUE}http://localhost:9200${NC}"
echo ""

# ==========================================
# Quick commands
# ==========================================
echo -e "${CYAN}Команды управления:${NC}"
echo ""
echo -e "  Запуск:       ${GREEN}./scripts/local_deploy.sh${NC}"
echo -e "  Перезапуск:   ${GREEN}./scripts/restart_services.sh${NC}"
echo -e "  Остановка:    ${GREEN}./scripts/stop_services.sh${NC}"
echo -e "  Health check: ${GREEN}./scripts/health_check.sh${NC}"
echo ""
echo "=========================================="
echo ""
