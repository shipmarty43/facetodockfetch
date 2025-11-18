#!/usr/bin/env python3
"""Create admin user for the system."""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, User
from app.utils.security import hash_password

# Default credentials
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

def create_admin(username: str, password: str, force: bool = False):
    """Create an admin user."""
    db = SessionLocal()

    try:
        # Validate password before attempting to hash
        if not password or len(password) < 6:
            print(f"✗ Password must be at least 6 characters long")
            return False

        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()

        if existing_user:
            if not force:
                print(f"✗ User '{username}' already exists")
                print("  Use --force to reset password")
                return False
            else:
                print(f"⚠ Resetting password for user '{username}'...")
                try:
                    password_hash = hash_password(password)
                    existing_user.password_hash = password_hash
                    existing_user.role = "admin"
                    existing_user.is_active = True
                    db.commit()
                    print(f"✓ Password reset for admin user '{username}'")
                    return True
                except Exception as hash_error:
                    print(f"✗ Password hashing failed: {hash_error}")
                    print(f"  Password length: {len(password)} characters")
                    print(f"  Password bytes: {len(password.encode('utf-8'))} bytes")
                    raise

        # Create new admin user
        print("  Hashing password...")
        try:
            password_hash = hash_password(password)
        except Exception as hash_error:
            print(f"✗ Password hashing failed: {hash_error}")
            print(f"  Password length: {len(password)} characters")
            print(f"  Password bytes: {len(password.encode('utf-8'))} bytes")
            raise

        print("  Creating user record...")
        admin = User(
            username=username,
            password_hash=password_hash,
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print(f"✓ Admin user created successfully")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"  Role: admin")

        return True

    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        help=f"Admin username (default: {DEFAULT_USERNAME})"
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help=f"Admin password (default: {DEFAULT_PASSWORD})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reset password if user exists"
    )

    args = parser.parse_args()

    print("Creating admin user...")
    print(f"  Username: {args.username}")
    print(f"  Password: {'*' * len(args.password)}")
    print()

    success = create_admin(args.username, args.password, args.force)
    sys.exit(0 if success else 1)
