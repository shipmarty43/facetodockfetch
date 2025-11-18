#!/usr/bin/env python3
"""Verify database path consistency across all modules."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("Database Path Verification")
print("=" * 60)
print()

# 1. Check config settings
print("1. Checking config.py settings...")
try:
    from app.config import settings
    print(f"   ✓ DATABASE_URL: {settings.DATABASE_URL}")
    print()
except Exception as e:
    print(f"   ✗ Error loading config: {e}")
    sys.exit(1)

# 2. Check database module
print("2. Checking database.py engine...")
try:
    from app.database import engine, SessionLocal
    print(f"   ✓ Engine URL: {engine.url}")
    print()
except Exception as e:
    print(f"   ✗ Error loading database: {e}")
    sys.exit(1)

# 3. Verify they match
print("3. Verifying consistency...")
if str(engine.url) == settings.DATABASE_URL:
    print(f"   ✓ Config and Engine use SAME database")
else:
    print(f"   ✗ MISMATCH!")
    print(f"     Config:  {settings.DATABASE_URL}")
    print(f"     Engine:  {engine.url}")
    sys.exit(1)
print()

# 4. Check database file
print("4. Checking database file...")
db_path_str = settings.DATABASE_URL.replace("sqlite:///", "")
db_path = Path(db_path_str)

print(f"   Path: {db_path}")
print(f"   Absolute: {db_path.absolute()}")
print(f"   Exists: {db_path.exists()}")

if db_path.exists():
    print(f"   Size: {db_path.stat().st_size} bytes")
else:
    print(f"   ⚠ Database file does not exist!")
    print(f"   Run: cd backend && python scripts/init_db.py")
print()

# 5. Test SessionLocal
print("5. Testing SessionLocal connection...")
try:
    db = SessionLocal()
    from app.database import User

    # Try to query users
    user_count = db.query(User).count()
    print(f"   ✓ Connection successful")
    print(f"   ✓ Users in database: {user_count}")

    # List all users
    if user_count > 0:
        print(f"\n   Users:")
        users = db.query(User).all()
        for user in users:
            print(f"     - {user.username} ({user.role}) {'✓ active' if user.is_active else '✗ inactive'}")
    else:
        print(f"   ⚠ No users found!")
        print(f"   Run: cd backend && python scripts/create_admin.py")

    db.close()
    print()
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. Verify User model
print("6. Checking User model...")
try:
    from app.database import User
    print(f"   ✓ Table name: {User.__tablename__}")
    print(f"   ✓ Columns:")
    for column in User.__table__.columns:
        print(f"     - {column.name}: {column.type}")
    print()
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("=" * 60)
print("✓ ALL CHECKS PASSED - Database consistency verified")
print("=" * 60)
print()
print("Summary:")
print(f"  • Database: {db_path}")
print(f"  • Config and Engine use same path: ✓")
print(f"  • Connection works: ✓")
print(f"  • Users: {user_count}")
print()
