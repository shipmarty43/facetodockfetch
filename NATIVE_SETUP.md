# Запуск без Docker - Нативная установка

Руководство по запуску Face Recognition & OCR System напрямую на хосте без Docker.

## Преимущества нативного запуска

✅ **Прямой доступ к GPU** - без Docker overhead
✅ **Проще отладка** - все логи доступны напрямую
✅ **Быстрее итерации** - не нужно пересобирать контейнеры
✅ **Лучше для разработки** - hot reload работает быстрее

## Системные требования

- Ubuntu 20.04+ / Debian 11+
- Python 3.10 или 3.11
- Conda (Anaconda или Miniconda)
- NVIDIA GPU + драйверы (опционально, для GPU версии)
- Redis server
- Elasticsearch 8.x

---

## Быстрый старт

### 1. Установка Conda (если не установлен)

```bash
# Скачать Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Установить
bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda3

# Активировать
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

### 2. Клонирование проекта

```bash
git clone https://github.com/shipmarty43/facetodockfetch.git
cd facetodockfetch
```

### 3. Автоматическая настройка окружения

```bash
# Запустить скрипт установки
./scripts/setup_conda.sh

# Скрипт спросит про GPU - выберите yes если есть NVIDIA GPU
```

### 4. Установка внешних сервисов

#### Redis (вариант 1: системный пакет)

```bash
sudo apt-get update
sudo apt-get install -y redis-server

# Запустить Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверка
redis-cli ping  # Должно ответить PONG
```

#### Redis (вариант 2: через Docker)

```bash
docker run -d --name redis \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7-alpine
```

#### Elasticsearch (вариант 1: через Docker - рекомендуется)

```bash
docker run -d --name elasticsearch \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \
  --restart unless-stopped \
  docker.elastic.co/elasticsearch/elasticsearch:8.10.0

# Проверка
curl http://localhost:9200
```

#### Elasticsearch (вариант 2: системная установка)

```bash
# Добавить репозиторий Elasticsearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | \
  sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# Установить
sudo apt-get update
sudo apt-get install -y elasticsearch

# Настроить
sudo tee -a /etc/elasticsearch/elasticsearch.yml > /dev/null <<EOF
discovery.type: single-node
xpack.security.enabled: false
EOF

# Запустить
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

### 5. Инициализация базы данных

```bash
# Активировать окружение
conda activate face-recognition-system

# Создать директории
mkdir -p data/uploads data/db data/cache logs models

# Инициализировать SQLite
cd backend
python -c "from app.database import init_db; init_db()"

# Инициализировать Elasticsearch
python scripts/init_elasticsearch.py

# Создать администратора
python scripts/create_admin.py --username admin --password admin123
```

### 6. Создать .env файл

```bash
cd /home/admin1/facetodockfetch  # или ваш путь

# Скопировать пример
cp .env.example .env

# Отредактировать .env
nano .env
```

**Минимальная конфигурация .env:**

```env
# Mode
MODE=debug

# Database
DATABASE_URL=sqlite:///./data/db/face_recognition.db

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-change-in-production

# GPU (если есть NVIDIA GPU)
USE_GPU=true
```

### 7. Запуск сервисов

Используйте автоматический скрипт:

```bash
# Запустить все сервисы (backend + celery + frontend)
./scripts/start_services.sh

# Остановить все сервисы
./scripts/stop_services.sh
```

Или запустите вручную в отдельных терминалах:

#### Терминал 1: Backend

```bash
cd /home/admin1/facetodockfetch
conda activate face-recognition-system

cd backend
uvicorn app.main:app --host 0.0.0.0 --port 30000 --reload
```

#### Терминал 2: Celery Worker

```bash
cd /home/admin1/facetodockfetch
conda activate face-recognition-system

cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

#### Терминал 3: Frontend (опционально)

```bash
cd /home/admin1/facetodockfetch/frontend

# Установить зависимости (первый раз)
npm install

# Запустить dev сервер
npm run dev
```

---

## Проверка работы

### Backend API

```bash
# Health check
curl http://localhost:30000/health

# API документация
open http://localhost:30000/docs
# или
firefox http://localhost:30000/docs
```

### Celery Worker

```bash
# Проверить что worker работает
celery -A app.celery_app inspect active
```

### GPU (если используется)

```bash
conda activate face-recognition-system
cd backend

python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'GPU count: {torch.cuda.device_count()}')
"
```

### Frontend

```bash
# Должен быть доступен на
http://localhost:3000
```

---

## Управление сервисами

### Использование скриптов

```bash
# Запустить все сервисы
./scripts/start_services.sh

# Остановить все сервисы
./scripts/stop_services.sh

# Проверить статус
ps aux | grep -E "uvicorn|celery|node"
```

### PID файлы

Скрипты создают PID файлы в `logs/`:
- `logs/backend.pid`
- `logs/celery.pid`
- `logs/frontend.pid`

### Логи

Логи сохраняются в:
- `logs/backend.log`
- `logs/celery.log`
- `logs/frontend.log`

### Просмотр логов в реальном времени

```bash
# Backend
tail -f logs/backend.log

