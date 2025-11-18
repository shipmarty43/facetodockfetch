#!/usr/bin/env python3
"""Initialize Elasticsearch indices for face embeddings and documents."""
import warnings

# Suppress bcrypt warnings BEFORE any imports
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.elasticsearch_service import elasticsearch_service

if __name__ == "__main__":
    print("Initializing Elasticsearch indices...")

    if not elasticsearch_service.client:
        print("✗ Elasticsearch is not available")
        print("  Make sure Elasticsearch is running on http://localhost:9200")
        sys.exit(1)

    try:
        # Check connection
        if not elasticsearch_service.client.ping():
            print("✗ Cannot connect to Elasticsearch")
            sys.exit(1)

        print("✓ Connected to Elasticsearch")

        # Create indices (elasticsearch_service should handle index creation)
        # For now, just verify connection
        info = elasticsearch_service.client.info()
        print(f"  Elasticsearch version: {info['version']['number']}")
        print("✓ Elasticsearch is ready")
        print("  Indices will be created automatically on first use")

    except Exception as e:
        print(f"✗ Error initializing Elasticsearch: {e}")
        sys.exit(1)
