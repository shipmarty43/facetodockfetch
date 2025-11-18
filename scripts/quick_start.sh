#!/bin/bash
# Полная автоматическая инициализация и запуск системы
# Объединяет: setup_conda → start_infrastructure → init_all → start_services

set -e

# Suppress bcrypt version warnings globally
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
echo "Быстрый старт - Полная инициализация"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Запустите скрипт из корневой директории проекта"
    echo "Текущая директория: $(pwd)"
    exit 1
fi

PROJECT_ROOT=$(pwd)

# ==========================================
# STEP 1: Check/Setup Conda Environment
# ==========================================
print_step "Шаг 1/5: Проверка Conda окружения"

if ! command -v conda &> /dev/null; then
    print_error "Conda не установлена!"
    echo "Установите Anaconda или Miniconda:"
    echo "https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

print_info "✓ Conda найдена: $(conda --version)"

ENV_NAME="face-recognition-system"

if conda env list | grep -q "^${ENV_NAME} "; then
    print_info "✓ Окружение '$ENV_NAME' уже существует"
else
    print_info "Создание окружения '$ENV_NAME'..."

    # Check for GPU
    if command -v nvidia-smi &> /dev/null; then
        print_info "Обнаружен GPU - используется полная конфигурация"
        nvidia-smi --query-gpu=name --format=csv,noheader | head -1
    else
        print_warn "GPU не обнаружен - будет использоваться CPU"
    fi

    # Create environment
    conda env create -f environment.yml
    print_success "✓ Окружение создано"
fi

# Activate environment
print_info "Активация окружения..."
eval "$(conda shell.bash hook)"
conda activate ${ENV_NAME}

if [[ "$CONDA_DEFAULT_ENV" != "${ENV_NAME}" ]]; then
    print_error "Не удалось активировать окружение"
    exit 1
fi

print_success "✓ Окружение активировано: $CONDA_DEFAULT_ENV"
echo ""

# ==========================================
# STEP 2: Create .env file
# ==========================================
print_step "Шаг 2/5: Настройка конфигурации"

if [ ! -f ".env" ]; then
    print_info "Создание .env файла из .env.example..."
    cp .env.example .env
    print_success "✓ .env файл создан"
    print_warn "⚠ Проверьте настройки в .env файле"
else
    print_info "✓ .env файл уже существует"
fi

# Create directories
print_info "Создание необходимых директорий..."
mkdir -p data/uploads data/db data/cache logs models
print_success "✓ Директории созданы"
echo ""

# ==========================================
# STEP 3: Start Infrastructure (Docker)
# ==========================================
print_step "Шаг 3/5: Запуск инфраструктуры (Redis + Elasticsearch)"

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
print_info "Ожидание готовности Redis..."
for i in {1..30}; do
    if docker exec face_recognition_redis redis-cli ping > /dev/null 2>&1; then
        print_success "✓ Redis готов"
        break
    fi
    sleep 1
done

