#!/bin/bash
# Комплексная проверка здоровья системы
# Проверяет все компоненты и их взаимодействие

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "Health Check - Face Recognition System"
echo "=========================================="
echo ""

TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNINGS=0

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((TOTAL_CHECKS++))
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
    ((TOTAL_CHECKS++))
}

# ==========================================
# 1. Infrastructure Checks
# ==========================================
echo -e "${CYAN}1. Инфраструктура${NC}"
echo ""

# Redis
if docker exec face_recognition_redis redis-cli ping > /dev/null 2>&1; then
    check_pass "Redis доступен (Docker)"
elif redis-cli ping > /dev/null 2>&1; then
    check_pass "Redis доступен (локально)"
else
    check_fail "Redis недоступен"
fi

# Elasticsearch
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    # Check cluster health
    ES_STATUS=$(curl -s http://localhost:9200/_cluster/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$ES_STATUS" = "green" ]; then
        check_pass "Elasticsearch здоров (status: green)"
    elif [ "$ES_STATUS" = "yellow" ]; then
        check_warn "Elasticsearch работает (status: yellow)"
    else
        check_warn "Elasticsearch работает (status: $ES_STATUS)"
    fi

    # Check indices
    FACES_INDEX=$(curl -s http://localhost:9200/face_embeddings 2>&1)
    if echo "$FACES_INDEX" | grep -q "face_embeddings"; then
        check_pass "Индекс face_embeddings существует"
    else
        check_warn "Индекс face_embeddings не найден"
    fi

    DOCS_INDEX=$(curl -s http://localhost:9200/documents_fulltext 2>&1)
    if echo "$DOCS_INDEX" | grep -q "documents_fulltext"; then
        check_pass "Индекс documents_fulltext существует"
    else
        check_warn "Индекс documents_fulltext не найден"
    fi
else
    check_fail "Elasticsearch недоступен"
fi

echo ""

# ==========================================
# 2. Backend API Checks
# ==========================================
echo -e "${CYAN}2. Backend API${NC}"
echo ""

# Health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:30000/health 2>&1)
if echo "$HEALTH_RESPONSE" | grep -q "healthy\|ok"; then
    check_pass "Health endpoint отвечает"

    # Parse health details
    if echo "$HEALTH_RESPONSE" | grep -q '"database"'; then
        DB_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"database"[^,}]*' | grep -o '"[^"]*"$' | tr -d '"')
        if [ "$DB_STATUS" = "connected" ] || [ "$DB_STATUS" = "ok" ]; then
            check_pass "База данных подключена"
        else
            check_warn "База данных: $DB_STATUS"
        fi
    fi

    if echo "$HEALTH_RESPONSE" | grep -q '"redis"'; then
        REDIS_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"redis"[^,}]*' | grep -o '"[^"]*"$' | tr -d '"')
        if [ "$REDIS_STATUS" = "connected" ] || [ "$REDIS_STATUS" = "ok" ]; then
            check_pass "Redis подключен к backend"
        else
            check_warn "Redis: $REDIS_STATUS"
        fi
    fi

    if echo "$HEALTH_RESPONSE" | grep -q '"elasticsearch"'; then
        ES_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"elasticsearch"[^,}]*' | grep -o '"[^"]*"$' | tr -d '"')
        if [ "$ES_STATUS" = "connected" ] || [ "$ES_STATUS" = "ok" ]; then
            check_pass "Elasticsearch подключен к backend"
        else
            check_warn "Elasticsearch: $ES_STATUS"
        fi
    fi
else
    check_fail "Backend не отвечает на /health"
fi

# Root endpoint
if curl -s http://localhost:30000/ | grep -q "Face Recognition"; then
    check_pass "Root endpoint отвечает"
else
    check_warn "Root endpoint не доступен"
fi

# API docs
if curl -s http://localhost:30000/docs > /dev/null 2>&1; then
    check_pass "API документация доступна (/docs)"
else
    check_warn "API документация недоступна"
fi

echo ""

# ==========================================
# 3. Database Checks
# ==========================================
echo -e "${CYAN}3. База данных${NC}"
echo ""

