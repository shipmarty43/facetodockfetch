#!/bin/bash
# Полный локальный деплой системы
# Docker используется только для Redis и Elasticsearch
# Backend, Celery и Frontend запускаются локально

set -e

# Suppress warnings
export PYTHONWARNINGS="ignore::UserWarning:passlib"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

# Banner
echo ""
echo "=========================================="
echo "Face Recognition & OCR System"
echo "Локальный деплой (Docker: Redis + ES)"
echo "=========================================="
echo ""

# Check directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Запустите скрипт из корневой директории проекта"
    echo "Текущая директория: $(pwd)"
    exit 1
fi

PROJECT_ROOT=$(pwd)

# ==========================================
# STEP 1: Check Python environment
# ==========================================
print_step "Шаг 1/6: Проверка Python окружения"

# Check for Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "Python не найден!"
    echo "Установите Python 3.10+"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
print_info "Python: $PYTHON_VERSION"

# Check if we're in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    print_info "Virtual environment активен: $VIRTUAL_ENV"
elif [[ "$CONDA_DEFAULT_ENV" != "" ]] && [[ "$CONDA_DEFAULT_ENV" != "base" ]]; then
    print_info "Conda окружение активно: $CONDA_DEFAULT_ENV"
else
    print_warn "Python окружение не активировано"
    echo ""
    echo "Рекомендуется использовать виртуальное окружение:"
    echo ""
    echo "  Вариант 1 - venv:"
    echo "    python3 -m venv venv"
    echo "    source venv/bin/activate"
    echo ""
    echo "  Вариант 2 - Conda:"
    echo "    conda activate face-recognition-system"
    echo ""
    read -p "Продолжить с системным Python? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# ==========================================
# STEP 2: Install Python dependencies
# ==========================================
print_step "Шаг 2/6: Проверка/установка Python зависимостей"

cd backend

# Check if key dependencies are installed
if $PYTHON_CMD -c "import fastapi, uvicorn, celery, redis, elasticsearch" 2>/dev/null; then
    print_info "Основные зависимости установлены"
else
    print_info "Установка зависимостей..."
    pip install -r requirements.txt
    print_success "Зависимости установлены"
fi

cd ..
echo ""

# ==========================================
# STEP 3: Create configuration
# ==========================================
print_step "Шаг 3/6: Настройка конфигурации"

# Create .env file
if [ ! -f ".env" ]; then
    print_info "Создание .env файла..."
    cp .env.example .env
    print_success ".env файл создан"
    print_warn "Проверьте настройки в .env файле"
else
    print_info ".env файл существует"
fi

# Create directories
print_info "Создание директорий..."
mkdir -p data/uploads data/db data/cache logs models
print_success "Директории созданы"
echo ""

# ==========================================
# STEP 4: Start Docker infrastructure
# ==========================================
print_step "Шаг 4/6: Запуск инфраструктуры (Docker: Redis + ES)"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker не установлен!"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Detect docker-compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    print_error "docker-compose недоступен!"
    exit 1
fi

print_info "Используется: $COMPOSE_CMD"

# Stop existing containers
print_info "Остановка существующих контейнеров..."
$COMPOSE_CMD -f docker-compose.infrastructure.yml down 2>/dev/null || true

# Start infrastructure
print_info "Запуск Redis и Elasticsearch..."
$COMPOSE_CMD -f docker-compose.infrastructure.yml up -d

# Wait for Redis
print_info "Ожидание Redis..."
for i in {1..30}; do
    if docker exec face_recognition_redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis готов"
        break
    fi
    sleep 1
done

# Wait for Elasticsearch
print_info "Ожидание Elasticsearch (до 60 сек)..."
for i in {1..60}; do
    if curl -s http://localhost:9200 > /dev/null 2>&1; then
        ES_VERSION=$(curl -s http://localhost:9200 | grep -o '"number" : "[^"]*"' | cut -d'"' -f4)
        print_success "Elasticsearch готов (v$ES_VERSION)"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# ==========================================
# STEP 5: Initialize databases
# ==========================================
print_step "Шаг 5/6: Инициализация баз данных"

cd backend

# Initialize SQLite
print_info "Инициализация SQLite..."
$PYTHON_CMD scripts/init_db.py
print_success "SQLite инициализирована"

# Initialize Elasticsearch
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    print_info "Инициализация Elasticsearch..."
    $PYTHON_CMD scripts/init_elasticsearch.py
    print_success "Elasticsearch инициализирован"
fi

# Create admin user
print_info "Создание администратора..."
$PYTHON_CMD scripts/create_admin.py --username "admin" --password "admin123" 2>/dev/null || true
print_success "Администратор создан/проверен"

cd ..
echo ""

# ==========================================
# STEP 6: Start services
# ==========================================
print_step "Шаг 6/6: Запуск сервисов"

# Stop existing services
./scripts/stop_services.sh 2>/dev/null || true

# Create log directory
mkdir -p logs

# Start backend
print_info "Запуск Backend API (port 30000)..."
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
    print_info "Запуск Frontend (port 3003)..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_info "Установка зависимостей frontend..."
        npm install
    fi
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
    print_success "Frontend запущен"
else
    print_warn "npm не найден - frontend пропущен"
fi

sleep 2

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo "=========================================="
echo -e "${GREEN}СИСТЕМА ЗАПУЩЕНА!${NC}"
echo "=========================================="
echo ""
echo -e "${CYAN}Docker контейнеры:${NC}"
echo -e "  ${BLUE}Redis:${NC}         localhost:6379"
echo -e "  ${BLUE}Elasticsearch:${NC} http://localhost:9200"
echo ""
echo -e "${CYAN}Локальные сервисы:${NC}"
echo -e "  ${BLUE}Backend API:${NC}   http://localhost:30000"
echo -e "  ${BLUE}API Docs:${NC}      http://localhost:30000/docs"
echo -e "  ${BLUE}Frontend:${NC}      http://localhost:3003"
echo ""
echo -e "${CYAN}Учетные данные:${NC}"
echo -e "  Username: ${GREEN}admin${NC}"
echo -e "  Password: ${GREEN}admin123${NC}"
echo ""
echo -e "${CYAN}Логи:${NC}"
echo -e "  Backend:  ${BLUE}tail -f logs/backend.log${NC}"
echo -e "  Celery:   ${BLUE}tail -f logs/celery.log${NC}"
echo -e "  Frontend: ${BLUE}tail -f logs/frontend.log${NC}"
echo ""
echo -e "${CYAN}Управление:${NC}"
echo -e "  Статус:              ${GREEN}./scripts/status.sh${NC}"
echo -e "  Остановить сервисы:  ${GREEN}./scripts/stop_services.sh${NC}"
echo -e "  Остановить Docker:   ${GREEN}./scripts/stop_infrastructure.sh${NC}"
echo -e "  Перезапуск:          ${GREEN}./scripts/restart_services.sh${NC}"
echo -e "  Health check:        ${GREEN}./scripts/health_check.sh${NC}"
echo ""
echo "=========================================="