# Wait for Elasticsearch
print_info "Ожидание готовности Elasticsearch (может занять 30-60 сек)..."
for i in {1..60}; do
    if curl -s http://localhost:9200 > /dev/null 2>&1; then
        ES_VERSION=$(curl -s http://localhost:9200 | grep -o '"number" : "[^"]*"' | cut -d'"' -f4)
        print_success "✓ Elasticsearch готов (версия: $ES_VERSION)"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# ==========================================
# STEP 4: Initialize Database and Services
# ==========================================
print_step "Шаг 4/5: Инициализация базы данных и сервисов"

# Check dependencies
print_info "Проверка критических зависимостей..."
cd backend
if python -c "import passlib, bcrypt, sqlalchemy, fastapi" 2>/dev/null; then
    print_success "✓ Критические зависимости установлены"
else
    print_warn "⚠ Некоторые зависимости могут отсутствовать"
    echo "  Запустите для проверки: python scripts/check_dependencies.py"
fi
cd ..

# Initialize SQLite database
print_info "Инициализация SQLite базы данных..."
cd backend
python scripts/init_db.py
if [ $? -eq 0 ]; then
    print_success "✓ База данных инициализирована"
else
    print_error "✗ Ошибка инициализации базы данных"
    exit 1
fi

# Initialize Elasticsearch
print_info "Инициализация Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    python scripts/init_elasticsearch.py
    if [ $? -eq 0 ]; then
        print_success "✓ Elasticsearch инициализирован"
    else
        print_warn "⚠ Elasticsearch инициализация не удалась (не критично)"
    fi
else
    print_warn "⚠ Пропуск инициализации Elasticsearch (не запущен)"
fi

# Create default admin user
print_info "Создание администратора по умолчанию..."
DEFAULT_USERNAME="admin"
DEFAULT_PASSWORD="admin123"

python scripts/create_admin.py --username "$DEFAULT_USERNAME" --password "$DEFAULT_PASSWORD"
if [ $? -eq 0 ]; then
    print_success "✓ Администратор создан/проверен"
else
    print_warn "⚠ Создание администратора не удалось (возможно уже существует)"
fi

cd ..
echo ""

# ==========================================
# STEP 5: Start Services
# ==========================================
print_step "Шаг 5/5: Запуск сервисов"

# Create log directory
mkdir -p logs

# Start backend
print_info "Запуск backend на http://localhost:30000..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 30000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
cd ..

# Wait for backend to start
sleep 3

# Start Celery worker
print_info "Запуск Celery worker..."
cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=4 > ../logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > ../logs/celery.pid
cd ..

# Start frontend (if npm is available)
if command -v npm &> /dev/null; then
    print_info "Запуск frontend на http://localhost:3003..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_info "Установка зависимостей frontend..."
        npm install
    fi
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
    print_success "✓ Frontend запущен"
else
    print_warn "npm не найден - frontend пропущен"
fi

# Wait a bit for services to start
sleep 2

echo ""
echo "=========================================="
echo -e "${GREEN}✓ СИСТЕМА ПОЛНОСТЬЮ ЗАПУЩЕНА!${NC}"
echo "=========================================="
echo ""
echo -e "${CYAN}Сервисы:${NC}"
echo -e "  ${BLUE}Backend API:${NC} http://localhost:30000"
echo -e "  ${BLUE}API Docs:${NC} http://localhost:30000/docs"
echo -e "  ${BLUE}Frontend:${NC} http://localhost:3003"
echo ""
echo -e "${CYAN}Учётные данные администратора:${NC}"
echo -e "  ${GREEN}Username:${NC} admin"
echo -e "  ${GREEN}Password:${NC} admin123"
echo -e "  ${YELLOW}⚠ ОБЯЗАТЕЛЬНО смените пароль в production!${NC}"
echo ""
echo -e "${CYAN}Логи:${NC}"
echo -e "  Backend:  ${BLUE}tail -f logs/backend.log${NC}"
echo -e "  Celery:   ${BLUE}tail -f logs/celery.log${NC}"
echo -e "  Frontend: ${BLUE}tail -f logs/frontend.log${NC}"
echo ""
echo -e "${CYAN}Управление:${NC}"
echo -e "  Остановить сервисы:      ${GREEN}./scripts/stop_services.sh${NC}"
echo -e "  Остановить инфраструктуру: ${GREEN}./scripts/stop_infrastructure.sh${NC}"
echo -e "  Проверить здоровье:      ${BLUE}curl http://localhost:30000/health${NC}"
echo ""
echo -e "${CYAN}Проверка GPU:${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "  ${GREEN}nvidia-smi${NC}"
    echo -e "  ${BLUE}curl http://localhost:30000/health${NC} (должен показать GPU status)"
else
    echo -e "  ${YELLOW}GPU не обнаружен - работа в CPU режиме${NC}"
fi
echo ""
echo "=========================================="
echo -e "${GREEN}Готово к работе! 🚀${NC}"
echo "=========================================="
echo ""
