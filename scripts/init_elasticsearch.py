#!/usr/bin/env python3
"""
Initialize Elasticsearch indices.

Creates face embeddings and documents indices.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.elasticsearch_service import elasticsearch_service
from backend.app.config import settings


def main():
    """Initialize Elasticsearch indices."""
    print("Initializing Elasticsearch indices...")
    print(f"Elasticsearch URL: {settings.ELASTICSEARCH_URL}")

    try:
        # Check connection
        if not elasticsearch_service.client:
            print("Error: Cannot connect to Elasticsearch")
            print("Make sure Elasticsearch is running")
            sys.exit(1)

        if not elasticsearch_service.client.ping():
            print("Error: Elasticsearch is not responding")
            sys.exit(1)

        print("Connected to Elasticsearch successfully")

        # Setup indices
        elasticsearch_service.setup_indices()

        # Verify indices
        indices = elasticsearch_service.client.cat.indices(format="json")
        our_indices = [
            idx for idx in indices
            if idx["index"] in [
                settings.ELASTICSEARCH_INDEX_FACES,
                settings.ELASTICSEARCH_INDEX_DOCUMENTS
            ]
        ]

        print(f"\nCreated indices ({len(our_indices)}):")
        for idx in our_indices:
            print(f"  - {idx['index']} ({idx['docs.count']} documents)")

        print("\nElasticsearch initialization complete!")

    except Exception as e:
        print(f"Error initializing Elasticsearch: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
