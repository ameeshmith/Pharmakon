"""Authentication utilities: bcrypt password hashing, JWT sessions, and SHA-256 hashed API keys."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from server.config import get_settings
from server.db import get_db
from server.models import APIKey, User

KEY_PREFIX_TAG = "pk_live_"


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(user_id: int, email: str) -> str:
    """Generate a signed JWT session token for a user."""
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT session token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return dict(payload)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns:
        (raw_key, key_prefix, key_hash)
        Only `key_prefix` and `key_hash` are stored in the database.
    """
    random_part = secrets.token_urlsafe(28)
    raw_key = f"{KEY_PREFIX_TAG}{random_part}"
    key_prefix = f"{raw_key[:14]}..."
    key_hash = hash_api_key(raw_key)
    return raw_key, key_prefix, key_hash


def hash_api_key(raw_key: str) -> str:
    """Compute SHA-256 hex digest of an API key."""
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


def extract_bearer_token(authorization: str | None) -> str | None:
    """Extract token from an 'Authorization: Bearer <token>' header."""
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency returning the authenticated User from a JWT Bearer token."""
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer session token.",
        )
    payload = decode_access_token(token)
    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )
    return user


def verify_api_key_in_db(db: Session, raw_key: str) -> APIKey | None:
    """Look up an active APIKey by its SHA-256 hash and update last_used_at."""
    if not raw_key:
        return None
    digest = hash_api_key(raw_key)
    api_key = db.query(APIKey).filter(APIKey.key_hash == digest, APIKey.is_active.is_(True)).first()
    if api_key is not None:
        api_key.last_used_at = datetime.now(UTC)
        db.commit()
        db.refresh(api_key)
    return api_key
