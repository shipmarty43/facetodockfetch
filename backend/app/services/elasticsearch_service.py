"""Elasticsearch service for vector search and full-text search."""
import logging
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch, helpers
from ..config import settings

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """Service for Elasticsearch operations."""

    def __init__(self):
        """Initialize Elasticsearch connection."""
        self.client = None
        self.connect()

    def connect(self):
        """Connect to Elasticsearch."""
        try:
            self.client = Elasticsearch(
                [settings.ELASTICSEARCH_URL],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )

            # Test connection
            if self.client.ping():
                logger.info("Connected to Elasticsearch successfully")
                self.setup_indices()
            else:
                logger.error("Failed to connect to Elasticsearch")
                self.client = None

        except Exception as e:
            logger.error(f"Elasticsearch connection error: {e}")
            self.client = None

    def setup_indices(self):
        """Create indices if they don't exist."""
        try:
            # Face embeddings index
            if not self.client.indices.exists(index=settings.ELASTICSEARCH_INDEX_FACES):
                face_mapping = {
                    "settings": {
                        "number_of_shards": 2,
                        "number_of_replicas": 1,
                        "index": {
                            "knn": True
                        }
                    },
                    "mappings": {
                        "properties": {
                            "face_id": {"type": "keyword"},
                            "document_id": {"type": "integer"},
                            "embedding_vector": {
                                "type": "dense_vector",
                                "dims": 512,
                                "index": True,
                                "similarity": "cosine"
                            },
                            "quality_score": {"type": "float"},
                            "indexed_at": {"type": "date"}
                        }
                    }
                }
                self.client.indices.create(
                    index=settings.ELASTICSEARCH_INDEX_FACES,
                    body=face_mapping
                )
                logger.info(f"Created index: {settings.ELASTICSEARCH_INDEX_FACES}")

            # Documents full-text index
            if not self.client.indices.exists(index=settings.ELASTICSEARCH_INDEX_DOCUMENTS):
                doc_mapping = {
                    "settings": {
                        "number_of_shards": 2,
                        "number_of_replicas": 1,
                        "analysis": {
                            "analyzer": {
                                "multilingual": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": ["lowercase", "russian_stop", "english_stop"]
                                }
                            },
                            "filter": {
                                "russian_stop": {
                                    "type": "stop",
                                    "stopwords": "_russian_"
                                },
                                "english_stop": {
                                    "type": "stop",
                                    "stopwords": "_english_"
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "document_id": {"type": "integer"},
                            "full_text": {
                                "type": "text",
                                "analyzer": "multilingual"
                            },
                            "mrz_text": {
                                "type": "text",
                                "analyzer": "keyword"
                            },
                            "document_number": {"type": "keyword"},
                            "surname": {"type": "text"},
                            "given_names": {"type": "text"},
                            "uploaded_at": {"type": "date"}
                        }
                    }
                }
                self.client.indices.create(
                    index=settings.ELASTICSEARCH_INDEX_DOCUMENTS,
                    body=doc_mapping
                )
                logger.info(f"Created index: {settings.ELASTICSEARCH_INDEX_DOCUMENTS}")

        except Exception as e:
            logger.error(f"Failed to setup indices: {e}")

    def index_face_embedding(
        self,
        face_id: int,
        document_id: int,
        embedding: List[float],
        quality_score: float
    ) -> bool:
        """
        Index a face embedding for vector search.

        Args:
            face_id: Database face ID
            document_id: Document ID
            embedding: Face embedding vector (512D)
            quality_score: Face quality score

        Returns:
            True if successful
        """
        try:
            if self.client is None:
                return False

            doc = {
                "face_id": str(face_id),
                "document_id": document_id,
                "embedding_vector": embedding,
                "quality_score": quality_score,
                "indexed_at": "now"
            }

            self.client.index(
                index=settings.ELASTICSEARCH_INDEX_FACES,
                id=str(face_id),
                body=doc
            )

            logger.info(f"Indexed face embedding: face_id={face_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index face embedding: {e}")
            return False

    def search_similar_faces(
        self,
        query_embedding: List[float],
        similarity_threshold: float = 0.6,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar faces using kNN vector search.

        Args:
            query_embedding: Query face embedding
            similarity_threshold: Minimum similarity score (0-1)
            max_results: Maximum number of results

        Returns:
            List of similar faces with scores
        """
        try:
            if self.client is None:
                return []

            # kNN search query
            query = {
                "knn": {
                    "field": "embedding_vector",
                    "query_vector": query_embedding,
                    "k": max_results,
                    "num_candidates": max_results * 10
                },
                "_source": ["face_id", "document_id", "quality_score"]
            }

            response = self.client.search(
                index=settings.ELASTICSEARCH_INDEX_FACES,
                body=query
            )

            results = []
            for hit in response["hits"]["hits"]:
                # Convert Elasticsearch score to similarity (0-1)
                similarity = hit["_score"]

                # Filter by threshold
                if similarity >= similarity_threshold:
                    results.append({
                        "face_id": int(hit["_source"]["face_id"]),
                        "document_id": hit["_source"]["document_id"],
                        "similarity_score": similarity,
                        "quality_score": hit["_source"]["quality_score"]
                    })

            logger.info(f"Found {len(results)} similar faces")
            return results

        except Exception as e:
            logger.error(f"Face search failed: {e}")
            return []

    def index_document_text(
        self,
        document_id: int,
        full_text: str,
        mrz_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Index document text for full-text search.

        Args:
            document_id: Document ID
            full_text: Full OCR text
            mrz_data: MRZ data if available

        Returns:
            True if successful
        """
        try:
            if self.client is None:
                return False

            doc = {
                "document_id": document_id,
                "full_text": full_text,
                "uploaded_at": "now"
            }

            if mrz_data:
                doc["mrz_text"] = " ".join([
                    mrz_data.get("raw_mrz_line1", ""),
                    mrz_data.get("raw_mrz_line2", ""),
                    mrz_data.get("raw_mrz_line3", "")
                ])
                doc["document_number"] = mrz_data.get("document_number", "")
                doc["surname"] = mrz_data.get("surname", "")
                doc["given_names"] = mrz_data.get("given_names", "")

            self.client.index(
                index=settings.ELASTICSEARCH_INDEX_DOCUMENTS,
                id=str(document_id),
                body=doc
            )

            logger.info(f"Indexed document text: document_id={document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index document text: {e}")
            return False

    def search_documents_text(
        self,
        query: str,
        search_in: str = "all",
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Full-text search in documents.

        Args:
            query: Search query
            search_in: Where to search (all, ocr, mrz)
            max_results: Maximum results

        Returns:
            List of matching documents
        """
        try:
            if self.client is None:
                return []

            # Build query based on search_in parameter
            if search_in == "mrz":
                search_query = {
                    "multi_match": {
                        "query": query,
                        "fields": ["mrz_text", "document_number", "surname", "given_names"]
                    }
                }
            elif search_in == "ocr":
                search_query = {
                    "match": {
                        "full_text": query
                    }
                }
            else:  # all
                search_query = {
                    "multi_match": {
                        "query": query,
                        "fields": ["full_text^2", "mrz_text", "document_number^3", "surname^2", "given_names^2"]
                    }
                }

            response = self.client.search(
                index=settings.ELASTICSEARCH_INDEX_DOCUMENTS,
                body={
                    "query": search_query,
                    "size": max_results,
                    "highlight": {
                        "fields": {
                            "full_text": {},
                            "surname": {},
                            "given_names": {}
                        }
                    }
                }
            )

            results = []
            for hit in response["hits"]["hits"]:
                highlight = None
                if "highlight" in hit:
                    highlight = " ... ".join(
                        sum(hit["highlight"].values(), [])
                    )

                results.append({
                    "document_id": hit["_source"]["document_id"],
                    "score": hit["_score"],
                    "highlight": highlight
                })

            logger.info(f"Found {len(results)} documents matching query")
            return results

        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []

    def delete_face_embedding(self, face_id: int) -> bool:
        """Delete face embedding from index."""
        try:
            if self.client is None:
                return False

            self.client.delete(
                index=settings.ELASTICSEARCH_INDEX_FACES,
                id=str(face_id),
                ignore=[404]
            )
            return True

        except Exception as e:
            logger.error(f"Failed to delete face embedding: {e}")
            return False

    def delete_document_text(self, document_id: int) -> bool:
        """Delete document from full-text index."""
        try:
            if self.client is None:
                return False

            self.client.delete(
                index=settings.ELASTICSEARCH_INDEX_DOCUMENTS,
                id=str(document_id),
                ignore=[404]
            )
            return True

        except Exception as e:
            logger.error(f"Failed to delete document text: {e}")
            return False


# Global Elasticsearch service instance
elasticsearch_service = ElasticsearchService()
