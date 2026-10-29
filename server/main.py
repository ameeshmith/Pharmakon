"""FastAPI application entrypoint mounting the Streamable HTTP FastMCP server."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import MEDICAL_DISCLAIMER, get_settings
from server.db import init_db
from server.http_client import http_client
from server.logging_utils import logger
from server.mcp_server import mcp

mcp_asgi_app = mcp.http_app(
    path="/",
    stateless_http=True,
    transport="streamable-http",
)


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
            "Hosted MCP Server (Streamable HTTP) and REST API for Drug Safety (openFDA), "
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

    app.mount("/mcp", mcp_asgi_app)
    return app


app = create_app()
