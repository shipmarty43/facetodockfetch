"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db, User
from ..models.auth import UserLogin, Token, UserResponse
from ..utils.auth import create_access_token, create_refresh_token
from ..utils.security import verify_password
from ..dependencies import get_current_user
from ..utils.logging import log_to_database

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with username and password.

    Returns JWT access and refresh tokens.
    """
    # Get user
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        log_to_database(
            db,
            "WARNING",
            "login_failed",
            {"username": credentials.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_access_token(user.username, user.role)
    refresh_token = create_refresh_token(user.username, user.role)

    log_to_database(
        db,
        "INFO",
        "login_success",
        {"username": user.username},
        user_id=user.id
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    # Create new tokens
    access_token = create_access_token(current_user.username, current_user.role)
    refresh_token = create_refresh_token(current_user.username, current_user.role)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout (client should discard tokens).
    """
    log_to_database(
        db,
        "INFO",
        "logout",
        {},
        user_id=current_user.id
    )

    return {"message": "Logged out successfully"}
