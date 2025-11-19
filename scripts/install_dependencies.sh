#!/bin/bash
# Установка Python зависимостей для локального деплоя
# Поддерживает venv и conda окружения

set -e

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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "=========================================="
echo "Установка зависимостей"
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
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    print_error "Python не найден!"
    exit 1
fi

print_info "Python: $($PYTHON_CMD --version)"

# Check environment
if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" || "$CONDA_DEFAULT_ENV" == "base" ]]; then
    print_warn "Виртуальное окружение не активно!"
    echo ""
    echo "Создать и активировать venv?"
    read -p "[y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Создание venv..."
        $PYTHON_CMD -m venv venv
        source venv/bin/activate
        print_info "venv активирован"
        # Update pip
        pip install --upgrade pip
    fi
fi

# ==========================================
# Install system dependencies (if on Linux)
# ==========================================
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_step "Проверка системных зависимостей..."

    MISSING_DEPS=""

    # Check for required system packages
    if ! dpkg -l | grep -q libpoppler-cpp-dev 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS libpoppler-cpp-dev"
    fi

    if ! dpkg -l | grep -q poppler-utils 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS poppler-utils"
    fi

    if ! dpkg -l | grep -q libgl1 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS libgl1"
    fi

    if [ -n "$MISSING_DEPS" ]; then
        print_warn "Некоторые системные пакеты могут отсутствовать"
        echo "Рекомендуется установить:"
        echo -e "  ${GREEN}sudo apt-get install -y libpoppler-cpp-dev poppler-utils libgl1 libglib2.0-0${NC}"
        echo ""
    else
        print_info "Системные зависимости в порядке"
    fi
fi

# ==========================================
# Install Python dependencies
# ==========================================
print_step "Установка Python зависимостей..."

cd backend

# Upgrade pip first
print_info "Обновление pip..."
$PIP_CMD install --upgrade pip

# Install main requirements
print_info "Установка основных зависимостей..."
$PIP_CMD install -r requirements.txt

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    print_info "Обнаружен GPU"

    if [ -f "requirements-gpu.txt" ]; then
        read -p "Установить GPU зависимости? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Установка GPU зависимостей..."
            $PIP_CMD install -r requirements-gpu.txt
        fi
    fi
else
    print_warn "GPU не обнаружен - будет использоваться CPU"
fi

cd ..

# ==========================================
# Install frontend dependencies
# ==========================================
if command -v npm &> /dev/null; then
    print_step "Установка frontend зависимостей..."
    cd frontend
    npm install
    cd ..
    print_info "Frontend зависимости установлены"
else
    print_warn "npm не найден - frontend зависимости пропущены"
    echo "Установите Node.js: https://nodejs.org/"
fi

# ==========================================
# Verify installation
# ==========================================
echo ""
print_step "Проверка установки..."

cd backend

# Check critical imports
CHECKS_PASSED=true

if $PYTHON_CMD -c "import fastapi" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} FastAPI"
else
    echo -e "  ${RED}✗${NC} FastAPI"
    CHECKS_PASSED=false
fi

if $PYTHON_CMD -c "import uvicorn" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Uvicorn"
else
    echo -e "  ${RED}✗${NC} Uvicorn"
    CHECKS_PASSED=false
fi

if $PYTHON_CMD -c "import celery" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Celery"
else
    echo -e "  ${RED}✗${NC} Celery"
    CHECKS_PASSED=false
fi

if $PYTHON_CMD -c "import redis" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Redis"
else
    echo -e "  ${RED}✗${NC} Redis"
    CHECKS_PASSED=false
fi

if $PYTHON_CMD -c "import elasticsearch" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Elasticsearch"
else
    echo -e "  ${RED}✗${NC} Elasticsearch"
    CHECKS_PASSED=false
fi

if $PYTHON_CMD -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$($PYTHON_CMD -c "import torch; print(torch.__version__)")
    echo -e "  ${GREEN}✓${NC} PyTorch ($TORCH_VERSION)"

    # Check CUDA
    if $PYTHON_CMD -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
        CUDA_VERSION=$($PYTHON_CMD -c "import torch; print(torch.version.cuda)")
        echo -e "    ${GREEN}✓${NC} CUDA доступен ($CUDA_VERSION)"
    else
        echo -e "    ${YELLOW}⚠${NC} CUDA недоступен"
    fi
else
    echo -e "  ${RED}✗${NC} PyTorch"
    CHECKS_PASSED=false
fi

if $PYTHON_CMD -c "import insightface" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} InsightFace"
else
    echo -e "  ${YELLOW}⚠${NC} InsightFace (опционально)"
fi

if $PYTHON_CMD -c "import surya" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Surya OCR"
else
    echo -e "  ${YELLOW}⚠${NC} Surya OCR (опционально)"
fi

cd ..

echo ""
if [ "$CHECKS_PASSED" = true ]; then
    echo "=========================================="
    echo -e "${GREEN}Зависимости установлены успешно!${NC}"
    echo "=========================================="
    echo ""
    echo "Следующие шаги:"
    echo -e "  1. ${GREEN}./scripts/start_infrastructure.sh${NC} - запуск Docker"
    echo -e "  2. ${GREEN}./scripts/init_all.sh${NC} - инициализация БД"
    echo -e "  3. ${GREEN}./scripts/start_services.sh${NC} - запуск сервисов"
    echo ""
    echo "Или одной командой:"
    echo -e "  ${GREEN}./scripts/local_deploy.sh${NC}"
else
    echo "=========================================="
    echo -e "${RED}Некоторые зависимости не установлены!${NC}"
    echo "=========================================="
    echo ""
    echo "Попробуйте:"
    echo -e "  ${GREEN}pip install -r backend/requirements.txt${NC}"
fi
echo ""
