# Быстрый старт

Полная автоматическая инициализация и запуск системы одной командой.

## Требования

- **Conda** (Anaconda или Miniconda)
- **Docker** и **docker-compose**
- **Node.js** и **npm** (для frontend)
- **NVIDIA GPU** (опционально, для ускорения)

## Установка за одну команду

```bash
# 1. Клонировать репозиторий
git clone https://github.com/shipmarty43/facetodockfetch.git
cd facetodockfetch

# 2. Запустить автоматическую инициализацию
./scripts/quick_start.sh
```

Скрипт `quick_start.sh` автоматически выполнит:

1. ✅ Создание/проверку Conda окружения
2. ✅ Создание .env файла из шаблона
3. ✅ Запуск инфраструктуры (Redis + Elasticsearch в Docker)
4. ✅ Инициализацию базы данных SQLite
5. ✅ Инициализацию Elasticsearch
6. ✅ Создание администратора (admin/admin123)
7. ✅ Запуск backend + Celery + frontend

## Что делать после запуска

### Проверить работу системы

```bash
# Проверить здоровье API
curl http://localhost:30000/health

# Проверить GPU (если установлен)
curl http://localhost:30000/health | grep gpu
```

### Открыть в браузере

- **Frontend:** http://localhost:3003
- **API Docs:** http://localhost:30000/docs

### Войти в систему

**Учётные данные по умолчанию:**
- Username: `admin`
- Password: `admin123`

⚠️ **ВАЖНО:** Смените пароль в production!

### Просмотр логов

```bash
# Backend
tail -f logs/backend.log

# Celery
tail -f logs/celery.log

# Frontend
tail -f logs/frontend.log

# Инфраструктура
docker-compose -f docker-compose.infrastructure.yml logs -f
```

## Управление системой

### Остановка сервисов

```bash
# Остановить приложение (backend + celery + frontend)
./scripts/stop_services.sh

# Остановить инфраструктуру (Redis + Elasticsearch)
./scripts/stop_infrastructure.sh

# Остановить всё
./scripts/stop_services.sh && ./scripts/stop_infrastructure.sh
```

### Перезапуск

```bash
# Перезапустить только приложение
./scripts/stop_services.sh
conda activate face-recognition-system
./scripts/start_services.sh

# Полный перезапуск всей системы
./scripts/stop_services.sh
./scripts/stop_infrastructure.sh
./scripts/quick_start.sh
```

### Повторная инициализация

```bash
# Только база данных
conda activate face-recognition-system
cd backend && python scripts/init_db.py

# Только Elasticsearch
cd backend && python scripts/init_elasticsearch.py

# Полная инициализация
./scripts/init_all.sh
```

## Пошаговый запуск (альтернатива)

Если нужен контроль на каждом шаге:

```bash
# 1. Создать Conda окружение (один раз)
./scripts/setup_conda.sh
conda activate face-recognition-system

# 2. Запустить инфраструктуру в Docker
./scripts/start_infrastructure.sh

# 3. Инициализировать систему
./scripts/init_all.sh

# 4. Запустить приложение
./scripts/start_services.sh
```

## Проверка зависимостей

```bash
conda activate face-recognition-system
cd backend
python scripts/check_dependencies.py
```

Скрипт проверит:
- ✅ FastAPI, Uvicorn, SQLAlchemy
- ✅ Passlib, bcrypt, Cryptography
- ✅ Pillow, OpenCV, pdf2image
- ✅ PyTorch, torchvision
- ✅ InsightFace, ONNX Runtime
- ✅ Surya OCR (с правильными предикторами)
- ✅ Elasticsearch client
- ✅ Настройки конфигурации

## Исправление проблем с PyTorch

Если возникает ошибка `operator torchvision::nms does not exist`:

```bash
conda activate face-recognition-system
./scripts/fix_torch_versions.sh
```

Скрипт автоматически установит совместимые версии:
- PyTorch 2.1.2
- torchvision 0.16.2
- CUDA 11.8

## Настройка GPU

### Проверка GPU

```bash
# Проверить наличие GPU
nvidia-smi

# Проверить PyTorch CUDA
conda activate face-recognition-system
python -c "import torch; print(f'CUDA доступна: {torch.cuda.is_available()}')"
```

### Включение/отключение GPU

В файле `.env`:

```bash
# Включить GPU (по умолчанию)
USE_GPU=true
CUDA_VISIBLE_DEVICES=0

# Отключить GPU (только CPU)
USE_GPU=false
```

📖 **Детальное руководство:** [GPU_SETUP.md](GPU_SETUP.md)

## Настройка Surya OCR

В файле `.env` можно настроить параметры OCR:

```bash
# Порог уверенности детекции текста
DETECTOR_TEXT_THRESHOLD=0.2

# Размеры батчей (больше = быстрее, но больше памяти)
DETECTOR_BATCH_SIZE=8
RECOGNITION_BATCH_SIZE=15
LAYOUT_BATCH_SIZE=52

# Настройка CUDA памяти
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

📖 **Детальное руководство:** [SURYA_OCR_CONFIG.md](SURYA_OCR_CONFIG.md)

## Структура директорий после запуска

```
facetodockfetch/
├── data/
│   ├── uploads/     # Загруженные документы
│   ├── db/          # SQLite база данных
│   └── cache/       # Кэш
├── logs/
│   ├── backend.log   # Логи backend
│   ├── celery.log    # Логи Celery
│   └── frontend.log  # Логи frontend
├── models/          # Загруженные ML модели
└── .env             # Конфигурация (создаётся автоматически)
```

## FAQ

### Ошибка: "Conda не найдена"

Установите Miniconda:
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### Ошибка: "Docker не найден"

Установите Docker:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Frontend не запускается

Установите Node.js:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Предупреждения bcrypt при запуске

Это нормально и не влияет на работу. Предупреждения подавляются через переменную окружения `PYTHONWARNINGS`.

### Elasticsearch долго запускается

Elasticsearch может запускаться 30-60 секунд. Подождите и проверьте:
```bash
curl http://localhost:9200
```

### Как сбросить пароль администратора

```bash
conda activate face-recognition-system
cd backend
python scripts/create_admin.py --username admin --password new_password --force
```

### Как полностью очистить систему

```bash
# Остановить всё
./scripts/stop_services.sh
./scripts/stop_infrastructure.sh

# Удалить данные
rm -rf data/ logs/ models/

# Удалить Docker контейнеры
docker-compose -f docker-compose.infrastructure.yml down -v

# Удалить Conda окружение
conda env remove -n face-recognition-system
```

## Дополнительная документация

- [README.md](README.md) - Основная документация
- [GPU_SETUP.md](GPU_SETUP.md) - Настройка GPU
- [SURYA_OCR_CONFIG.md](SURYA_OCR_CONFIG.md) - Настройка OCR
- [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md) - Переменные окружения
- [SCRIPTS.md](SCRIPTS.md) - Описание всех скриптов
- [NATIVE_SETUP.md](NATIVE_SETUP.md) - Детальная установка
- [CHANGELOG_SESSION.md](CHANGELOG_SESSION.md) - История изменений

## Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f logs/*.log`
2. Проверьте Docker: `docker ps`
3. Проверьте зависимости: `python backend/scripts/check_dependencies.py`
4. Проверьте конфигурацию: `cat .env`
