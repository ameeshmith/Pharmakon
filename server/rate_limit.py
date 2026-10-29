"""Per-key sliding-window minute rate limiter, daily call cap, and usage logger."""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from server.config import get_settings
from server.db import get_session_factory
from server.logging_utils import logger, sanitize_text
from server.models import UsageLog


@dataclass
class RateLimitDecision:
    """Result of checking rate limits for an API key or client bucket."""

    allowed: bool
    retry_after_seconds: int
    limit_minute: int
    remaining_minute: int
    limit_day: int
    remaining_day: int
    reason: str | None = None

    def headers(self) -> dict[str, str]:
        h = {
            "X-RateLimit-Limit-Minute": str(self.limit_minute),
            "X-RateLimit-Remaining-Minute": str(max(0, self.remaining_minute)),
            "X-RateLimit-Limit-Day": str(self.limit_day),
            "X-RateLimit-Remaining-Day": str(max(0, self.remaining_day)),
        }
        if not self.allowed:
            h["Retry-After"] = str(max(1, self.retry_after_seconds))
        return h


class KeyRateLimiter:
    """Sliding-window per-minute and daily call quota tracker per API key."""

    def __init__(self) -> None:
        self._minute_windows: dict[str, deque[float]] = defaultdict(deque)
        self._daily_counts: dict[tuple[str, str], int] = defaultdict(int)

    def reset(self) -> None:
        self._minute_windows.clear()
        self._daily_counts.clear()

    @staticmethod
    def _utc_day_str(now_dt: datetime | None = None) -> str:
        dt = now_dt or datetime.now(UTC)
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def _seconds_until_utc_midnight(now_dt: datetime | None = None) -> int:
        dt = now_dt or datetime.now(UTC)
        tomorrow = datetime(dt.year, dt.month, dt.day, tzinfo=UTC).timestamp() + 86400
        return max(1, int(math.ceil(tomorrow - dt.timestamp())))

    def _get_daily_usage(self, bucket_id: str, api_key_id: int | None, db: Session | None) -> int:
        today_str = self._utc_day_str()
        mem_count = self._daily_counts.get((bucket_id, today_str), 0)
        if api_key_id is not None and db is not None:
            now_dt = datetime.now(UTC)
            day_start = datetime(now_dt.year, now_dt.month, now_dt.day, tzinfo=UTC)
            db_count = (
                db.query(func.count(UsageLog.id))
                .filter(
                    UsageLog.api_key_id == api_key_id,
                    UsageLog.timestamp >= day_start,
                )
                .scalar()
                or 0
            )
            return max(mem_count, int(db_count))
        return mem_count

    def check_and_consume(
        self,
        bucket_id: str,
        *,
        api_key_id: int | None = None,
        db: Session | None = None,
    ) -> RateLimitDecision:
        """Check whether `bucket_id` is within minute and daily quotas and consume 1 unit if allowed."""
        settings = get_settings()
        limit_min = max(1, settings.rate_limit_per_minute)
        limit_day = max(1, settings.rate_limit_per_day)

        now = time.time()
        window_start = now - 60.0
        q = self._minute_windows[bucket_id]
        while q and q[0] <= window_start:
            q.popleft()

        used_day = self._get_daily_usage(bucket_id, api_key_id, db)

        # 1. Check daily quota first
        if used_day >= limit_day:
            retry_after = self._seconds_until_utc_midnight()
            return RateLimitDecision(
                allowed=False,
                retry_after_seconds=retry_after,
                limit_minute=limit_min,
                remaining_minute=max(0, limit_min - len(q)),
                limit_day=limit_day,
                remaining_day=0,
                reason=f"Daily call quota ({limit_day} requests/day) exceeded.",
            )

        # 2. Check per-minute sliding window
        if len(q) >= limit_min:
            oldest = q[0]
            retry_after = max(1, int(math.ceil((oldest + 60.0) - now)))
            return RateLimitDecision(
                allowed=False,
                retry_after_seconds=retry_after,
                limit_minute=limit_min,
                remaining_minute=0,
                limit_day=limit_day,
                remaining_day=max(0, limit_day - used_day),
                reason=f"Per-minute rate limit ({limit_min} requests/minute) exceeded.",
            )

        # Consume 1 request slot
        q.append(now)
        today_str = self._utc_day_str()
        self._daily_counts[(bucket_id, today_str)] = used_day + 1

        return RateLimitDecision(
            allowed=True,
            retry_after_seconds=0,
            limit_minute=limit_min,
            remaining_minute=max(0, limit_min - len(q)),
            limit_day=limit_day,
            remaining_day=max(0, limit_day - (used_day + 1)),
        )

    def peek_status(
        self,
        bucket_id: str,
        *,
        api_key_id: int | None = None,
        db: Session | None = None,
    ) -> RateLimitDecision:
        """Inspect current rate limit consumption without consuming a slot."""
        settings = get_settings()
        limit_min = max(1, settings.rate_limit_per_minute)
        limit_day = max(1, settings.rate_limit_per_day)

        now = time.time()
        window_start = now - 60.0
        q = self._minute_windows[bucket_id]
        while q and q[0] <= window_start:
            q.popleft()

        used_day = self._get_daily_usage(bucket_id, api_key_id, db)
        return RateLimitDecision(
            allowed=(len(q) < limit_min and used_day < limit_day),
            retry_after_seconds=0,
            limit_minute=limit_min,
            remaining_minute=max(0, limit_min - len(q)),
            limit_day=limit_day,
            remaining_day=max(0, limit_day - used_day),
        )


rate_limiter = KeyRateLimiter()


def record_tool_usage(
    *,
    api_key_id: int | None,
    tool_name: str,
    latency_ms: float,
    status: str,
    error_message: str | None = None,
) -> None:
    """Persist a UsageLog entry and emit a structured log line."""
    clean_err = sanitize_text(error_message)[:500] if error_message else None
    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            log_row = UsageLog(
                api_key_id=api_key_id,
                tool_name=tool_name,
                latency_ms=round(latency_ms, 2),
                status=status,
                error_message=clean_err,
            )
            db.add(log_row)
            db.commit()
    except Exception as exc:
        logger.warning(f"Failed to persist usage log: {sanitize_text(str(exc))}")

    logger.info(
        f"Tool {tool_name} completed with status={status} in {latency_ms:.1f}ms",
        extra={
            "tool": tool_name,
            "latency_ms": round(latency_ms, 2),
            "status": status,
        },
    )
