"""Celery tasks for async processing."""

from .document_processing import process_document_task, batch_process_documents
