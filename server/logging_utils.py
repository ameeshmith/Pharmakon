"""Structured logging and strict secret redaction utilities."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import UTC, datetime
from typing import Any

from server.config import get_settings

_API_KEY_QUERY_RE = re.compile(r"([?&]api_key=)[^&\s\"']+", re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """Remove any api_key query param or raw OPENFDA_API_KEY from text/URLs."""
    if not text:
        return text
    cleaned = _API_KEY_QUERY_RE.sub(r"\1[REDACTED]", text)
    settings = get_settings()
    secret = settings.effective_openfda_key
    if secret and len(secret) >= 4:
        cleaned = cleaned.replace(secret, "[REDACTED]")
    env_secret = os.environ.get("OPENFDA_API_KEY", "").strip()
    if env_secret and len(env_secret) >= 4:
        cleaned = cleaned.replace(env_secret, "[REDACTED]")
    ncbi_secret = os.environ.get("NCBI_API_KEY", "").strip()
    if ncbi_secret and len(ncbi_secret) >= 4:
        cleaned = cleaned.replace(ncbi_secret, "[REDACTED]")
    return cleaned


class SecretRedactingFilter(logging.Filter):
    """Logging filter that strips OPENFDA_API_KEY and api_key= from all records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_text(record.msg)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    sanitize_text(str(a)) if isinstance(a, str) else a for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: sanitize_text(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
        return True


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON with secret redaction."""

    def format(self, record: logging.LogRecord) -> str:
        message = sanitize_text(record.getMessage())
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }
        for extra_field in ("tool", "latency_ms", "status", "key_prefix", "endpoint"):
            val = getattr(record, extra_field, None)
            if val is not None:
                payload[extra_field] = sanitize_text(val) if isinstance(val, str) else val
        if record.exc_info:
            payload["exception"] = sanitize_text(self.formatException(record.exc_info))
        return json.dumps(payload)


def configure_logging() -> logging.Logger:
    """Configure root/pharmakon structured logger with redaction filter."""
    logger = logging.getLogger("pharmakon")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(SecretRedactingFilter())
    logger.addHandler(handler)
    logger.propagate = False

    # Also attach redaction filter to httpx/uvicorn loggers so URLs never leak keys
    for noisy_logger_name in ("httpx", "httpcore", "uvicorn", "uvicorn.access"):
        ext_logger = logging.getLogger(noisy_logger_name)
        ext_logger.addFilter(SecretRedactingFilter())
        if noisy_logger_name in ("httpx", "httpcore"):
            ext_logger.setLevel(logging.WARNING)

    return logger


logger = configure_logging()
