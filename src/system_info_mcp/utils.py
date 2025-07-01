"""Utility functions for data formatting and caching."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps

from .config import config

# Set up logging
logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

# Type variable for cache decorator
T = TypeVar("T")

# Simple in-memory cache
_cache: Dict[str, Dict[str, Any]] = {}


def bytes_to_gb(bytes_value: int) -> float:
    """Convert bytes to gigabytes with 1 decimal precision."""
    return round(bytes_value / (1024**3), 1)


def bytes_to_mb(bytes_value: int) -> float:
    """Convert bytes to megabytes with 1 decimal precision."""
    return round(bytes_value / (1024**2), 1)


def format_uptime(uptime_seconds: int) -> str:
    """Format uptime seconds into human-readable string."""
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    return ", ".join(parts) if parts else "0 minutes"


def timestamp_to_iso(timestamp: float) -> str:
    """Convert Unix timestamp to ISO format string."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def cache_result(cache_key: str, ttl: Optional[int] = None) -> Any:
    """Decorator to cache function results with TTL."""
    if ttl is None:
        ttl = config.cache_ttl

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_time = time.time()

            # Check if we have cached result
            if cache_key in _cache:
                cache_entry = _cache[cache_key]
                if current_time - cache_entry["timestamp"] < ttl:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cache_entry["data"]

            # Get fresh data
            logger.debug(f"Cache miss for {cache_key}, fetching fresh data")
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Cache the result
            _cache[cache_key] = {"data": result, "timestamp": current_time}

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            current_time = time.time()

            # Check if we have cached result
            if cache_key in _cache:
                cache_entry = _cache[cache_key]
                if current_time - cache_entry["timestamp"] < ttl:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cache_entry["data"]

            # Get fresh data
            logger.debug(f"Cache miss for {cache_key}, fetching fresh data")
            result = func(*args, **kwargs)

            # Cache the result
            _cache[cache_key] = {"data": result, "timestamp": current_time}

            return result

        # Return appropriate wrapper based on whether function is async
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def clear_cache(cache_key: Optional[str] = None) -> None:
    """Clear cache entries. If cache_key is None, clear all entries."""
    if cache_key is None:
        _cache.clear()
        logger.debug("Cleared all cache entries")
    elif cache_key in _cache:
        del _cache[cache_key]
        logger.debug(f"Cleared cache entry for {cache_key}")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    current_time = time.time()
    stats = {"total_entries": len(_cache), "entries": {}}

    for key, entry in _cache.items():
        age = current_time - entry["timestamp"]
        stats["entries"][key] = {
            "age_seconds": round(age, 2),
            "expired": age > config.cache_ttl,
        }

    return stats


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with default fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int with default fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def filter_sensitive_cmdline(cmdline: List[str]) -> List[str]:
    """Filter potentially sensitive information from command line arguments."""
    if not cmdline:
        return []

    filtered = []
    skip_next = False

    for i, arg in enumerate(cmdline):
        if skip_next:
            filtered.append("[REDACTED]")
            skip_next = False
            continue

        # Common sensitive argument patterns
        sensitive_patterns = [
            "--password",
            "-p",
            "--token",
            "--secret",
            "--key",
            "--api-key",
            "--auth",
            "--credential",
            "--pass",
        ]

        # Check if this argument is a sensitive flag
        if any(pattern in arg.lower() for pattern in sensitive_patterns):
            if "=" in arg:
                # Format: --password=secret
                key, _ = arg.split("=", 1)
                filtered.append(f"{key}=[REDACTED]")
            else:
                # Format: --password secret (next arg is the value)
                filtered.append(arg)
                skip_next = True
        else:
            filtered.append(arg)

    return filtered
