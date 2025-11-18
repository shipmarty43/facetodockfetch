#!/bin/bash
# Quick Native Setup - Быстрая установка без Docker
# Автоматическая установка всего необходимого для нативного запуска

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

echo "=========================================="
echo "Face Recognition & OCR System"
echo "Quick Native Setup (без Docker)"
echo "=========================================="
echo ""

# 1. Проверка conda
print_step "Проверка Conda..."
if ! command -v conda &> /dev/null; then
    print_error "Conda не установлен!"
    echo "Установите Miniconda:"
    echo "  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "  bash Miniconda3-latest-Linux-x86_64.sh"
    exit 1
fi
print_success "Conda установлен: $(conda --version)"

# 2. Проверка GPU (опционально)
print_step "Проверка GPU..."
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU обнаружен"
    nvidia-smi --query-gpu=name --format=csv,noheader
    USE_GPU=true
else
    print_warning "NVIDIA GPU не обнаружен - будет использован CPU"
    USE_GPU=false
fi

# 3. Создание conda окружения
print_step "Создание conda окружения..."
if conda env list | grep -q "face-recognition-system"; then
    print_warning "Окружение уже существует"
    read -p "Пересоздать окружение? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        conda env remove -n face-recognition-system -y
    else
        print_success "Используем существующее окружение"
    fi
fi

if ! conda env list | grep -q "face-recognition-system"; then
    if [ "$USE_GPU" = true ]; then
        print_step "Создание GPU окружения..."
        conda env create -f environment-gpu.yml
    else
        print_step "Создание CPU окружения..."
        conda env create -f environment.yml
    fi
    print_success "Conda окружение создано"
fi

# 4. Проверка Redis
print_step "Проверка Redis..."
if systemctl is-active --quiet redis-server 2>/dev/null; then
    print_success "Redis уже запущен (системный)"
elif docker ps | grep -q redis 2>/dev/null; then
    print_success "Redis уже запущен (Docker)"
elif redis-cli ping &> /dev/null; then
    print_success "Redis доступен"
else
    print_warning "Redis не запущен"
    echo "Выберите вариант установки Redis:"
    echo "  1) Docker (рекомендуется)"
    echo "  2) Системный пакет"
    echo "  3) Пропустить (настрою вручную)"
    read -p "Выбор [1-3]: " redis_choice

    case $redis_choice in
        1)
            print_step "Запуск Redis через Docker..."
            docker run -d --name face-recognition-redis \
                -p 6379:6379 \
                --restart unless-stopped \
                redis:7-alpine
            print_success "Redis запущен через Docker"
            ;;
        2)
            print_step "Установка Redis (системный)..."
            sudo apt-get update
            sudo apt-get install -y redis-server
            sudo systemctl start redis-server
            sudo systemctl enable redis-server
            print_success "Redis установлен и запущен"
            ;;
        *)
            print_warning "Redis пропущен - настройте вручную!"
            ;;
    esac
fi

# 5. Проверка Elasticsearch
print_step "Проверка Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    print_success "Elasticsearch уже запущен"
else
    print_warning "Elasticsearch не запущен"
    echo "Выберите вариант установки Elasticsearch:"
    echo "  1) Docker (рекомендуется)"
    echo "  2) Системный пакет"
    echo "  3) Пропустить (настрою вручную)"
    read -p "Выбор [1-3]: " es_choice

    case $es_choice in
        1)
            print_step "Запуск Elasticsearch через Docker..."
            docker run -d --name face-recognition-elasticsearch \
                -p 9200:9200 -p 9300:9300 \
                -e "discovery.type=single-node" \
                -e "xpack.security.enabled=false" \
                -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \
                --restart unless-stopped \
                docker.elastic.co/elasticsearch/elasticsearch:8.10.0

            print_step "Ожидание запуска Elasticsearch..."
            for i in {1..30}; do
                if curl -s http://localhost:9200 > /dev/null 2>&1; then
                    print_success "Elasticsearch запущен"
                    break
                fi
                echo -n "."
                sleep 2
            done
            echo ""
            ;;
        2)
            print_step "Установка Elasticsearch (системный)..."
            wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | \
                sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
            echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | \
                sudo tee /etc/apt/sources.list.d/elastic-8.x.list
            sudo apt-get update
            sudo apt-get install -y elasticsearch

            # Настройка
            echo "discovery.type: single-node" | sudo tee -a /etc/elasticsearch/elasticsearch.yml
            echo "xpack.security.enabled: false" | sudo tee -a /etc/elasticsearch/elasticsearch.yml

            sudo systemctl start elasticsearch
            sudo systemctl enable elasticsearch
            print_success "Elasticsearch установлен и запущен"
            ;;
        *)
            print_warning "Elasticsearch пропущен - настройте вручную!"
            ;;
    esac