# Check SQLite file
if [ -f "data/db/face_recognition.db" ]; then
    DB_SIZE=$(du -h data/db/face_recognition.db | cut -f1)
    check_pass "SQLite файл существует ($DB_SIZE)"

    # Check if sqlite3 is available
    if command -v sqlite3 &> /dev/null; then
        # Count tables
        TABLE_COUNT=$(sqlite3 data/db/face_recognition.db "SELECT count(*) FROM sqlite_master WHERE type='table';" 2>/dev/null)
        if [ "$TABLE_COUNT" -gt 0 ]; then
            check_pass "Таблицы созданы ($TABLE_COUNT таблиц)"
        else
            check_warn "Таблицы не найдены"
        fi

        # Check users table
        USER_COUNT=$(sqlite3 data/db/face_recognition.db "SELECT count(*) FROM users;" 2>/dev/null)
        if [ "$USER_COUNT" -gt 0 ]; then
            check_pass "Пользователи существуют ($USER_COUNT)"
        else
            check_warn "Пользователи не найдены"
        fi
    fi
else
    check_fail "SQLite файл не найден"
fi

echo ""

# ==========================================
# 4. Celery Worker Checks
# ==========================================
echo -e "${CYAN}4. Celery Worker${NC}"
echo ""

# Check process
if pgrep -f "celery.*app.celery_app" > /dev/null 2>&1; then
    WORKER_COUNT=$(pgrep -f "celery.*app.celery_app" | wc -l)
    check_pass "Celery процессы запущены ($WORKER_COUNT)"
else
    check_fail "Celery worker не запущен"
fi

# Check Celery can connect to Redis
if command -v celery &> /dev/null; then
    cd backend 2>/dev/null
    CELERY_STATUS=$(timeout 5 celery -A app.celery_app inspect ping 2>&1 || true)
    cd .. 2>/dev/null

    if echo "$CELERY_STATUS" | grep -q "pong"; then
        check_pass "Celery workers отвечают"
    else
        check_warn "Celery workers не отвечают (возможно запускаются)"
    fi
fi

echo ""

# ==========================================
# 5. Frontend Checks
# ==========================================
echo -e "${CYAN}5. Frontend${NC}"
echo ""

if curl -s http://localhost:3003 > /dev/null 2>&1; then
    check_pass "Frontend доступен на port 3003"
elif pgrep -f "vite" > /dev/null 2>&1; then
    check_warn "Frontend процесс запущен, но не отвечает"
else
    check_warn "Frontend не запущен"
fi

echo ""

# ==========================================
# 6. File System Checks
# ==========================================
echo -e "${CYAN}6. Файловая система${NC}"
echo ""

# Check directories
if [ -d "data/uploads" ]; then
    check_pass "Директория uploads существует"
else
    check_fail "Директория uploads не найдена"
fi

if [ -d "logs" ]; then
    check_pass "Директория logs существует"
else
    check_warn "Директория logs не найдена"
fi

if [ -f ".env" ]; then
    check_pass "Файл .env существует"
else
    check_warn "Файл .env не найден"
fi

# Check disk space
DISK_AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
DISK_PERCENT=$(df -h . | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_PERCENT" -lt 90 ]; then
    check_pass "Место на диске достаточно ($DISK_AVAILABLE доступно)"
else
    check_warn "Мало места на диске ($DISK_AVAILABLE доступно, использовано $DISK_PERCENT%)"
fi

echo ""

# ==========================================
# 7. GPU Checks (if available)
# ==========================================
if command -v nvidia-smi &> /dev/null; then
    echo -e "${CYAN}7. GPU${NC}"
    echo ""

    GPU_STATUS=$(nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>&1)
    if [ $? -eq 0 ]; then
        check_pass "GPU доступен: $GPU_STATUS"

        # Check PyTorch CUDA
        if python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
            check_pass "PyTorch CUDA работает"
        else
            check_warn "PyTorch CUDA недоступен"
        fi
    else
        check_warn "GPU недоступен"
    fi

    echo ""
fi

# ==========================================
# Summary
# ==========================================
echo "=========================================="
echo -e "${CYAN}Результат${NC}"
echo "=========================================="
echo ""

FAILED=$((TOTAL_CHECKS - PASSED_CHECKS - WARNINGS))

echo -e "  Всего проверок:  ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "  Успешно:         ${GREEN}$PASSED_CHECKS${NC}"
echo -e "  Предупреждений:  ${YELLOW}$WARNINGS${NC}"
echo -e "  Ошибок:          ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}Система полностью работоспособна!${NC}"
    EXIT_CODE=0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}Система работает с предупреждениями${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}Обнаружены проблемы!${NC}"
    echo ""
    echo "Рекомендации:"
    echo -e "  1. Проверьте логи: ${BLUE}tail -f logs/*.log${NC}"
    echo -e "  2. Перезапустите сервисы: ${GREEN}./scripts/restart_services.sh${NC}"
    echo -e "  3. Проверьте Docker: ${GREEN}docker ps${NC}"
    EXIT_CODE=1
fi

echo ""
echo "=========================================="
echo ""

exit $EXIT_CODE