# Celery
tail -f logs/celery.log

# Все логи
tail -f logs/*.log
```

---

## Тестирование

### Быстрая проверка окружения

```bash
conda activate face-recognition-system

# Базовый тест
python scripts/test_environment.py

# С продвинутым логированием
python scripts/test_environment_advanced.py
```

### Pytest

```bash
conda activate face-recognition-system

# Все тесты
pytest

# С покрытием
pytest --cov=backend/app --cov-report=html
```

---

## Обновление

```bash
# Остановить сервисы
./scripts/stop_services.sh

# Обновить код
git pull origin main

# Обновить conda окружение
conda activate face-recognition-system
conda env update -f environment.yml  # или environment-gpu.yml

# Переустановить frontend зависимости (если изменились)
cd frontend
npm install

# Запустить снова
cd ..
./scripts/start_services.sh
```

---

## Производительность GPU

### Мониторинг GPU

```bash
# В отдельном терминале
watch -n 1 nvidia-smi

# Или более детально
nvtop  # нужно установить: sudo apt install nvtop
```

### Оптимизация для GPU

В `.env` файле:

```env
# GPU настройки
USE_GPU=true
CUDA_VISIBLE_DEVICES=0  # Использовать первый GPU

# Увеличить concurrency для Celery с GPU
CELERY_CONCURRENCY=8
```

Запуск Celery с GPU оптимизацией:

```bash
celery -A app.celery_app worker \
  --loglevel=info \
  --concurrency=8 \
  --pool=solo  # Для лучшей работы с GPU
```

---

## Troubleshooting

### Backend не запускается

```bash
# Проверить логи
cat logs/backend.log

# Проверить что порт 30000 свободен
sudo lsof -i :30000

# Проверить что все зависимости установлены
conda activate face-recognition-system
python -c "from app.main import app; print('OK')"
```

### Celery не подключается к Redis

```bash
# Проверить что Redis работает
redis-cli ping

# Проверить подключение
conda activate face-recognition-system
cd backend
python -c "from redis import Redis; r = Redis(host='localhost', port=6379); print(r.ping())"
```

### Elasticsearch не доступен

```bash
# Проверить статус
curl http://localhost:9200

# Если через Docker
docker logs elasticsearch

# Если системный
sudo systemctl status elasticsearch
sudo journalctl -u elasticsearch -f
```

### GPU не доступен

```bash
# Проверить драйверы
nvidia-smi

# Проверить CUDA в Python
conda activate face-recognition-system
python -c "import torch; print(torch.cuda.is_available())"

# Проверить переменные окружения
echo $CUDA_VISIBLE_DEVICES
echo $USE_GPU
```

---

## Сравнение: Нативный запуск vs Docker

| Аспект | Нативный | Docker |
|--------|----------|---------|
| **Скорость разработки** | ✅ Быстрее | ⚠️ Медленнее rebuild |
| **Доступ к GPU** | ✅ Прямой | ⚠️ Через runtime |
| **Изоляция** | ⚠️ Нет | ✅ Полная |
| **Deployment** | ⚠️ Сложнее | ✅ Проще |
| **Отладка** | ✅ Проще | ⚠️ Сложнее |
| **Производительность** | ✅ Лучше | ⚠️ Небольшой overhead |

---

## Переключение между нативным и Docker

### Из нативного в Docker

```bash
# Остановить нативные сервисы
./scripts/stop_services.sh

# Запустить Docker
docker-compose up -d
# или для GPU
docker-compose -f docker-compose.gpu.yml up -d
```

### Из Docker в нативный

```bash
# Остановить Docker контейнеры
docker-compose down

# Запустить нативно
./scripts/start_services.sh
```

---

## Полезные команды

```bash
# Проверить все процессы проекта
ps aux | grep -E "face-recognition|uvicorn|celery"

# Освободить порты если заняты
sudo lsof -ti:30000 | xargs kill -9  # Backend
sudo lsof -ti:3000 | xargs kill -9  # Frontend

# Очистить кэш conda
conda clean -a

# Пересоздать окружение
conda env remove -n face-recognition-system
./scripts/setup_conda.sh

# Очистить данные
rm -rf data/db/* data/cache/*
# Переинициализировать
cd backend
python scripts/init_db.py
python scripts/init_elasticsearch.py
```

---

## Поддержка

- 📖 [README.md](README.md) - Общая документация
- 🔧 [SCRIPTS.md](SCRIPTS.md) - Управление скриптами
- 🎮 [GPU_SETUP.md](GPU_SETUP.md) - Настройка GPU
- 🐛 [GPU_TROUBLESHOOTING.md](GPU_TROUBLESHOOTING.md) - Решение проблем с GPU
- 🧪 [tests/README.md](tests/README.md) - Тестирование
