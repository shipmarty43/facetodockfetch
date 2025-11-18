# Quick Start - Локальная разработка

Быстрый старт для разработки: **инфраструктура в Docker, приложение локально**.

## Преимущества этого подхода

✅ **Redis и Elasticsearch в Docker** - простой запуск и управление
✅ **Backend и Frontend локально** - быстрая разработка с hot reload
✅ **Прямой доступ к GPU** - без Docker overhead
✅ **Простая отладка** - все логи доступны напрямую

---

## Шаг 1: Установка Conda окружения

```bash
# Создать окружение
./scripts/setup_conda.sh

# Активировать
conda activate face-recognition-system
```

---

## Шаг 2: Запустить инфраструктуру (Redis + Elasticsearch)

```bash
# Запустить Redis и Elasticsearch в Docker
./scripts/start_infrastructure.sh
```

Это запустит:
- **Redis** на порту `6379`
- **Elasticsearch** на порту `9200`

**Проверить статус:**
```bash
# Проверить контейнеры
docker ps | grep face_recognition

# Проверить подключения
redis-cli ping                    # Должно ответить: PONG
curl http://localhost:9200        # Должно показать версию Elasticsearch
```

---

## Шаг 3: Инициализировать базы данных

### Вариант A: Автоматическая инициализация (рекомендуется)

```bash
# Активировать окружение
conda activate face-recognition-system

# Запустить полную инициализацию (БД + Elasticsearch + admin)
./scripts/init_all.sh
```

**Этот скрипт автоматически:**
- ✅ Создаст все необходимые директории
- ✅ Инициализирует SQLite базу данных
- ✅ Инициализирует Elasticsearch индексы
- ✅ Создаст администратора с логином: **admin** / пароль: **admin123**

### Вариант B: Ручная инициализация

```bash
cd backend

# Инициализировать SQLite
python scripts/init_db.py

# Инициализировать Elasticsearch индексы
python scripts/init_elasticsearch.py

# Создать администратора (можно указать свои данные)
python scripts/create_admin.py --username admin --password admin123

cd ..
```

**Параметры create_admin.py:**
- `--username` - имя пользователя (по умолчанию: admin)
- `--password` - пароль (по умолчанию: admin123)
- `--force` - сбросить пароль если пользователь существует

---

## Шаг 4: Запустить приложение

```bash
# Активировать окружение (если ещё не активировано)
conda activate face-recognition-system

# Запустить backend, celery и frontend
./scripts/start_services.sh
```

Это запустит:
- **Backend API** на `http://localhost:30000`
- **Celery worker** для асинхронной обработки
- **Frontend** на `http://localhost:3003`

---

## Проверка работы

```bash
# Backend health check
curl http://localhost:30000/health

# API документация
open http://localhost:30000/docs  # или
firefox http://localhost:30000/docs

# Frontend
open http://localhost:3003
```

---

## Логи

```bash
# Backend
tail -f logs/backend.log

# Celery
tail -f logs/celery.log

# Frontend
tail -f logs/frontend.log

# Все сразу
tail -f logs/*.log
```

---

## Управление сервисами

### Остановить приложение (но оставить инфраструктуру)

```bash
./scripts/stop_services.sh
```

### Остановить всё (включая Redis и Elasticsearch)

```bash
# Остановить приложение
./scripts/stop_services.sh

# Остановить инфраструктуру
./scripts/stop_infrastructure.sh
```

### Перезапустить только приложение

```bash
./scripts/stop_services.sh
./scripts/start_services.sh
```

---

## Полезные команды

### Проверить что запущено

```bash
# Инфраструктура (Docker)
docker ps | grep face_recognition

# Приложение (процессы)
ps aux | grep -E "uvicorn|celery|npm"
```

### Просмотр PID файлов

```bash
cat logs/backend.pid
cat logs/celery.pid
cat logs/frontend.pid
```

### Освободить порты если заняты

```bash
# Backend
sudo lsof -ti:30000 | xargs kill -9

# Frontend
sudo lsof -ti:3003 | xargs kill -9
```

### Просмотр логов инфраструктуры

```bash
# Redis
docker logs face_recognition_redis -f

# Elasticsearch
docker logs face_recognition_elasticsearch -f
```

---

## Структура портов

| Сервис         | Порт   | URL                             |
|----------------|--------|---------------------------------|
| Backend API    | 30000  | http://localhost:30000          |
| API Docs       | 30000  | http://localhost:30000/docs     |
| Frontend       | 3003   | http://localhost:3003           |
| Redis          | 6379   | localhost:6379                  |
| Elasticsearch  | 9200   | http://localhost:9200           |

---

## Troubleshooting

### "Redis is not running"

```bash
./scripts/start_infrastructure.sh
```

### "Elasticsearch is not running"

```bash
./scripts/start_infrastructure.sh

# Или проверить логи
docker logs face_recognition_elasticsearch
```

### Frontend не запускается

```bash
# Проверить что npm установлен
which npm
npm --version

# Установить зависимости
cd frontend
npm install
cd ..
```

### Backend ошибки при запуске

```bash
# Проверить логи
cat logs/backend.log

# Проверить что conda окружение активировано
conda activate face-recognition-system

# Проверить зависимости
python -c "from app.main import app; print('OK')"
```

---

## Альтернативные способы запуска

### Вариант 1: Всё в Docker (проще для production)

```bash
docker-compose up -d
```

### Вариант 2: Всё в Docker с GPU

```bash
docker-compose -f docker-compose.gpu.yml up -d
```

### Вариант 3: Локально с инфраструктурой в Docker (этот гайд)

**Рекомендуется для разработки!**

```bash
./scripts/start_infrastructure.sh  # Только инфраструктура
./scripts/start_services.sh        # Приложение
```

---

## Дополнительная документация

- 📖 [README.md](README.md) - Общая документация
- 📖 [NATIVE_SETUP.md](NATIVE_SETUP.md) - Детальная нативная установка
- 🎮 [GPU_SETUP.md](GPU_SETUP.md) - Настройка GPU
- 🛠️ [SCRIPTS.md](SCRIPTS.md) - Все скрипты управления
- 🐛 [GPU_TROUBLESHOOTING.md](GPU_TROUBLESHOOTING.md) - Решение проблем с GPU