fi

# 6. Создание директорий
print_step "Создание директорий..."
mkdir -p data/uploads data/db data/cache logs models
print_success "Директории созданы"

# 7. Создание .env файла
print_step "Создание .env файла..."
if [ ! -f .env ]; then
    cp .env.example .env

    # Добавить GPU настройку
    if [ "$USE_GPU" = true ]; then
        echo "USE_GPU=true" >> .env
    else
        echo "USE_GPU=false" >> .env
    fi

    print_success ".env файл создан"
    print_warning "Отредактируйте .env и установите SECRET_KEY!"
else
    print_success ".env файл уже существует"
fi

# 8. Инициализация баз данных
print_step "Инициализация баз данных..."
eval "$(conda shell.bash hook)"
conda activate face-recognition-system

cd backend

# Проверка подключения к Elasticsearch
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    print_step "Инициализация Elasticsearch..."
    python scripts/init_elasticsearch.py || print_warning "Ошибка инициализации Elasticsearch"
else
    print_warning "Elasticsearch недоступен - пропуск инициализации"
fi

print_step "Инициализация SQLite..."
python scripts/init_db.py || print_warning "База данных уже инициализирована"

cd ..

print_success "Базы данных инициализированы"

# 9. Создание администратора
print_step "Создание администратора..."
read -p "Создать администратора? [Y/n]: " create_admin
if [[ ! $create_admin =~ ^[Nn]$ ]]; then
    read -p "Username [admin]: " admin_user
    admin_user=${admin_user:-admin}

    read -s -p "Password [admin123]: " admin_pass
    admin_pass=${admin_pass:-admin123}
    echo ""

    cd backend
    python scripts/create_admin.py --username "$admin_user" --password "$admin_pass" || \
        print_warning "Администратор уже существует или ошибка создания"
    cd ..
    print_success "Администратор создан"
fi

# 10. Сводка
echo ""
echo "=========================================="
echo "Установка завершена!"
echo "=========================================="
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Активировать окружение:"
echo "   ${GREEN}conda activate face-recognition-system${NC}"
echo ""
echo "2. Запустить сервисы:"
echo "   ${GREEN}./scripts/start_services.sh${NC}"
echo ""
echo "3. Проверить работу:"
echo "   ${GREEN}curl http://localhost:30000/health${NC}"
echo ""
echo "4. Открыть в браузере:"
echo "   Frontend:  ${BLUE}http://localhost:3003${NC}"
echo "   Backend:   ${BLUE}http://localhost:30000/docs${NC}"
echo ""
echo "5. Остановить сервисы:"
echo "   ${GREEN}./scripts/stop_services.sh${NC}"
echo ""

if [ "$USE_GPU" = true ]; then
    echo "GPU поддержка: ${GREEN}ВКЛЮЧЕНА${NC}"
    echo "Проверить GPU:"
    echo "   ${GREEN}python -c 'import torch; print(torch.cuda.is_available())'${NC}"
    echo ""
fi

echo "Документация:"
echo "  📖 ${BLUE}NATIVE_SETUP.md${NC} - Полное руководство"
echo "  📖 ${BLUE}README.md${NC} - Общая документация"
echo "  🎮 ${BLUE}GPU_SETUP.md${NC} - Настройка GPU"
echo ""

print_success "Готово к работе!"
