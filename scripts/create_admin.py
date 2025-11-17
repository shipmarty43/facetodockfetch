#!/usr/bin/env python3
"""
Create admin user.

Usage:
    python create_admin.py --username admin --password secure_password
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database import SessionLocal, User
from backend.app.utils.auth import get_password_hash


def main():
    """Create admin user."""
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")

    args = parser.parse_args()

    db = SessionLocal()

    try:
        # Check if user exists
        existing = db.query(User).filter(User.username == args.username).first()
        if existing:
            print(f"User '{args.username}' already exists!")
            response = input("Update password? (y/n): ")
            if response.lower() == "y":
                existing.password_hash = get_password_hash(args.password)
                existing.role = "admin"
                existing.is_active = True
                db.commit()
                print(f"Updated user '{args.username}' with admin role")
            return

        # Create new admin user
        admin = User(
            username=args.username,
            password_hash=get_password_hash(args.password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print(f"Admin user '{args.username}' created successfully!")
        print(f"Role: admin")
        print("\nYou can now login with these credentials.")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
