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

## Быстрый старт с Docker Compose

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
│   └── init_elasticsearch.py
├── docker-compose.yml
├── environment.yml        # Conda environment
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

## Лицензия

Proprietary. All rights reserved.
