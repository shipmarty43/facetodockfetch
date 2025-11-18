# Решение проблемы с логином

## Проблема: "Не могу залогиниться через веб"

### Причина

Система не запущена или не инициализирована. Frontend пытается подключиться к backend через прокси `/api` → `http://localhost:30000`, но backend не отвечает.

---

## Решение

### Вариант 1: Автоматический запуск (рекомендуется)

Выполните одну команду:

```bash
./scripts/quick_start.sh
```

Это автоматически:
- Создаст Conda окружение
- Запустит Redis + Elasticsearch в Docker
- Инициализирует базу данных
- Создаст пользователя `admin` с паролем `admin123`
- Запустит все сервисы

---

### Вариант 2: Пошаговый запуск

Если у вас уже установлена Conda и нужен контроль на каждом шаге:

#### 1. Запустить инфраструктуру (Redis + Elasticsearch)

```bash
./scripts/start_infrastructure.sh
```

**Что это делает:**
- Запускает Redis в Docker на порту 6379
- Запускает Elasticsearch в Docker на порту 9200
- Ждёт полной готовности сервисов (30-60 секунд)

#### 2. Активировать Conda окружение

```bash
conda activate face-recognition-system
```

Если окружение не создано:
```bash
./scripts/setup_conda.sh
conda activate face-recognition-system
```

#### 3. Инициализировать систему

```bash
./scripts/init_all.sh
```

**Что это делает:**
- Создаёт базу данных SQLite
- Инициализирует Elasticsearch индексы
- **Создаёт администратора:** username=`admin`, password=`admin123`

#### 4. Запустить приложение

```bash
./scripts/start_services.sh
```

**Запускаются:**
- Backend на http://localhost:30000
- Celery worker
- Frontend на http://localhost:3003

---

## Проверка работы

### 1. Проверить backend

```bash
curl http://localhost:30000/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "database": "ok",
  "elasticsearch": "ok",
  "mode": "debug"
}
```

### 2. Проверить инфраструктуру

```bash
# Redis
redis-cli ping
# Должен ответить: PONG

# Elasticsearch
curl http://localhost:9200
# Должен вернуть JSON с версией
```

### 3. Проверить логин напрямую

```bash
curl -X POST http://localhost:30000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Ожидаемый ответ:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Если получили токены - логин работает! ✅

### 4. Проверить пользователя в базе данных

```bash
cd backend
python scripts/test_login.py
```

Этот скрипт проверит:
- Существование базы данных
- Наличие пользователя `admin`
- Корректность пароля `admin123`
- Возможность генерации хешей

---

## Типичные ошибки

### Ошибка: "Cannot connect to backend"

**Причина:** Backend не запущен

**Решение:**
```bash
# Проверить процессы
ps aux | grep uvicorn

# Если не запущен
conda activate face-recognition-system
./scripts/start_services.sh
```

---

### Ошибка: "401 Unauthorized" или "Incorrect username or password"

**Причина:** Пользователь не создан или неверный пароль

**Решение:**
```bash
conda activate face-recognition-system
cd backend

# Проверить пользователя
python scripts/test_login.py

# Пересоздать с force
python scripts/create_admin.py --username admin --password admin123 --force
```

---

### Ошибка: "Connection refused localhost:30000"

**Причина:** Backend не запущен на порту 30000

**Решение:**
```bash
# Проверить, занят ли порт
lsof -i :30000

# Запустить backend
conda activate face-recognition-system
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 30000 --reload
```

---

### Ошибка: "Cannot connect to Redis/Elasticsearch"

**Причина:** Инфраструктура не запущена

**Решение:**
```bash
# Запустить инфраструктуру
./scripts/start_infrastructure.sh

# Проверить Docker контейнеры
docker ps | grep face_recognition
```

---

### Frontend показывает ошибку в консоли браузера

**Проверьте:**

1. **Открыть DevTools (F12) → Console**
   - Ищите ошибки с `ERR_CONNECTION_REFUSED`
   - Ищите ошибки с `/api/v1/auth/login`

2. **Открыть DevTools (F12) → Network**
   - Нажать кнопку "Sign In"
   - Посмотреть запрос к `/api/v1/auth/login`
   - Проверить статус код (должен быть 200)
   - Проверить Response (должен содержать токены)

3. **Проверить прокси Vite**
   - Убедитесь, что frontend запущен через `npm run dev`
   - Не используйте production build для локальной разработки

---

## После успешного запуска

**Учётные данные по умолчанию:**
- **Username:** `admin`
- **Password:** `admin123`

**Интерфейсы:**
- Frontend: http://localhost:3003
- Backend API Docs: http://localhost:30000/docs
- Elasticsearch: http://localhost:9200

**⚠️ ВАЖНО:** Обязательно смените пароль в production!

```bash
conda activate face-recognition-system
cd backend
python scripts/create_admin.py --username admin --password YOUR_SECURE_PASSWORD --force
```

---

## Полезные команды

```bash
# Остановить всё
./scripts/stop_services.sh
./scripts/stop_infrastructure.sh

# Перезапустить
./scripts/quick_start.sh

# Просмотр логов
tail -f logs/backend.log
tail -f logs/celery.log
tail -f logs/frontend.log

# Проверка здоровья
curl http://localhost:30000/health
```

---

## Нужна помощь?

1. Запустите диагностический скрипт:
   ```bash
   cd backend
   python scripts/test_login.py
   ```

2. Проверьте логи:
   ```bash
   tail -50 logs/backend.log
   ```

3. Проверьте все сервисы:
   ```bash
   # Backend
   curl http://localhost:30000/health

   # Frontend
   curl http://localhost:3003

   # Redis
   redis-cli ping

   # Elasticsearch
   curl http://localhost:9200
   ```

4. Полная переинициализация:
   ```bash
   # Остановить всё
   ./scripts/stop_services.sh
   ./scripts/stop_infrastructure.sh

   # Удалить данные
   rm -rf data/db/*

   # Запустить заново
   ./scripts/quick_start.sh
   ```
