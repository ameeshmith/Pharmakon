"""REST API routes for Auth, API Key management, Usage Analytics, Tool Schemas, and Playground proxy."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from server.auth import (
    create_access_token,
    decode_access_token,
    extract_bearer_token,
    generate_api_key,
    get_current_user,
    hash_password,
    verify_api_key_in_db,
    verify_password,
)
from server.config import MEDICAL_DISCLAIMER, get_settings
from server.db import get_db
from server.models import APIKey, UsageLog, User
from server.rate_limit import rate_limiter
from server.tool_registry import TOOL_SCHEMAS, execute_tool_by_name

router = APIRouter(prefix="/api")


class SignupRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class CreateKeyRequest(BaseModel):
    name: str = Field(
        default="Default MCP Key",
        min_length=1,
        max_length=100,
        description="Human-readable label for the API key (e.g. 'Claude Desktop', 'Cursor IDE').",
    )


class PlaygroundRunRequest(BaseModel):
    tool: str = Field(..., description="Name of the MCP tool to execute.")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Input arguments matching the tool's schema."
    )


def _validate_email(email: str) -> str:
    cleaned = email.strip().lower()
    if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Please provide a valid email address.",
        )
    return cleaned


@router.post(
    "/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, tags=["auth"]
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Create a new user account and issue a JWT session token."""
    email = _validate_email(payload.email)
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.post("/auth/login", response_model=AuthResponse, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Authenticate an existing user with email + password and issue a JWT token."""
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.get("/auth/me", tags=["auth"])
def get_me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Return profile details for the currently logged-in user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat(),
    }


@router.get("/keys", tags=["keys"])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List all API keys (active and revoked) belonging to the authenticated user."""
    keys = (
        db.query(APIKey)
        .filter(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
        .all()
    )
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "key_prefix": k.key_prefix,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat(),
                "revoked_at": k.revoked_at.isoformat() if k.revoked_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            }
            for k in keys
        ]
    }


@router.post("/keys", status_code=status.HTTP_201_CREATED, tags=["keys"])
def create_api_key_route(
    payload: CreateKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a new hashed API key. The plaintext `raw_key` is returned ONLY ONCE."""
    raw_key, key_prefix, key_hash = generate_api_key()
    key_row = APIKey(
        user_id=current_user.id,
        name=payload.name.strip() or "MCP Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        is_active=True,
    )
    db.add(key_row)
    db.commit()
    db.refresh(key_row)

    return {
        "id": key_row.id,
        "name": key_row.name,
        "key_prefix": key_row.key_prefix,
        "raw_key": raw_key,
        "is_active": key_row.is_active,
        "created_at": key_row.created_at.isoformat(),
        "notice": "Save this API key now. For security, only its SHA-256 hash is stored and it cannot be viewed again.",
    }


@router.delete("/keys/{key_id}", tags=["keys"])
def revoke_api_key_route(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Revoke an existing API key belonging to the authenticated user."""
    key_row = (
        db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == current_user.id).first()
    )
    if not key_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found.",
        )

    key_row.is_active = False
    key_row.revoked_at = datetime.now(UTC)
    db.commit()
    db.refresh(key_row)

    return {
        "id": key_row.id,
        "name": key_row.name,
        "key_prefix": key_row.key_prefix,
        "is_active": key_row.is_active,
        "revoked_at": key_row.revoked_at.isoformat() if key_row.revoked_at else None,
    }


