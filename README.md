# Face Recognition and OCR Document Analysis System

Полнофункциональная система распознавания лиц и анализа документов с использованием OCR (Optical Character Recognition) и биометрической идентификации.

## Возможности

- **Распознавание лиц**: Высокоточное распознавание лиц с использованием InsightFace (AdaFace/ArcFace)
- **OCR документов**: Извлечение текста из документов с помощью Surya OCR
- **Парсинг MRZ**: Автоматическое извлечение данных из машиночитаемой зоны паспортов и ID карт
- **Векторный поиск**: Быстрый поиск похожих лиц через Elasticsearch
- **Асинхронная обработка**: Очередь задач на базе Celery для обработки больших объемов
- **REST API**: Полноценный API с автоматической документацией
- **Web интерфейс**: Современный React SPA с Material-UI
- **Роли пользователей**: Администраторы и операторы с разными правами доступа
- **GPU ускорение**: Опциональная поддержка CUDA для 10-50x ускорения

## Быстрый старт

### Вариант 1: Docker Compose (CPU)

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd facetodockfetch

# 2. Создать .env файл
cp .env.example .env

# 3. Запустить все сервисы
docker-compose up -d

# 4. Инициализировать базу данных (подождите ~30 сек для запуска Elasticsearch)
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/init_elasticsearch.py

# 5. Создать администратора
docker-compose exec backend python scripts/create_admin.py --username admin --password admin123

# 6. Открыть в браузере
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Вариант 2: Docker Compose с GPU (рекомендуется для production)

```bash
# Требования: NVIDIA GPU + nvidia-docker2

# 1. Проверить GPU
nvidia-smi

# 2. Запустить с GPU поддержкой
docker-compose -f docker-compose.gpu.yml up -d

# 3-6. Те же шаги что и для CPU версии
docker-compose -f docker-compose.gpu.yml exec backend python scripts/init_db.py
# ...

# Проверить GPU
curl http://localhost:8000/health
# Должно показать: "gpu": "available (NVIDIA GeForce RTX ...)"
```

📖 **Детальное руководство по GPU:** [GPU_SETUP.md](GPU_SETUP.md)

### Вариант 3: Conda (локальная разработка)

```bash
# 1. Автоматическая установка
./scripts/setup_conda.sh

# 2. Активировать окружение
conda activate face-recognition-system

# 3. Запустить сервисы
./scripts/start_services.sh

# 4. Остановить сервисы
./scripts/stop_services.sh
```

## Структура проекта

```
facetodockfetch/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Главное приложение
│   │   ├── config.py       # Конфигурация
│   │   ├── database.py     # SQLAlchemy модели
│   │   ├── models/         # Pydantic модели
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Бизнес-логика
│   │   ├── tasks/          # Celery tasks
│   │   └── utils/          # Утилиты
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/         # Страницы
│   │   ├── components/    # Компоненты
│   │   ├── services/      # API клиенты
│   │   └── store/         # Redux store
│   ├── package.json
│   └── Dockerfile
├── scripts/               # Скрипты инициализации
│   ├── init_db.py
│   ├── create_admin.py
│   ├── init_elasticsearch.py
│   ├── setup_conda.sh    # Автоустановка Conda
│   ├── start_services.sh # Запуск для Conda
│   └── stop_services.sh  # Остановка сервисов
├── docker-compose.yml     # CPU версия
├── docker-compose.gpu.yml # GPU версия
├── environment.yml        # Conda environment
├── GPU_SETUP.md          # GPU руководство
└── README.md
```

## API Документация

Swagger UI: http://localhost:8000/docs

### Основные endpoints

**Аутентификация:**
- `POST /api/v1/auth/login` - Вход в систему
- `POST /api/v1/auth/refresh` - Обновление токена

**Документы:**
- `POST /api/v1/documents/upload` - Загрузить документ
- `GET /api/v1/documents` - Список документов
- `DELETE /api/v1/documents/{id}` - Удалить документ

**Поиск:**
- `POST /api/v1/search/face` - Поиск по лицу
- `POST /api/v1/search/text` - Полнотекстовый поиск

**Администрирование:**
- `GET /api/v1/admin/stats` - Статистика системы
- `POST /api/v1/admin/reindex` - Ре-индексация базы

## Технологии

**Backend:** Python, FastAPI, SQLAlchemy, Celery, Elasticsearch, InsightFace, Surya OCR
**Frontend:** React, Material-UI, Redux Toolkit, Axios
**Infrastructure:** Docker, Redis, Elasticsearch, Nginx
**GPU:** CUDA 11.8, PyTorch, ONNX Runtime GPU

## Производительность

### CPU vs GPU (RTX 3080)

| Операция | CPU | GPU | Ускорение |
|----------|-----|-----|-----------|
| Face detection | 0.5s | 0.08s | **6x** |
| Face embedding | 0.5s | 0.05s | **10x** |
| Batch (100 faces) | 50s | 5s | **10x** |

📊 Полное тестирование: [GPU_SETUP.md](GPU_SETUP.md#производительность)

## Лицензия

Proprietary. All rights reserved.
