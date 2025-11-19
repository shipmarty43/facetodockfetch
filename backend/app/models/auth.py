"""Authentication and user management models."""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime


class UserLogin(BaseModel):
    """User login request."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    """User creation request (admin only)."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Literal["admin", "operator"] = "operator"


class UserUpdate(BaseModel):
    """User update request (admin only)."""
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[Literal["admin", "operator"]] = None
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    role: str
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    settings_json: Optional[dict] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # username
    exp: datetime
    role: str


class UserSettings(BaseModel):
    """User personal settings."""
    face_similarity_threshold: float = Field(0.6, ge=0.0, le=1.0)
    results_per_page: int = Field(50, ge=10, le=200)
    language: str = "en"
