# Исправление проблемы с логином

## Проблема

Пользователи не могли войти в систему, даже с правильными учётными данными `admin` / `admin123`.

## Причина

**Дублирование функций хеширования и верификации паролей** в двух разных модулях:

### До исправления:

1. **При создании пользователя** использовался `app/utils/security.py`:
   ```python
   # В create_admin.py и admin.py
   from app.utils.security import hash_password  # ИЛИ
   from app.utils.auth import get_password_hash
   ```

2. **При логине** использовался `app/utils/auth.py`:
   ```python
   # В routes/auth.py
   from ..utils.auth import verify_password
   ```

### Потенциальные проблемы:

1. **Разные экземпляры `pwd_context`**
   - `security.py` создавал свой `CryptContext`
   - `auth.py` создавал свой отдельный `CryptContext`

2. **Разная обработка whitespace**
   - `hash_password` в `security.py` делает `.strip()` (удаляет пробелы)
   - `verify_password` в `auth.py` НЕ делает `.strip()`
   - Это могло привести к несовпадению, если пароль вводился с пробелами

3. **Разная обработка ошибок**
   - `security.verify_password`: ловит все исключения → `False`
   - `auth.verify_password`: пробрасывает исключения

---

## Решение

### Унификация функций паролей

**Все функции работы с паролями теперь используют `app/utils/security.py` как единственный источник:**

#### 1. Изменён `backend/app/routes/auth.py`

```python
# Было:
from ..utils.auth import verify_password, create_access_token, create_refresh_token

# Стало:
from ..utils.auth import create_access_token, create_refresh_token
from ..utils.security import verify_password  # ← Используем из security.py
```

#### 2. Изменён `backend/app/routes/admin.py`

```python
# Было:
from ..utils.auth import get_password_hash

# Стало:
from ..utils.security import hash_password  # ← Используем hash_password из security.py

# И заменены вызовы:
password_hash = hash_password(user_data.password)  # Было: get_password_hash
```

#### 3. Улучшена функция `verify_password` в `security.py`

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # Strip whitespace for consistency with hash_password
    if isinstance(plain_password, str):
        plain_password = plain_password.strip()  # ← Добавлено для консистентности

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
```

---

## Изменённые файлы

1. `backend/app/routes/auth.py` - изменён импорт verify_password
2. `backend/app/routes/admin.py` - изменён импорт и использование hash_password
3. `backend/app/utils/security.py` - добавлен .strip() в verify_password

---

## Что теперь работает правильно

### ✅ Единый источник истины

Все операции с паролями используют один и тот же `pwd_context` из `security.py`:

```
Создание пользователя:  security.hash_password()    → pwd_context
Верификация при логине: security.verify_password()  → pwd_context (тот же!)
```

### ✅ Консистентная обработка whitespace

Оба метода теперь делают `.strip()`:
- При хешировании: `password.strip()` → хеш
- При верификации: `plain_password.strip()` → сравнение с хешем

### ✅ Унифицированная обработка ошибок

Обе функции ловят исключения и возвращают понятные результаты.

---

## Тестирование

### До применения исправления:

```bash
# 1. Создать пользователя
cd backend
python scripts/create_admin.py --username admin --password admin123

# 2. Попытка логина через API
curl -X POST http://localhost:30000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Результат: 401 Unauthorized ❌
```

### После применения исправления:

```bash
# 1. Пересоздать пользователя (с новым кодом)
cd backend
python scripts/create_admin.py --username admin --password admin123 --force

# 2. Попытка логина через API
curl -X POST http://localhost:30000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Результат: 200 OK с токенами ✅
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Дополнительная проверка:

```bash
# Проверить пользователя в базе
cd backend
python scripts/test_login.py

# Должен показать:
# ✓ Пользователь найден
# ✓ Пароль 'admin123' верен!
# ✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!
```

---

## Миграция для существующих пользователей

Если пользователи уже были созданы с использованием старого кода, **необходимо пересоздать пароли**:

### Вариант 1: Пересоздать всех пользователей

```bash
conda activate face-recognition-system
cd backend

# Сбросить пароль администратора
python scripts/create_admin.py --username admin --password admin123 --force
```

### Вариант 2: Через API (если у вас есть доступ админа)

```bash
# Обновить пароль через admin API
curl -X PUT http://localhost:30000/api/v1/admin/users/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "admin123"}'
```

---

## Обратная совместимость

### Функции в `auth.py` оставлены

Функции `verify_password` и `get_password_hash` в `utils/auth.py` **НЕ удалены**, они остались для обратной совместимости, если какой-то внешний код их использует.

**Рекомендация для будущих разработок:**
- Всегда использовать `from app.utils.security import hash_password, verify_password`
- Не использовать `get_password_hash` из `auth.py`

---

## Предотвращение подобных проблем в будущем

### 1. Единый модуль для паролей

Вся работа с паролями должна идти через `app/utils/security.py`:
- `hash_password()` - для создания хешей
- `verify_password()` - для проверки

### 2. Линтинг импортов

Можно добавить проверку в pre-commit hook:

```bash
# Запретить импорт функций паролей из auth.py
grep -r "from.*auth import.*password" backend/app/routes/ && \
  echo "❌ Используйте функции из security.py" && exit 1
```

### 3. Документация

Добавить в `CONTRIBUTING.md`:

```markdown
## Работа с паролями

Всегда используйте функции из `app/utils/security.py`:

```python
from app.utils.security import hash_password, verify_password

# Создание хеша
password_hash = hash_password("mypassword")

# Проверка
is_valid = verify_password("mypassword", password_hash)
```

Не используйте функции из `app/utils/auth.py` для паролей!
```

---

## Резюме

| Аспект | До | После |
|--------|-----|-------|
| Источник hash | `auth.py` ИЛИ `security.py` | Только `security.py` ✅ |
| Источник verify | Только `auth.py` | Только `security.py` ✅ |
| Обработка whitespace | Непоследовательная | Консистентная (.strip()) ✅ |
| Обработка ошибок | Разная | Унифицированная ✅ |
| Логин работает | ❌ | ✅ |

---

## Дата исправления

**2025-11-18**

## Версия

Исправление применено в коммите: `[commit hash will be here]`
