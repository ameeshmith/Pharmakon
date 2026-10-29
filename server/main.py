"""FastAPI application entrypoint mounting the Streamable HTTP FastMCP server and REST API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from server.api_routes import router as api_router
from server.auth import extract_bearer_token, verify_api_key_in_db
from server.config import MEDICAL_DISCLAIMER, get_settings
from server.db import get_session_factory, init_db
from server.http_client import http_client
from server.logging_utils import logger
from server.mcp_server import current_mcp_api_key_id, mcp
from server.rate_limit import rate_limiter

mcp_asgi_app = mcp.http_app(
    path="/",
    stateless_http=True,
    transport="streamable-http",
)


class AuthenticatedMCPApp:
    """ASGI wrapper enforcing Bearer API key authentication and per-key rate limits on /mcp."""

    def __init__(self, inner: ASGIApp) -> None:
        self.inner = inner

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.inner(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        if request.method == "OPTIONS":
            await self.inner(scope, receive, send)
            return

        auth_header = request.headers.get("authorization")
        raw_key = extract_bearer_token(auth_header) or request.headers.get("x-api-key")
        if not raw_key:
            resp = JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Missing Bearer API key. Pass 'Authorization: Bearer pk_live_...' to connect to /mcp.",
                },
            )
            await resp(scope, receive, send)
            return

        session_factory = get_session_factory()
        with session_factory() as db:
            api_key = verify_api_key_in_db(db, raw_key)
            if api_key is None:
                resp = JSONResponse(
                    status_code=401,
                    content={
                        "error": "Unauthorized",
                        "message": "Invalid or revoked API key.",
                    },
                )
                await resp(scope, receive, send)
                return

            decision = rate_limiter.check_and_consume(
                f"key:{api_key.id}", api_key_id=api_key.id, db=db
            )
            key_id = api_key.id

        if not decision.allowed:
            resp = JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": decision.reason or "Rate limit exceeded.",
                    "retry_after_seconds": decision.retry_after_seconds,
                },
                headers=decision.headers(),
            )
            await resp(scope, receive, send)
            return

        token_ctx = current_mcp_api_key_id.set(key_id)
        try:
            await self.inner(scope, receive, send)
        finally:
            current_mcp_api_key_id.reset(token_ctx)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize SQLite/PostgreSQL schema, log openFDA key mode, and run FastMCP lifespan."""
    settings = get_settings()
    init_db()
    if not settings.effective_openfda_key:
        logger.warning(
            "OPENFDA_API_KEY is not set. Running openFDA requests in keyless mode "
            "(rate limit: 240 req/min, 1,000 req/day per IP). Set OPENFDA_API_KEY in .env for 120,000 req/day."
        )
    else:
        logger.info("OPENFDA_API_KEY detected and configured (authenticated openFDA tier active).")

    async with mcp_asgi_app.lifespan(app):
        yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Pharmakon — Hosted MCP Server (Streamable HTTP) and REST API for Drug Safety (openFDA), "
            "Clinical Trials (ClinicalTrials.gov v2), Literature (PubMed), and Drug Normalization (RxNorm)."
        ),
        lifespan=app_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "Retry-After",
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Limit-Day",
            "X-RateLimit-Remaining-Day",
        ],
    )

    @app.get("/health", tags=["system"])
    @app.get("/api/health", tags=["system"])
    async def health_check() -> dict[str, Any]:
        cfg = get_settings()
        return {
            "status": "ok",
            "service": cfg.app_name,
            "version": cfg.app_version,
            "mcp_transport": "streamable-http",
            "mcp_endpoint": "/mcp",
            "openfda_key_configured": bool(cfg.effective_openfda_key),
            "cache_stats": http_client.stats,
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    app.include_router(api_router)
    app.mount("/mcp", AuthenticatedMCPApp(mcp_asgi_app))
    return app


app = create_app()
