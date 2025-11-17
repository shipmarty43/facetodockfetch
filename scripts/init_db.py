#!/usr/bin/env python3
"""
Initialize database tables.

Creates all necessary tables in SQLite database.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database import init_db, engine
from backend.app.config import settings

def main():
    """Initialize database."""
    print("Initializing database...")
    print(f"Database URL: {settings.DATABASE_URL}")

    try:
        # Create tables
        init_db()
        print("Database tables created successfully!")

        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\nCreated tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")

        print("\nDatabase initialization complete!")

    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
