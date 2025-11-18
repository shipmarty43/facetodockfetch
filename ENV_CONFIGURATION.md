# Конфигурация через .env файл

## Как работает .env файл

### Расположение файла

`.env` файл должен находиться в **корне проекта**:

```
facetodockfetch/
├── .env              ← Здесь!
├── .env.example
├── backend/
├── frontend/
├── scripts/
└── docker-compose.yml
```

### Автоматическая загрузка

При запуске приложения файл `.env` загружается **автоматически**:

1. **Backend** (`backend/app/config.py`) автоматически находит `.env` в корне проекта
2. **Docker Compose** автоматически загружает переменные из `.env`
3. Все скрипты используют переменные из `.env` через backend конфигурацию

**Важно:** Путь к `.env` вычисляется автоматически относительно `backend/app/config.py`:
```python
PROJECT_ROOT = Path(__file__).parent.parent.parent  # backend/app/config.py -> root
ENV_FILE = PROJECT_ROOT / ".env"
```

Это работает независимо от того, откуда вы запускаете скрипты!

---

## Создание .env файла

### Вариант 1: Автоматически (рекомендуется)

```bash
# Скрипт init_all.sh создаёт .env автоматически
./scripts/init_all.sh
```

### Вариант 2: Вручную

```bash
# В корне проекта
cp .env.example .env
```

---

## Основные настройки

### Режим работы

```env
# debug - для разработки (подробные логи, автоперезагрузка)
# production - для продакшена (оптимизации, безопасность)
MODE=debug
```

### Безопасность

```env
SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key

# Для production обязательно измените на случайные строки!
# Генерация: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### База данных

```env
# SQLite (по умолчанию)
DATABASE_URL=sqlite:///./data/db/face_recognition.db

# Для PostgreSQL (опционально):
# DATABASE_URL=postgresql://user:password@localhost:5432/facedb
```

### Redis и Elasticsearch

```env
# Если используете Docker infrastructure (./scripts/start_infrastructure.sh)
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200

# Если Docker на другом хосте:
# REDIS_URL=redis://192.168.1.100:6379/0
# ELASTICSEARCH_URL=http://192.168.1.100:9200
```

### GPU настройки

```env
# Включить GPU (если есть NVIDIA)
USE_GPU=true
CUDA_VISIBLE_DEVICES=0  # Номер GPU (0, 1, 2...)

# Для CPU-only
USE_GPU=false
```

### CORS (для фронтенда)

```env
# Разрешённые origins для CORS
CORS_ORIGINS=http://localhost:3003,http://localhost:30000

# Для production добавьте ваш домен:
# CORS_ORIGINS=https://yourapp.com,https://api.yourapp.com
```

### Логирование

```env
# Уровень логов: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=DEBUG      # DEBUG для разработки
# LOG_LEVEL=INFO     # INFO для production

LOG_FILE=./logs/app.log
LOG_MAX_SIZE_MB=100
LOG_RETENTION_DAYS=30
```

---

## Переопределение переменных

### Приоритет загрузки:

1. **Переменные окружения** (самый высокий приоритет)
2. **Файл .env**
3. **Дефолтные значения** в `backend/app/config.py`

### Примеры:

```bash
# Временно переопределить для одного запуска
USE_GPU=true MODE=production ./scripts/start_services.sh

# Установить переменную для всей сессии
export USE_GPU=true
./scripts/start_services.sh

# Использовать другой .env файл
ENV_FILE=.env.production ./scripts/start_services.sh
```

---

## Docker vs Локальное развёртывание

### Docker Compose

При использовании `docker-compose up`:
- `.env` в корне проекта **автоматически** загружается
- Используется для подстановки `${VARIABLE}` в `docker-compose.yml`
- Передаётся в контейнеры через `environment:`

```yaml
services:
  backend:
    environment:
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key}  # Из .env
```

### Локальное развёртывание

При использовании `./scripts/start_services.sh`:
- `.env` загружается через `pydantic_settings`
- Backend читает файл автоматически при импорте `config.py`
- Путь к `.env` вычисляется относительно `backend/app/config.py`

---

## Проверка конфигурации

### Посмотреть текущие настройки:

```bash
conda activate face-recognition-system
cd backend

# Показать все настройки
python -c "from app.config import settings; import json; print(json.dumps({k: str(v) for k, v in settings.__dict__.items() if not k.startswith('_')}, indent=2))"

# Проверить конкретную настройку
python -c "from app.config import settings; print(f'USE_GPU: {settings.USE_GPU}')"
python -c "from app.config import settings; print(f'MODE: {settings.MODE}')"
python -c "from app.config import settings; print(f'ENV_FILE: {settings.Config.env_file}')"
```

---

## Безопасность

### ⚠️ ВАЖНО:

1. **Никогда не коммитьте .env в git!**
   - `.env` уже в `.gitignore`
   - Коммитьте только `.env.example` с примерами

2. **Измените секреты в production:**
   ```bash
   # Генерация случайных ключей
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
   ```

3. **Ограничьте права доступа:**
   ```bash
   chmod 600 .env  # Только владелец может читать/писать
   ```

4. **Для production используйте secrets management:**
   - Docker Secrets
   - Kubernetes Secrets
   - HashiCorp Vault
   - AWS Secrets Manager

---

## Troubleshooting

### Проблема: "Settings validation error"

**Причина:** В `.env` есть переменная, которой нет в `Settings` классе

**Решение:**
```bash
# Проверить какие переменные в .env
cat .env

# Сравнить с допустимыми в backend/app/config.py
# Удалить неиспользуемые переменные из .env
```

### Проблема: ".env file not found"

**Причина:** Файл `.env` не создан

**Решение:**
```bash
# Создать из примера
cp .env.example .env

# Или запустить init_all.sh
./scripts/init_all.sh
```

### Проблема: "Настройки не применяются"

**Причина:** Возможно используются переменные окружения с более высоким приоритетом

**Решение:**
```bash
# Проверить переменные окружения
env | grep -E "MODE|SECRET_KEY|USE_GPU"

# Удалить если нужно
unset MODE
unset USE_GPU

# Перезапустить сервисы
./scripts/stop_services.sh
./scripts/start_services.sh
```

### Проблема: "Permission denied"

**Причина:** Нет прав на чтение `.env`

**Решение:**
```bash
# Установить права
chmod 600 .env

# Проверить владельца
ls -la .env
```

---

## Примеры конфигураций

### Development (локально с Docker infrastructure)

```env
MODE=debug
USE_GPU=false
LOG_LEVEL=DEBUG

REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200

CORS_ORIGINS=http://localhost:3003,http://localhost:30000
```

### Development (с GPU)

```env
MODE=debug
USE_GPU=true
CUDA_VISIBLE_DEVICES=0
LOG_LEVEL=DEBUG

REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200
```

### Production

```env
MODE=production
USE_GPU=true
CUDA_VISIBLE_DEVICES=0
LOG_LEVEL=INFO

SECRET_KEY=<сгенерированный-ключ>
JWT_SECRET_KEY=<сгенерированный-ключ>

DATABASE_URL=postgresql://user:password@db-host:5432/production_db
REDIS_URL=redis://redis-host:6379/0
ELASTICSEARCH_URL=http://es-host:9200

CORS_ORIGINS=https://app.example.com,https://api.example.com

MAX_UPLOAD_SIZE_MB=100
CELERY_WORKERS=16
```

---

## Дополнительная информация

- 📖 [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- 📖 [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- 📖 Полный список переменных: см. `backend/app/config.py` класс `Settings`
