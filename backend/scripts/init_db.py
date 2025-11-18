#!/usr/bin/env python3
"""Initialize SQLite database - create all tables."""
import warnings

# Suppress bcrypt warnings BEFORE any imports
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db

if __name__ == "__main__":
    print("Initializing SQLite database...")
    try:
        init_db()
        print("✓ Database initialized successfully")
        print("  Tables created in data/db/face_recognition.db")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
