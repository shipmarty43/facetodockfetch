# Обновление кода на сервере

## Проблема

Docker build падает с ошибкой:
```
COPY ../environment-gpu.yml environment.yml
"/environment-gpu.yml": not found
```

Это означает, что на сервере используется старая версия Dockerfile.gpu.

## Решение

### Шаг 1: Проверить текущую ветку

```bash
cd /home/admin1/facetodockfetch
git branch
git log --oneline -1
```

### Шаг 2: Обновить код

Если вы на ветке `claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD`:

```bash
# Сохранить локальные изменения (если есть)
git stash

# Получить последние изменения
git fetch origin

# Переключиться на правильную ветку
git checkout claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD

# Обновить
git pull origin claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD

# Проверить текущий коммит (должен быть ae775c1 или новее)
git log --oneline -1
```

Если вы на ветке `main`:

```bash
# Сохранить локальные изменения (если есть)
git stash

# Получить последние изменения
git fetch origin

# Слить изменения из ветки разработки
git merge origin/claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD

# Или переключиться на ветку разработки
git checkout claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD
git pull origin claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD
```

### Шаг 3: Проверить исправления

Проверьте, что файлы обновлены:

```bash
# Должно быть: COPY environment-gpu.yml .
grep "COPY.*environment-gpu.yml" backend/Dockerfile.gpu

# Должно быть: COPY backend/app ./app
grep "COPY.*app.*app" backend/Dockerfile.gpu

# Проверить docker-compose
grep "context:" docker-compose.gpu.yml
```

**Ожидаемый результат:**
```
backend/Dockerfile.gpu:COPY environment-gpu.yml .
backend/Dockerfile.gpu:COPY backend/app ./app

docker-compose.gpu.yml:      context: .
```

### Шаг 4: Пересобрать контейнеры

```bash
# GPU версия
docker-compose -f docker-compose.gpu.yml build --no-cache

# Или через скрипт
./scripts/rebuild_containers.sh gpu
```

## Альтернатива: Использовать автоматический скрипт обновления

```bash
# Этот скрипт автоматически:
# 1. Делает git pull
# 2. Пересобирает контейнеры
./scripts/update_from_git.sh
```

## Проверка успешности

После обновления build должен пройти без ошибок. Проверьте:

```bash
docker-compose -f docker-compose.gpu.yml build 2>&1 | grep -i "error\|failed"
```

Если нет вывода - build прошел успешно!

## Последние коммиты с исправлениями

```
ae775c1 - Fix Docker build context for conda environment files (КРИТИЧНО!)
0e53b85 - Add automated tests with advanced logging and fix opencv conflict
72c5dda - Fix incorrect package name: python-mrz -> mrz
cfbe712 - Add repository URL to documentation
3041b16 - Simplify conda environment files to include only direct dependencies
941b1f3 - Migrate from pip to conda for dependency management
```

Ваш текущий коммит: `5e84940` (старая версия)
Нужный коммит: `ae775c1` или новее

## Быстрое решение одной командой

```bash
cd /home/admin1/facetodockfetch && \
git fetch origin && \
git checkout claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD && \
git pull origin claude/face-recognition-ocr-system-01354YdRBb24kyicgGNpwLvD && \
echo "Текущий коммит:" && git log --oneline -1
```

После этого запустите rebuild:

```bash
./scripts/rebuild_containers.sh gpu
```
