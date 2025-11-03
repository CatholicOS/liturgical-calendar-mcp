"""
litcal_cache.py - Simple in-memory cache for liturgical calendar metadata.
"""

import sys
import logging
from typing import Optional, Dict, Set, List, TypedDict
from datetime import datetime, timedelta
import httpx

# === CONFIGURATION ===
CACHE_EXPIRY_HOURS = 24
API_BASE_URL = "https://litcal.johnromanodorazio.com/api/dev"
DEFAULT_TIMEOUT = 30

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("litcal-cache")


class CalendarItem(TypedDict, total=False):
    """Metadata for a liturgical Calendar item, whether a national or a diocesan calendar."""
    calendar_id: str
    locales: List[str]


class CalendarMetadataCache:
    """Simple in-memory cache for calendar metadata."""

    _data: Optional[Dict] = None
    _timestamp: Optional[datetime] = None
    _national_calendars: Set[str] = set()
    _diocesan_calendars: Set[str] = set()
    _general_locales: Set[str] = set()
    _calendar_locales: Dict[str, Set[str]] = {}
    _api_base_url: str = API_BASE_URL
    _cache_expiry_hours: int = CACHE_EXPIRY_HOURS

    def __new__(cls):
        raise RuntimeError("Use CalendarMetadataCache.init(), no instantiation needed.")

    @classmethod
    async def init(
        cls,
        api_base_url: str = API_BASE_URL,
        cache_expiry_hours: int = CACHE_EXPIRY_HOURS,
    ) -> bool:
        """Ensure metadata cache is loaded and fresh."""
        # Only set/update if cache is not initialized OR if not expired
        if cls._data is None:
            if api_base_url != API_BASE_URL:
                logger.info("Setting custom API base URL: %s", api_base_url)
            cls._api_base_url = api_base_url

            if cache_expiry_hours != CACHE_EXPIRY_HOURS:
                logger.info("Setting custom cache expiry hours: %s", cache_expiry_hours)
            cls._cache_expiry_hours = cache_expiry_hours
        else:
            # Warn if attempting to change settings after initialization (ensure idempotency)
            if api_base_url != cls._api_base_url:
                logger.warning(
                    "Attempting to change API URL from %s to %s after cache initialization",
                    cls._api_base_url,
                    api_base_url,
                )
            if cache_expiry_hours != cls._cache_expiry_hours:
                logger.warning(
                    "Attempting to change cache expiry hours from %d to %d after cache initialization",
                    cls._cache_expiry_hours,
                    cache_expiry_hours,
                )

        if not cls.is_expired():
            return True

        logger.info("Cache expired or empty, fetching metadata...")
        try:
            url = f"{cls._api_base_url}/calendars"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                cls.set(data)
                return True
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error while requesting calendars metadata: %s", e)
            return False
        except httpx.RequestError as e:
            logger.error("Network error while requesting calendars metadata: %s", e)
            return False
        except ValueError as e:
            logger.error("Failed to parse metadata JSON: %s", e)
            return False

    @classmethod
    def is_expired(cls) -> bool:
        """Check if cache has expired."""
        if cls._timestamp is None:
            return True
        return datetime.now() - cls._timestamp > timedelta(
            hours=cls._cache_expiry_hours
        )

    @classmethod
    def set(cls, data: Dict) -> None:
        """Store metadata and extract useful information."""
        cls._data = data
        cls._timestamp = datetime.now()

        # Clear existing parsed data
        cls._national_calendars.clear()
        cls._diocesan_calendars.clear()
        cls._general_locales.clear()
        cls._calendar_locales.clear()

        metadata: Dict = data.get("litcal_metadata", {})
        item: CalendarItem

        # Parse national calendars
        for item in metadata.get("national_calendars", []):
            calendar_id = item.get("calendar_id", "").upper()
            if calendar_id:
                cls._national_calendars.add(calendar_id)
                locales = set(item.get("locales", []))
                cls._calendar_locales[f"national_{calendar_id}"] = locales

        # Parse diocesan calendars
        for item in metadata.get("diocesan_calendars", []):
            calendar_id = item.get("calendar_id", "").lower()
            if calendar_id:
                cls._diocesan_calendars.add(calendar_id)
                locales = set(item.get("locales", []))
                cls._calendar_locales[f"diocesan_{calendar_id}"] = locales

        # Parse general calendar locales
        cls._general_locales = set(metadata.get("locales", []))

        logger.info(
            "Cache updated: %d national, %d diocesan calendars, %d general locales",
            len(cls._national_calendars),
            len(cls._diocesan_calendars),
            len(cls._general_locales),
        )

    @classmethod
    async def get_data(cls) -> Optional[Dict]:
        """Get raw cached data."""
        if cls.is_expired():
            await cls.init()
        return cls._data

    @classmethod
    async def is_valid_national(cls, nation: str) -> bool:
        """Check if a nation code is valid."""
        if cls.is_expired():
            await cls.init()
        return nation.upper() in cls._national_calendars

    @classmethod
    async def is_valid_diocesan(cls, diocese: str) -> bool:
        """Check if a diocese ID is valid."""
        if cls.is_expired():
            await cls.init()
        return diocese.lower() in cls._diocesan_calendars

    @classmethod
    async def get_supported_locale(
        cls, calendar_type: str, calendar_id: str, requested_locale: str
    ) -> str:
        """
        Get the best matching locale for a calendar.
        Returns the requested locale if supported, otherwise falls back to 'en'.
        """
        if cls.is_expired():
            await cls.init()

        # Get available locales
        if calendar_type == "general":
            available_locales = cls._general_locales
        else:
            key = f"{calendar_type}_{calendar_id}"
            available_locales = cls._calendar_locales.get(key, set())

        # Check exact match
        if requested_locale in available_locales:
            return requested_locale

        # Check language prefix match (e.g., 'en-US' -> 'en', 'fr' -> 'fr_CA')
        lang_prefix = requested_locale.split("-")[0].split("_")[0]
        for locale in available_locales:
            if locale.startswith(lang_prefix):
                logger.info("Locale fallback: %s -> %s", requested_locale, locale)
                return locale

        # Fall back to English if available
        if "en" in available_locales:
            logger.warning(
                "Locale %s not supported, falling back to 'en'", requested_locale
            )
            return "en"

        # Return first available locale as last resort
        if available_locales:
            fallback = next(iter(available_locales))
            logger.warning(
                "Locale %s not supported, falling back to %s",
                requested_locale,
                fallback,
            )
            return fallback

        # No locales found, return requested
        return requested_locale

    @classmethod
    async def get_national_calendars(cls) -> List[str]:
        """Get list of valid national calendar codes."""
        if cls.is_expired():
            await cls.init()
        return sorted(cls._national_calendars)

    @classmethod
    async def get_diocesan_calendars(cls) -> List[str]:
        """Get list of valid diocesan calendar IDs."""
        if cls.is_expired():
            await cls.init()
        return sorted(cls._diocesan_calendars)
