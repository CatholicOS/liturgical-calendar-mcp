"""
litcal_calendar_cache.py - File-based cache for liturgical calendar data.
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("litcal-calendar-cache")

# === CONFIGURATION ===
CACHE_EXPIRY_HOURS = 24 * 7  # Cache for 1 week
CACHE_DIR = Path("cache")  # Will be created in the same directory as the script


class CalendarDataCache:
    """File-based cache for liturgical calendar data."""

    def __init__(self):
        """Initialize the cache directory."""
        self._cache_dir = CACHE_DIR
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self._cache_dir.mkdir(exist_ok=True)

    def _build_cache_key(
        self, calendar_type: str, calendar_id: str, year: int, locale: str = "en"
    ) -> str:
        """
        Build a unique cache key for the calendar request.

        Args:
            calendar_type: Type of calendar ("general", "national", or "diocesan")
            calendar_id: Calendar identifier (nation code or diocese id, empty for general)
            year: Calendar year
            locale: Locale code for the calendar content

        Returns:
            A unique cache key string including all parameters
        """
        locale_part = locale.replace("-", "_")  # Normalize locale format

        if calendar_type == "general":
            return f"general_{year}_{locale_part}"
        elif calendar_type == "national":
            return f"national_{calendar_id.upper()}_{year}_{locale_part}"
        else:  # diocesan
            return f"diocesan_{calendar_id.lower()}_{year}_{locale_part}"

    def _get_cache_file(self, cache_key: str) -> Path:
        """Get the cache file path for a given key."""
        return self._cache_dir / f"{cache_key}.json"

    def get(
        self, calendar_type: str, calendar_id: str, year: int, locale: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached calendar data if available and not expired.

        Args:
            calendar_type: Type of calendar ("general", "national", or "diocesan")
            calendar_id: Calendar identifier (nation code or diocese id, empty for general)
            year: Calendar year
            locale: Locale code for the calendar content

        Returns:
            The cached calendar data if available and not expired, None otherwise
        """
        cache_key = self._build_cache_key(calendar_type, calendar_id, year, locale)
        cache_file = self._get_cache_file(cache_key)

        if not cache_file.exists():
            return None

        try:
            stats = cache_file.stat()
            age = datetime.now() - datetime.fromtimestamp(stats.st_mtime)

            # Check if cache has expired
            if age > timedelta(hours=CACHE_EXPIRY_HOURS):
                logger.info("Cache expired for %s", cache_key)
                return None

            # Read and return cached data
            with cache_file.open("r", encoding="utf-8") as f:
                return json.load(f)

        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error reading cache file %s: %s", cache_file, e)
            return None

    def set(
        self,
        calendar_type: str,
        calendar_id: str,
        year: int,
        data: Dict[str, Any],
        locale: str = "en",
    ) -> None:
        """
        Store calendar data in the cache.

        Args:
            calendar_type: Type of calendar ("general", "national", or "diocesan")
            calendar_id: Calendar identifier (nation code or diocese id, empty for general)
            year: Calendar year
            data: Calendar data to cache
            locale: Locale code for the calendar content
        """
        cache_key = self._build_cache_key(calendar_type, calendar_id, year, locale)
        cache_file = self._get_cache_file(cache_key)

        try:
            # Write data to cache file
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info("Successfully cached calendar data for %s", cache_key)

        except OSError as e:
            logger.error("Error writing to cache file %s: %s", cache_file, e)

    def clear(
        self, calendar_type: str = "", calendar_id: str = "", year: Optional[int] = None
    ) -> None:
        """
        Clear cached data. If no parameters are provided, clears all cache.

        Args:
            calendar_type: Optional calendar type to clear
            calendar_id: Optional calendar ID to clear
            year: Optional year to clear
        """
        if not any([calendar_type, calendar_id, year]):
            # Clear all cache
            for file in self._cache_dir.glob("*.json"):
                file.unlink()
            logger.info("Cleared all calendar cache")
            return

        pattern = ""
        if calendar_type:
            pattern += f"{calendar_type}_"
            if calendar_id:
                id_part = (
                    calendar_id.upper()
                    if calendar_type == "national"
                    else calendar_id.lower()
                )
                pattern += f"{id_part}_"
                if year:
                    pattern += f"{year}"

        if pattern:
            for file in self._cache_dir.glob(f"{pattern}*.json"):
                file.unlink()
            logger.info("Cleared cache matching pattern: %s", pattern)
