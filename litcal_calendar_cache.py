"""
litcal_calendar_cache.py - File-based cache for liturgical calendar data.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Create logger as a child of the main litcal logger
logger = logging.getLogger("litcal.cache")

# === CONFIGURATION ===
CACHE_EXPIRY_HOURS = 24 * 7  # Cache for 1 week
CACHE_DIR = Path("cache")  # Will be created in the same directory as the script


@dataclass(frozen=True)
class CalendarCacheKey:
    """
    Immutable key for identifying cached calendar data.

    Attributes:
        calendar_type: Type of calendar ("general", "national", or "diocesan")
        calendar_id: Calendar identifier (nation code or diocese id, empty for general)
        year: Calendar year
        locale: Locale code for the calendar content (default: "en")
    """

    calendar_type: str
    calendar_id: str
    year: int
    locale: str = "en"

    def __post_init__(self):
        """Validate the calendar type."""
        valid_types = ("general", "national", "diocesan")
        if self.calendar_type not in valid_types:
            raise ValueError(
                f"Invalid calendar type: {self.calendar_type}. "
                f"Must be one of {valid_types}"
            )

    def to_cache_filename(self) -> str:
        """
        Build a unique cache filename for this key.

        Returns:
            A unique cache key string including all parameters
        """
        locale_part = self.locale.replace("-", "_")  # Normalize locale format

        if self.calendar_type == "general":
            return f"general_{self.year}_{locale_part}"
        if self.calendar_type == "national":
            return f"national_{self.calendar_id.upper()}_{self.year}_{locale_part}"
        # diocesan
        return f"diocesan_{self.calendar_id.lower()}_{self.year}_{locale_part}"


class CalendarDataCache:
    """File-based cache for liturgical calendar data."""

    def __init__(self):
        """Initialize the cache directory."""
        self._cache_dir = CACHE_DIR
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self._cache_dir.mkdir(exist_ok=True)

    def _get_cache_file(self, key: CalendarCacheKey) -> Path:
        """Get the cache file path for a given key."""
        filename = key.to_cache_filename()
        return self._cache_dir / f"{filename}.json"

    def _get_sync(self, key: CalendarCacheKey) -> Optional[Dict[str, Any]]:
        """Synchronous implementation of get -- kept as a helper so async
        variant can run this off the event loop with asyncio.to_thread.

        This function performs blocking file I/O.
        """
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return None

        try:
            stats = cache_file.stat()
            age = datetime.now() - datetime.fromtimestamp(stats.st_mtime)

            # Check if cache has expired
            if age > timedelta(hours=CACHE_EXPIRY_HOURS):
                logger.info("Cache expired for %s", key.to_cache_filename())
                return None

            # Read and return cached data
            with cache_file.open("r", encoding="utf-8") as f:
                return json.load(f)

        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error reading cache file %s: %s", cache_file, e)
            return None

    def get(self, key: CalendarCacheKey) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper kept for callers that expect blocking behavior.

        Prefer using ``async_get`` from asyncio-based handlers so file I/O
        runs off the event loop.
        """
        return self._get_sync(key)

    async def async_get(self, key: CalendarCacheKey) -> Optional[Dict[str, Any]]:
        """Asynchronous get which offloads blocking file I/O to a thread pool.

        Use this from asyncio-based handlers to avoid blocking the event loop.
        """
        return await asyncio.to_thread(self._get_sync, key)

    def _update_sync(self, key: CalendarCacheKey, data: Dict[str, Any]) -> None:
        """Synchronous implementation of update; used by async wrapper."""
        cache_file = self._get_cache_file(key)

        try:
            # Write data to cache file
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(
                "Successfully cached calendar data for %s", key.to_cache_filename()
            )

        except OSError as e:
            logger.error("Error writing to cache file %s: %s", cache_file, e)

    def update(self, key: CalendarCacheKey, data: Dict[str, Any]) -> None:
        """Synchronous wrapper kept for compatibility; prefer ``async_update``."""
        return self._update_sync(key, data)

    async def async_update(self, key: CalendarCacheKey, data: Dict[str, Any]) -> None:
        """Asynchronous update which offloads blocking file I/O to a thread pool.

        Use this from asyncio-based handlers to avoid blocking the event loop.
        """
        await asyncio.to_thread(self._update_sync, key, data)

    def clear(self, key: Optional[CalendarCacheKey] = None) -> None:
        """
        Clear cached data. If no parameters are provided, clears all cache.

        Args:
            key: Optional CalendarCacheKey to clear specific cached data.
                 If None, clears all cache files.
        """
        if key is None:
            # Clear all cache
            for file in self._cache_dir.glob("*.json"):
                file.unlink()
            logger.info("Cleared all calendar cache")
            return

        # Clear specific cache file
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            cache_file.unlink()
            logger.info("Cleared cache for %s", key.to_cache_filename())
        else:
            logger.info("No cache found for %s", key.to_cache_filename())
