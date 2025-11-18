"""Security utilities for encryption and file handling."""
import hashlib
import warnings
from pathlib import Path
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from ..config import settings

# Suppress bcrypt version warning from passlib (bcrypt 4.0+ changed structure)
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks for memory efficiency
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_string_hash(content: str) -> str:
    """Calculate SHA-256 hash of a string."""
    return hashlib.sha256(content.encode()).hexdigest()


def get_encryption_key() -> bytes:
    """Get encryption key for production mode."""
    if settings.is_production:
        if not settings.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY must be set in production mode")
        return settings.ENCRYPTION_KEY.encode()
    return b"dev-key-not-secure-do-not-use-in-production"


def encrypt_data(data: bytes) -> bytes:
    """Encrypt data using Fernet (AES-256)."""
    if not settings.is_production:
        # No encryption in debug mode
        return data

    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(data)


def decrypt_data(encrypted_data: bytes) -> bytes:
    """Decrypt data using Fernet."""
    if not settings.is_production:
        # No encryption in debug mode
        return encrypted_data

    key = get_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted_data)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal attacks."""
    # Remove path separators and parent directory references
    filename = Path(filename).name
    # Remove potentially dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    return filename


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Ensure password is a string and strip whitespace
    if not isinstance(password, str):
        password = str(password)

    password = password.strip()

    # Validate password length
    if not password:
        raise ValueError("Password cannot be empty")

    # Check byte length (bcrypt has 72-byte limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError(f"Password is too long ({len(password_bytes)} bytes). Maximum is 72 bytes.")

    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
