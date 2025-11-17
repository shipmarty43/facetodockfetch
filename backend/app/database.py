"""
Database configuration and session management.
Handles SQLite connection and table creation.
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from .config import settings


# SQLAlchemy setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=settings.is_debug,  # Log SQL queries in debug mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin' or 'operator'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    settings_json = Column(JSON, nullable=True)  # Personal settings

    # Relationships
    uploaded_documents = relationship("Document", back_populates="uploader", foreign_keys="Document.uploaded_by")
    search_logs = relationship("SearchLog", back_populates="user")


class Document(Base):
    """Document model for storing uploaded files metadata."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'pdf', 'jpg', 'png'
    file_size_bytes = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    processing_status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed, requires_review
    version_number = Column(Integer, default=1)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    page_count = Column(Integer, nullable=True)
    has_mrz = Column(Boolean, default=False)

    # Relationships
    uploader = relationship("User", back_populates="uploaded_documents", foreign_keys=[uploaded_by])
    parent_document = relationship("Document", remote_side=[id], backref="versions")
    ocr_results = relationship("OCRResult", back_populates="document", cascade="all, delete-orphan")
    mrz_data = relationship("MRZData", back_populates="document", cascade="all, delete-orphan")
    faces = relationship("Face", back_populates="document", cascade="all, delete-orphan")
    processing_failures = relationship("ProcessingFailure", back_populates="document", cascade="all, delete-orphan")


class OCRResult(Base):
    """OCR results for documents."""
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    full_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)  # Coordinates, blocks, structure
    language_detected = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    attempt_number = Column(Integer, default=1)  # OCR attempt number (1-3)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="ocr_results")


class MRZData(Base):
    """Machine Readable Zone data extracted from documents."""
    __tablename__ = "mrz_data"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document_type = Column(String(10), nullable=True)  # TD1, TD2, TD3
    document_number = Column(String(50), nullable=True, index=True)
    country_code = Column(String(3), nullable=True)
    surname = Column(String(100), nullable=True, index=True)
    given_names = Column(String(100), nullable=True)
    nationality = Column(String(3), nullable=True)
    date_of_birth = Column(String(10), nullable=True)  # YYMMDD
    sex = Column(String(1), nullable=True)
    expiry_date = Column(String(10), nullable=True)  # YYMMDD
    personal_number = Column(String(50), nullable=True)
    optional_data = Column(String(100), nullable=True)
    raw_mrz_line1 = Column(String(50), nullable=True)
    raw_mrz_line2 = Column(String(50), nullable=True)
    raw_mrz_line3 = Column(String(50), nullable=True)  # For TD1
    checksum_valid = Column(Boolean, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="mrz_data")


class Face(Base):
    """Face embeddings and metadata."""
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    face_image_path = Column(String(500), nullable=True)  # Path to cropped face image
    bbox_x = Column(Integer, nullable=True)
    bbox_y = Column(Integer, nullable=True)
    bbox_width = Column(Integer, nullable=True)
    bbox_height = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=True)  # 0-1
    embedding_id = Column(String(100), nullable=True, index=True)  # ID in Elasticsearch
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="faces")


class SearchLog(Base):
    """Log of face search operations."""
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    search_type = Column(String(20), nullable=False)  # photo, webcam, batch
    query_image_hash = Column(String(64), nullable=True)
    similarity_threshold = Column(Float, nullable=False)
    results_count = Column(Integer, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    searched_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="search_logs")


class SystemLog(Base):
    """System audit logs."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ProcessingFailure(Base):
    """Failed document processing attempts."""
    __tablename__ = "processing_failures"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    failure_type = Column(String(50), nullable=False)  # ocr_failed, face_detection_failed, etc.
    attempt_number = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="processing_failures")


# Database dependency for FastAPI
def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
