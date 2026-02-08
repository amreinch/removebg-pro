"""
API Key authentication and management
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, APIKey
import secrets
import hashlib
from typing import Optional


def generate_api_key() -> str:
    """Generate a secure random API key"""
    # Format: rbp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx (32 chars after prefix)
    random_part = secrets.token_urlsafe(24)  # ~32 chars base64
    return f"rbp_live_{random_part}"


def hash_api_key(key: str) -> str:
    """Hash API key for storage (store hash, not plain key)"""
    return hashlib.sha256(key.encode()).hexdigest()


async def get_current_user_from_api_key(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate user via API key header
    Header: X-API-Key: rbp_live_xxxxx
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Hash the provided key to compare with stored hash
    key_hash = hash_api_key(x_api_key)
    
    # Find API key in database
    api_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    # Get associated user
    user = db.query(User).filter(User.id == api_key.user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive"
        )
    
    # Check if user has API access (Pro or Business tier)
    if user.subscription_tier not in ["pro", "business"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API access requires Pro or Business subscription"
        )
    
    # Update last used timestamp
    from datetime import datetime
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    
    return user


def check_api_access(user: User):
    """Check if user has API access (Pro or Business tier)"""
    if user.subscription_tier not in ["pro", "business"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API access requires Pro or Business subscription. Upgrade at /pricing"
        )
