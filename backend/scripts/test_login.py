#!/usr/bin/env python3
"""Test login functionality and diagnose issues."""
import warnings
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.database import SessionLocal, User, init_db
    from app.utils.auth import verify_password
    from app.utils.security import hash_password
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nТребуемые пакеты:")
    print("  pip install sqlalchemy passlib[bcrypt] bcrypt pydantic pydantic-settings")
    sys.exit(1)


def test_database():
    """Test database connection and admin user."""
    print("=" * 60)
    print("Тест системы логина")
    print("=" * 60)
    print()

    # Check if database file exists
    db_path = Path(__file__).parent.parent.parent / "data" / "db" / "face_recognition.db"
    print(f"1. Проверка базы данных:")
    print(f"   Путь: {db_path}")

    if not db_path.exists():
        print(f"   ❌ База данных не найдена!")
        print(f"\n   Создайте базу данных:")
        print(f"   cd backend && python scripts/init_db.py")
        return False

    print(f"   ✓ База данных существует ({db_path.stat().st_size} bytes)")
    print()

    # Try to connect
    print("2. Подключение к базе данных...")
    try:
        db = SessionLocal()
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False

    print("   ✓ Подключение успешно")
    print()

    # Check for admin user
    print("3. Поиск пользователя 'admin'...")
    try:
        admin = db.query(User).filter(User.username == "admin").first()
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")
        print("\n   Возможно, база данных не инициализирована.")
        print("   Запустите: cd backend && python scripts/init_db.py")
        db.close()
        return False

    if not admin:
        print("   ❌ Пользователь 'admin' не найден!")
        print("\n   Создайте администратора:")
        print("   cd backend && python scripts/create_admin.py --username admin --password admin123")
        db.close()
        return False

    print(f"   ✓ Пользователь найден:")
    print(f"     ID: {admin.id}")
    print(f"     Username: {admin.username}")
    print(f"     Email: {admin.email or 'не указан'}")
    print(f"     Role: {admin.role}")
    print(f"     Active: {admin.is_active}")
    print(f"     Created: {admin.created_at}")
    print(f"     Last login: {admin.last_login or 'никогда'}")
    print()

    # Test password verification
    print("4. Тест верификации пароля 'admin123'...")
    try:
        is_valid = verify_password("admin123", admin.password_hash)
        if is_valid:
            print("   ✓ Пароль 'admin123' верен!")
        else:
            print("   ❌ Пароль 'admin123' неверен!")
            print("\n   Возможные причины:")
            print("   - Пароль был изменён")
            print("   - Пользователь создан с другим паролем")
            print("\n   Сбросьте пароль:")
            print("   cd backend && python scripts/create_admin.py --username admin --password admin123 --force")
            db.close()
            return False
    except Exception as e:
        print(f"   ❌ Ошибка верификации: {e}")
        db.close()
        return False

    print()

    # Test hash generation
    print("5. Тест генерации хеша пароля...")
    try:
        test_hash = hash_password("test123")
        print(f"   ✓ Хеш сгенерирован: {test_hash[:50]}...")
    except Exception as e:
        print(f"   ❌ Ошибка генерации хеша: {e}")
        db.close()
        return False

    print()

    # Show all users
    print("6. Список всех пользователей:")
    users = db.query(User).all()
    for user in users:
        status = "✓ активен" if user.is_active else "✗ неактивен"
        print(f"   - {user.username} ({user.role}) - {status}")

    db.close()

    print()
    print("=" * 60)
    print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("=" * 60)
    print()
    print("Логин должен работать с:")
    print("  Username: admin")
    print("  Password: admin123")
    print()
    print("API endpoint: POST http://localhost:30000/api/v1/auth/login")
    print("JSON body:")
    print('  {"username": "admin", "password": "admin123"}')
    print()

    return True


if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