@router.get("/usage/stats", tags=["usage"])
def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return usage analytics by day, by tool, recent invocations, and live rate limit status."""
    user_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    key_ids = [k.id for k in user_keys]
    key_map = {k.id: k for k in user_keys}

    now = datetime.now(UTC)
    seven_days_ago = now - timedelta(days=6)
    day_buckets: dict[str, int] = {
        (seven_days_ago + timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(7)
    }
    by_tool: dict[str, int] = defaultdict(int)
    recent_logs: list[dict[str, Any]] = []
    total_calls = 0
    avg_latency_ms = 0.0

    if key_ids:
        logs = (
            db.query(UsageLog)
            .filter(UsageLog.api_key_id.in_(key_ids))
            .order_by(UsageLog.timestamp.desc())
            .limit(500)
            .all()
        )
        total_calls = len(logs)
        if logs:
            avg_latency_ms = round(sum(log.latency_ms for log in logs) / len(logs), 1)
        for log in logs:
            ts = log.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            day_str = ts.strftime("%Y-%m-%d")
            if day_str in day_buckets:
                day_buckets[day_str] += 1
            by_tool[log.tool_name] += 1

        for log in logs[:20]:
            k_obj = key_map.get(log.api_key_id or -1)
            recent_logs.append(
                {
                    "id": log.id,
                    "tool_name": log.tool_name,
                    "latency_ms": round(log.latency_ms, 1),
                    "status": log.status,
                    "key_name": k_obj.name if k_obj else "Key",
                    "key_prefix": k_obj.key_prefix if k_obj else "",
                    "timestamp": log.timestamp.isoformat(),
                }
            )

    active_key = next((k for k in user_keys if k.is_active), None)
    if active_key:
        rl_status = rate_limiter.peek_status(
            f"key:{active_key.id}", api_key_id=active_key.id, db=db
        )
    else:
        settings = get_settings()
        rl_status = rate_limiter.peek_status(f"user:{current_user.id}", db=db)
        rl_status.limit_minute = settings.rate_limit_per_minute
        rl_status.limit_day = settings.rate_limit_per_day

    return {
        "total_calls": total_calls,
        "average_latency_ms": avg_latency_ms,
        "active_keys_count": sum(1 for k in user_keys if k.is_active),
        "by_day": [{"date": d, "count": c} for d, c in sorted(day_buckets.items())],
        "by_tool": [
            {"tool": t, "count": c} for t, c in sorted(by_tool.items(), key=lambda x: (-x[1], x[0]))
        ],
        "recent_calls": recent_logs,
        "rate_limit": {
            "limit_per_minute": rl_status.limit_minute,
            "remaining_minute": rl_status.remaining_minute,
            "limit_per_day": rl_status.limit_day,
            "remaining_day": rl_status.remaining_day,
        },
    }


@router.get("/tools", tags=["tools"])
def get_tools_catalog() -> dict[str, Any]:
    """Return schemas, descriptions, parameters, and examples for all 6 MCP tools."""
    settings = get_settings()
    return {
        "server_name": settings.app_name,
        "version": settings.app_version,
        "mcp_endpoint": "/mcp",
        "transport": "streamable-http",
        "rate_limits": {
            "requests_per_minute": settings.rate_limit_per_minute,
            "requests_per_day": settings.rate_limit_per_day,
        },
        "tools": TOOL_SCHEMAS,
        "disclaimer": MEDICAL_DISCLAIMER,
    }


@router.post("/playground/run", tags=["playground"])
async def run_playground_tool(
    payload: PlaygroundRunRequest,
    request: Request,
    response: Response,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Execute any of the 6 MCP tools from the Web Playground with rate limiting and usage logging."""
    valid_tool_names = {t["name"] for t in TOOL_SCHEMAS}
    if payload.tool not in valid_tool_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tool '{payload.tool}'. Valid tools: {sorted(valid_tool_names)}",
        )

    bearer = extract_bearer_token(authorization)
    raw_api_key = x_api_key or (bearer if bearer and bearer.startswith("pk_live_") else None)

    api_key_id: int | None = None
    bucket_id = f"ip:{request.client.host if request.client else 'local'}"

    if raw_api_key:
        key_obj = verify_api_key_in_db(db, raw_api_key)
        if not key_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked Pharmakon API key.",
            )
        api_key_id = key_obj.id
        bucket_id = f"key:{key_obj.id}"
    elif bearer:
        # Logged-in JWT session user: attribute to their primary active API key if present
        try:
            jwt_data = decode_access_token(bearer)
            uid = int(jwt_data.get("sub", 0))
            bucket_id = f"user:{uid}"
            first_key = (
                db.query(APIKey)
                .filter(APIKey.user_id == uid, APIKey.is_active.is_(True))
                .order_by(APIKey.created_at.asc())
                .first()
            )
            if first_key:
                api_key_id = first_key.id
                bucket_id = f"key:{first_key.id}"
        except HTTPException:
            pass

    decision = rate_limiter.check_and_consume(bucket_id, api_key_id=api_key_id, db=db)
    for hk, hv in decision.headers().items():
        response.headers[hk] = hv

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=decision.reason or "Rate limit exceeded.",
            headers=decision.headers(),
        )

    result = await execute_tool_by_name(
        payload.tool,
        payload.arguments,
        api_key_id=api_key_id,
    )
    return {
        "tool": payload.tool,
        "arguments": payload.arguments,
        "result": result,
        "rate_limit": {
            "limit_minute": decision.limit_minute,
            "remaining_minute": decision.remaining_minute,
            "limit_day": decision.limit_day,
            "remaining_day": decision.remaining_day,
        },
    }
