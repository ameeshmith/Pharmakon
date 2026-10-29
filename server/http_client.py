"""Resilient upstream HTTP client with SQLite + memory TTL caching, retries, and key redaction."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from server.config import get_settings
from server.db import get_session_factory
from server.logging_utils import logger, sanitize_text
from server.models import HTTPCache

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class UpstreamAPIError(Exception):
    """Raised when an upstream biomedical API fails after retries."""

    def __init__(self, source: str, message: str, status_code: int | None = None) -> None:
        clean_msg = sanitize_text(message)
        super().__init__(clean_msg)
        self.source = source
        self.message = clean_msg
        self.status_code = status_code


class CachedHttpClient:
    """HTTP client with SQLite/in-memory TTL cache, exponential backoff, and secret scrubbing."""

    def __init__(self) -> None:
        self._mem_cache: dict[str, tuple[float, str, str]] = {}
        self._stats = {"hits": 0, "misses": 0, "errors": 0}

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    def clear_cache(self) -> None:
        """Clear both in-memory and SQLite cache entries."""
        self._mem_cache.clear()
        try:
            session_factory = get_session_factory()
            with session_factory() as db:
                db.query(HTTPCache).delete()
                db.commit()
        except Exception:
            pass

    @staticmethod
    def _make_cache_key(url: str, params: dict[str, Any] | list[tuple[str, Any]] | None) -> str:
        """Build a deterministic SHA-256 key excluding sensitive api_key params."""
        clean_items: list[tuple[str, str]] = []
        if isinstance(params, dict):
            for k, v in sorted(params.items()):
                if k.lower() == "api_key" or v is None:
                    continue
                clean_items.append((str(k), str(v)))
        elif isinstance(params, list):
            for k, v in sorted(params, key=lambda x: (str(x[0]), str(x[1]))):
                if str(k).lower() == "api_key" or v is None:
                    continue
                clean_items.append((str(k), str(v)))
        canonical = f"GET|{sanitize_text(url)}|{urlencode(clean_items)}"
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _get_cached(self, cache_key: str) -> tuple[str, str] | None:
        now = time.time()
        mem_item = self._mem_cache.get(cache_key)
        if mem_item is not None:
            expires_at, content_type, payload = mem_item
            if expires_at > now:
                self._stats["hits"] += 1
                return content_type, payload
            self._mem_cache.pop(cache_key, None)

        try:
            session_factory = get_session_factory()
            with session_factory() as db:
                row = db.get(HTTPCache, cache_key)
                if row is not None:
                    if row.expires_at > now:
                        self._mem_cache[cache_key] = (
                            row.expires_at,
                            row.content_type,
                            row.payload,
                        )
                        self._stats["hits"] += 1
                        return row.content_type, row.payload
                    db.delete(row)
                    db.commit()
        except Exception:
            pass
        return None

    def _set_cached(
        self,
        cache_key: str,
        url: str,
        status_code: int,
        content_type: str,
        payload: str,
        ttl_seconds: int,
    ) -> None:
        if ttl_seconds <= 0:
            return
        now = time.time()
        expires_at = now + ttl_seconds
        safe_url = sanitize_text(url)[:1024]
        self._mem_cache[cache_key] = (expires_at, content_type, payload)

        try:
            session_factory = get_session_factory()
            with session_factory() as db:
                existing = db.get(HTTPCache, cache_key)
                if existing:
                    existing.payload = payload
                    existing.status_code = status_code
                    existing.content_type = content_type
                    existing.created_at = now
                    existing.expires_at = expires_at
                else:
                    db.add(
                        HTTPCache(
                            cache_key=cache_key,
                            url=safe_url,
                            status_code=status_code,
                            content_type=content_type,
                            payload=payload,
                            created_at=now,
                            expires_at=expires_at,
                        )
                    )
                db.commit()
        except Exception:
            pass

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        source: str = "upstream",
        ttl_seconds: int | None = None,
        max_retries: int = 3,
        timeout: float = 15.0,
        allow_404_empty: bool = False,
    ) -> dict[str, Any]:
        """Fetch JSON with TTL cache, exponential backoff, and key sanitization."""
        raw_text = await self.get_text(
            url,
            params=params,
            source=source,
            ttl_seconds=ttl_seconds,
            max_retries=max_retries,
            timeout=timeout,
            allow_404_empty=allow_404_empty,
            expected_type="application/json",
        )
        if not raw_text:
            return {}
        try:
            data = json.loads(raw_text)
            return data if isinstance(data, dict) else {"data": data}
        except json.JSONDecodeError as exc:
            self._stats["errors"] += 1
            raise UpstreamAPIError(source, f"{source} returned invalid JSON response.") from exc

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        source: str = "upstream",
        ttl_seconds: int | None = None,
        max_retries: int = 3,
        timeout: float = 15.0,
        allow_404_empty: bool = False,
        expected_type: str = "text/plain",
    ) -> str:
        """Fetch text/XML/JSON with TTL cache and exponential backoff."""
        settings = get_settings()
        ttl = settings.cache_ttl_seconds if ttl_seconds is None else ttl_seconds
        cache_key = self._make_cache_key(url, params)

        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached[1]

        self._stats["misses"] += 1
        headers = {
            "User-Agent": "Pharmakon-MCP/0.1.0 (https://github.com/ameeshmith/Pharmakon; biomedical-safety-research)",
            "Accept": "application/json, text/xml, */*",
        }

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=timeout, headers=headers, follow_redirects=True
                ) as client:
                    response = await client.get(url, params=params)

                if response.status_code == 404 and allow_404_empty:
                    self._set_cached(cache_key, url, 404, expected_type, "", ttl)
                    return ""

                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < max_retries - 1:
                    backoff = 0.4 * (2**attempt)
                    logger.warning(
                        f"Transient HTTP {response.status_code} from {source} (attempt {attempt + 1}/{max_retries}); retrying in {backoff:.1f}s"
                    )
                    await asyncio.sleep(backoff)
                    continue

                if response.status_code >= 400:
                    self._stats["errors"] += 1
                    raise UpstreamAPIError(
                        source=source,
                        message=f"{source} API returned HTTP {response.status_code} for {sanitize_text(str(response.url))}",
                        status_code=response.status_code,
                    )

                text_body = response.text
                self._set_cached(
                    cache_key,
                    url,
                    response.status_code,
                    response.headers.get("content-type", expected_type),
                    text_body,
                    ttl,
                )
                return text_body

            except UpstreamAPIError:
                raise
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    backoff = 0.4 * (2**attempt)
                    logger.warning(
                        f"Network error contacting {source} (attempt {attempt + 1}/{max_retries}): {sanitize_text(str(exc))}"
                    )
                    await asyncio.sleep(backoff)
                    continue

        self._stats["errors"] += 1
        err_detail = sanitize_text(str(last_exc)) if last_exc else "unreachable"
        raise UpstreamAPIError(
            source=source,
            message=f"{source} service is temporarily unavailable after {max_retries} attempts ({err_detail}).",
            status_code=503,
        )


http_client = CachedHttpClient()
