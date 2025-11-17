# Управление проектом - скрипты и команды

Набор утилит для управления Face Recognition & OCR System.

## 📋 Содержание

- [Основные скрипты](#основные-скрипты)
- [Docker управление](#docker-управление)
- [Conda управление](#conda-управление)
- [Git актуализация](#git-актуализация)
- [Логи и мониторинг](#логи-и-мониторинг)

---

## Основные скрипты

### Инициализация

```bash
# Инициализация базы данных
python scripts/init_db.py

# Инициализация Elasticsearch
python scripts/init_elasticsearch.py

# Создание администратора
python scripts/create_admin.py --username admin --password yourpassword
```

---

## Docker управление

### Пересоздание контейнеров

```bash
# CPU версия
./scripts/rebuild_containers.sh

# GPU версия
./scripts/rebuild_containers.sh gpu
```

**Что делает:**
- Останавливает контейнеры
- Пересобирает с `--no-cache`
- Запускает заново
- Проверяет health статус

### Быстрое пересоздание

```bash
# Для быстрого rebuild без подтверждений
./scripts/quick_rebuild.sh

# GPU версия
./scripts/quick_rebuild.sh gpu
```

### Просмотр логов

```bash
# Все сервисы
./scripts/logs.sh

# Конкретный сервис
./scripts/logs.sh backend
./scripts/logs.sh celery_worker
./scripts/logs.sh frontend

# GPU версия
./scripts/logs.sh gpu backend

# Без автообновления (--no-follow)
./scripts/logs.sh backend --no-follow
```

### Очистка Docker

```bash
# Очистка неиспользуемых ресурсов
./scripts/docker_cleanup.sh
```

**Очищает:**
- Остановленные контейнеры
- Неиспользуемые сети
- Dangling images
- Build cache (опционально)
- Volumes (опционально, осторожно!)

---

## Conda управление

> **Преимущества Conda:** Проект использует Conda вместо pip для автоматического управления зависимостями. Conda подтягивает совместимые версии библиотек без жёсткой привязки к конкретным версиям, что упрощает обновление и решение конфликтов зависимостей.

### Автоматическая установка

```bash
# Интерактивная установка
./scripts/setup_conda.sh

# Скрипт:
# - Определит автоматически наличие NVIDIA GPU
# - Выберет environment.yml (CPU) или environment-gpu.yml (GPU)
# - Создаст conda окружение с гибкими версиями зависимостей
# - Проверит GPU если выбран GPU режим
```

### Запуск сервисов

```bash
# Запустить все (backend + celery + frontend)
./scripts/start_services.sh

# Остановить все
./scripts/stop_services.sh
```

**start_services.sh запускает:**
- Redis (если не запущен)
- Backend на :8000
- Celery worker
- Frontend на :3000 (если установлен npm)

**PID файлы сохраняются в:** `logs/*.pid`

---

## Git актуализация

### Автоматическое обновление

```bash
# Обновить из git и rebuild
./scripts/update_from_git.sh
```

**Workflow:**
1. Проверяет наличие изменений в git
2. Предлагает stash если есть локальные изменения
3. Делает `git pull`
4. Определяет тип развертывания (Docker/Conda)
5. **Автоматически пересобирает контейнеры** или обновляет Conda
6. Показывает что изменилось

**Пример:**
```bash
$ ./scripts/update_from_git.sh

==========================================
Update from Git and Rebuild
==========================================

Current branch: main
Current commit: 7ca11bd

Fetching updates from remote...
Updates available:
* e3a30b4 Add CUDA/GPU support
* 5889c09 Implement complete system

Pulling updates...
Updated to commit: e3a30b4

Detected Docker deployment
Rebuild Docker containers? [Y/n]: y

Rebuilding with CPU...
[... rebuild process ...]

Update completed successfully!
```

### Ручное обновление

```bash
# 1. Git pull
git pull origin main

# 2. Rebuild контейнеров (Docker)
./scripts/rebuild_containers.sh

# Или для Conda (автоматически обновит зависимости)
# CPU версия
conda env update -f environment.yml

# GPU версия
conda env update -f environment-gpu.yml

# Перезапуск сервисов
./scripts/stop_services.sh
./scripts/start_services.sh
```

**Примечание:** Conda автоматически разрешит совместимые версии при обновлении, без конфликтов зависимостей.

---

## Логи и мониторинг

### Docker logs

```bash
# Real-time все сервисы
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Последние 100 строк
docker-compose logs --tail=100 backend

# С timestamps
docker-compose logs -f -t backend
```

### Conda logs

Логи сохраняются в `logs/`:

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

### Health check

```bash
# Проверить статус всех сервисов
curl http://localhost:8000/health | python3 -m json.tool

# Пример ответа:
{
  "status": "healthy",
  "database": "ok",
  "elasticsearch": "ok",
  "gpu": "available (NVIDIA GeForce RTX 3080)",
  "mode": "debug"
}
```

### Container status

```bash
# Статус контейнеров
docker-compose ps

# Детальная информация
docker inspect face_recognition_backend

# Использование ресурсов
docker stats
```

---

## Полезные команды

### Docker

```bash
# Перезапуск одного сервиса
docker-compose restart backend

# Выполнить команду в контейнере
docker-compose exec backend python scripts/init_db.py

# Shell в контейнере
docker-compose exec backend bash

# Остановить все
docker-compose down

# Остановить и удалить volumes (ОСТОРОЖНО!)
docker-compose down -v
```

### Conda

```bash
# Активировать окружение
conda activate face-recognition-system

# Обновить зависимости (CPU)
conda env update -f environment.yml

# Обновить зависимости (GPU)
conda env update -f environment-gpu.yml

# Экспорт окружения
conda env export > environment_backup.yml

# Проверить установленные пакеты
conda list

# Деактивировать
conda deactivate
```

**Преимущества Conda:**
- Автоматическое разрешение конфликтов версий
- Бинарные пакеты (быстрее компиляции pip)
- Лучшая поддержка ML/AI библиотек
- Гибкие версии (`>=` вместо `==`)

### Database

```bash
# Подключиться к SQLite
sqlite3 data/db/face_recognition.db

# Посмотреть таблицы
sqlite3 data/db/face_recognition.db ".tables"

# Бэкап БД
cp data/db/face_recognition.db data/db/backup_$(date +%Y%m%d).db

# Восстановление
cp data/db/backup_20241117.db data/db/face_recognition.db
```

### Elasticsearch

```bash
# Проверить индексы
curl http://localhost:9200/_cat/indices

# Статистика
curl http://localhost:9200/_stats

# Удалить индекс
curl -X DELETE http://localhost:9200/face_embeddings

# Пересоздать (через админку)
curl -X POST http://localhost:8000/api/v1/admin/reindex \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### "Port already in use"

```bash
# Найти процесс на порту 8000
lsof -i :8000

# Убить процесс
kill -9 <PID>

# Или остановить все контейнеры
docker-compose down
```

### "Cannot connect to Docker daemon"

```bash
# Запустить Docker
sudo systemctl start docker

# Проверить статус
sudo systemctl status docker
```

### "Out of disk space"

```bash
# Очистить Docker
./scripts/docker_cleanup.sh

# Или вручную
docker system prune -a --volumes
```

### "Database locked"

```bash
# Остановить все процессы
./scripts/stop_services.sh
docker-compose down

# Проверить файл БД
ls -lh data/db/face_recognition.db

# Перезапустить
docker-compose up -d
```

---

## Автоматизация

### Cron для автообновления

```bash
# Добавить в crontab (crontab -e)

# Обновление каждую ночь в 2:00
0 2 * * * cd /path/to/facetodockfetch && ./scripts/update_from_git.sh >> logs/auto_update.log 2>&1

# Очистка Docker каждое воскресенье
0 3 * * 0 cd /path/to/facetodockfetch && ./scripts/docker_cleanup.sh >> logs/cleanup.log 2>&1
```

### Systemd service (для Conda)

```bash
# Создать /etc/systemd/system/face-recognition.service

[Unit]
Description=Face Recognition System
After=network.target

[Service]
Type=forking
User=youruser
WorkingDirectory=/path/to/facetodockfetch
ExecStart=/path/to/facetodockfetch/scripts/start_services.sh
ExecStop=/path/to/facetodockfetch/scripts/stop_services.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Активировать
sudo systemctl enable face-recognition
sudo systemctl start face-recognition
```

---

## Резюме команд

| Задача | Команда |
|--------|---------|
| **Обновить из git** | `./scripts/update_from_git.sh` |
| **Rebuild контейнеров** | `./scripts/rebuild_containers.sh` |
| **Быстрый rebuild** | `./scripts/quick_rebuild.sh` |
| **Просмотр логов** | `./scripts/logs.sh backend` |
| **Очистка Docker** | `./scripts/docker_cleanup.sh` |
| **Запуск (Conda)** | `./scripts/start_services.sh` |
| **Остановка (Conda)** | `./scripts/stop_services.sh` |
| **Health check** | `curl localhost:8000/health` |

Все скрипты находятся в `scripts/` и имеют права на выполнение.
