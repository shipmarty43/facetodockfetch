#!/bin/bash
# Быстрый старт БЕЗ Conda и Docker
# Для окружений типа Codespaces, GitPod, или чистого Python

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
echo "Быстрый старт БЕЗ Conda/Docker"
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
# STEP 1: Check Python
# ==========================================
print_step "Шаг 1/5: Проверка Python"

if ! command -v python3 &> /dev/null; then
    print_error "Python3 не найден!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_info "✓ Python найден: $PYTHON_VERSION"

# ==========================================
# STEP 2: Install Dependencies
# ==========================================
print_step "Шаг 2/5: Установка зависимостей"

cd backend

print_info "Установка основных пакетов..."
pip3 install -q fastapi uvicorn sqlalchemy pydantic pydantic-settings \
             passlib bcrypt python-jose cryptography pillow numpy \
             python-multipart redis elasticsearch celery aiofiles \
             python-dotenv requests aiohttp pytesseract mrz \
             scikit-learn pandas pdf2image opencv-python

print_success "✓ Зависимости установлены"
cd ..

# ==========================================
# STEP 3: Create directories and .env
# ==========================================
print_step "Шаг 3/5: Создание директорий и конфигурации"

mkdir -p data/uploads data/db data/cache logs models
print_info "✓ Директории созданы"

if [ ! -f ".env" ]; then
    cp .env.example .env
    print_info "✓ .env файл создан"
else
    print_info "✓ .env файл уже существует"
fi

# ==========================================
# STEP 4: Initialize Database
# ==========================================
print_step "Шаг 4/5: Инициализация базы данных"

cd backend

# Check if database exists
if [ -f "../data/db/face_recognition.db" ]; then
    print_info "База данных уже существует"
else
    print_info "Создание базы данных..."
    python3 scripts/init_db.py
fi

# Create admin user
print_info "Создание/обновление admin пользователя..."
python3 scripts/create_admin.py --username admin --password admin123 --force

print_success "✓ База данных готова"
cd ..

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

print_success "✓ Backend запущен (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 3

# Check backend health
if curl -s http://localhost:30000/health > /dev/null 2>&1; then
    print_success "✓ Backend работает"
else
    print_warn "⚠ Backend может быть еще не готов (подождите 5-10 секунд)"
fi

# Optional: Start frontend (if npm is available)
if command -v npm &> /dev/null; then
    print_info "Запуск frontend на http://localhost:3003..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_info "Установка frontend зависимостей..."
        npm install
    fi
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    print_success "✓ Frontend запущен (PID: $FRONTEND_PID)"
    cd ..
else
    print_warn "⚠ npm не найден, frontend не запущен"
    print_info "Установите Node.js для запуска frontend"
fi

# ==========================================
# Summary
# ==========================================
echo ""
echo "=========================================="
print_success "Система запущена!"
echo "=========================================="
echo ""
echo -e "${BLUE}Доступ:${NC}"
echo -e "  - Backend API: ${CYAN}http://localhost:30000${NC}"
echo -e "  - API Docs: ${CYAN}http://localhost:30000/docs${NC}"
if command -v npm &> /dev/null; then
    echo -e "  - Frontend: ${CYAN}http://localhost:3003${NC}"
fi
echo ""
echo -e "${BLUE}Логин:${NC}"
echo -e "  - Username: ${GREEN}admin${NC}"
echo -e "  - Password: ${GREEN}admin123${NC}"
echo ""
echo -e "${YELLOW}⚠ ВАЖНО: Смените пароль в продакшене!${NC}"
echo ""
echo "Логи:"
echo "  - Backend: tail -f logs/backend.log"
if command -v npm &> /dev/null; then
    echo "  - Frontend: tail -f logs/frontend.log"
fi
echo ""
echo "Остановка:"
echo "  ./scripts/stop_services.sh"
echo ""
echo -e "${CYAN}Примечание:${NC} Redis и Elasticsearch не запущены"
echo "  - Celery задачи не будут работать"
echo "  - Поиск по лицам будет ограничен"
echo "  - Но базовая авторизация и API работают ✓"
echo ""
