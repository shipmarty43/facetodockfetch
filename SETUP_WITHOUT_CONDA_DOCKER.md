# Запуск без Conda и Docker

**Ситуация:** Вы находитесь в окружении без Conda и Docker (например, Codespaces, GitPod, или контейнер разработки).

## Быстрый старт (минимальная конфигурация)

### 1. Установить Python зависимости

```bash
cd /home/user/facetodockfetch

# Установить backend зависимости
cd backend
pip3 install -r requirements.txt

# Или минимальный набор:
pip3 install fastapi uvicorn sqlalchemy pydantic pydantic-settings \
             passlib[bcrypt] bcrypt python-jose[cryptography] \
             pillow numpy python-multipart
```

### 2. Создать .env файл

```bash
cd /home/user/facetodockfetch
cp .env.example .env
```

### 3. Создать директории

```bash
mkdir -p data/db data/uploads data/cache logs models
```

### 4. Инициализировать базу данных

```bash
cd backend
python3 scripts/init_db.py
```

### 5. Создать администратора

```bash
python3 scripts/create_admin.py --username admin --password admin123
```

### 6. Запустить backend БЕЗ Redis и Elasticsearch

```bash
# Из директории backend
cd /home/user/facetodockfetch/backend
uvicorn app.main:app --host 0.0.0.0 --port 30000 --reload
```

**Примечание:** Redis и Elasticsearch не обязательны для базовой работы:
- Backend запустится и будет отвечать на запросы
- Celery не будет работать (нужен Redis)
- Поиск по лицам не будет работать (нужен Elasticsearch)
- Но логин и базовый API будут работать ✅

### 7. Запустить frontend (в новом терминале)

```bash
cd /home/user/facetodockfetch/frontend

# Установить зависимости (если нужно)
npm install

# Запустить dev server
npm run dev
```

Frontend будет доступен на http://localhost:3003

---

## Полная инструкция (с Redis и Elasticsearch)

Если нужны Redis и Elasticsearch, но Docker недоступен:

### Вариант A: Установить локально

#### Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Проверка
redis-cli ping  # Должен ответить: PONG
```

#### Elasticsearch

```bash
# Скачать и запустить (Linux/macOS)
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.10.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.10.0-linux-x86_64.tar.gz
cd elasticsearch-8.10.0
./bin/elasticsearch

# В .env установить:
ELASTICSEARCH_URL=http://localhost:9200
```

### Вариант B: Использовать облачные сервисы

```bash
# В .env указать внешние URL:
REDIS_URL=redis://your-redis-cloud.com:6379
ELASTICSEARCH_URL=https://your-es-cloud.com:9200
```

---

## Запуск всех сервисов вручную

### Terminal 1: Backend

```bash
cd /home/user/facetodockfetch/backend
export PYTHONWARNINGS="ignore::UserWarning:passlib"
uvicorn app.main:app --host 0.0.0.0 --port 30000 --reload
```

### Terminal 2: Celery (если Redis доступен)

```bash
cd /home/user/facetodockfetch/backend
export PYTHONWARNINGS="ignore::UserWarning:passlib"
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

### Terminal 3: Frontend

```bash
cd /home/user/facetodockfetch/frontend
npm run dev
```

---

## Проверка работы

### 1. Backend health

```bash
curl http://localhost:30000/health
```

Ожидается:
```json
{
  "status": "healthy",
  "database": "ok",
  "elasticsearch": "unavailable",  // Если не запущен
  "mode": "debug"
}
```

### 2. Логин

```bash
curl -X POST http://localhost:30000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Ожидается:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Frontend

Откройте http://localhost:3003 в браузере
- Должна открыться страница логина
- Введите: `admin` / `admin123`
- Должны войти в систему

---

## Troubleshooting

### Ошибка: ModuleNotFoundError

```bash
# Установите недостающий модуль
pip3 install <module-name>

# Или весь requirements.txt
cd backend
pip3 install -r requirements.txt
```

### Ошибка: Port 30000 already in use

```bash
# Найти процесс
lsof -i :30000

# Убить процесс
kill -9 <PID>

# Или использовать другой порт
uvicorn app.main:app --port 30001
```

### Frontend: ECONNREFUSED

**Причина:** Backend не запущен

**Решение:**
1. Проверьте backend: `curl http://localhost:30000/health`
2. Если не отвечает, запустите backend (см. выше)
3. Проверьте vite.config.js - должен проксировать на правильный порт

### База данных: No such table

**Причина:** БД не инициализирована

**Решение:**
```bash
cd backend
python3 scripts/init_db.py
python3 scripts/create_admin.py
```

---

## Минимальная конфигурация .env

```env
# Application Mode
MODE=debug

# Security (генерируйте свои ключи!)
SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_KEY=dev-encryption-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production

# Database (используется абсолютный путь по умолчанию)
# DATABASE_URL будет автоматически: sqlite:///PROJECT_ROOT/data/db/face_recognition.db

# Redis (если НЕ доступен - некоторые функции не будут работать)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Elasticsearch (если НЕ доступен - поиск по лицам не будет работать)
ELASTICSEARCH_URL=http://localhost:9200

# CORS (для разработки)
CORS_ORIGINS=http://localhost:3003,http://localhost:30000

# GPU (если нет GPU)
USE_GPU=false
```

---

## Что будет работать без Redis/Elasticsearch

### ✅ Работает:
- Логин / Logout
- API documentation (http://localhost:30000/docs)
- Базовые CRUD операции
- Загрузка файлов
- Frontend интерфейс

### ❌ Не работает:
- Celery задачи (требует Redis)
- Поиск по лицам (требует Elasticsearch)
- Полнотекстовый поиск (требует Elasticsearch)
- Асинхронная обработка документов

---

## Для production

Для production обязательно:
1. Установите Redis и Elasticsearch
2. Используйте PostgreSQL вместо SQLite
3. Сгенерируйте надёжные ключи
4. Смените пароль admin
5. Настройте reverse proxy (nginx)
6. Используйте HTTPS
7. Настройте мониторинг

Подробнее: см. документацию по deployment
