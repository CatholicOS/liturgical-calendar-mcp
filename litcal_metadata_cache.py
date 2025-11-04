"""
litcal_metadata_cache.py - Simple in-memory cache for liturgical calendar metadata.
"""

import logging
from typing import ClassVar, Optional, Dict, Set, List, TypedDict
from datetime import datetime, timedelta
import httpx
from enums import CalendarType

# === CONFIGURATION ===
CACHE_EXPIRY_HOURS = 24
API_BASE_URL = "https://litcal.johnromanodorazio.com/api/dev"
DEFAULT_TIMEOUT = 30

# Create logger as a child of the main litcal logger
logger = logging.getLogger("litcal.metadata")


class CalendarItem(TypedDict, total=False):
    """Metadata for a liturgical Calendar item, whether a national or a diocesan calendar."""

    calendar_id: str
    locales: List[str]


class CalendarMetadataCache:
    """Simple in-memory cache for calendar metadata."""

    _http_client: ClassVar[Optional[httpx.AsyncClient]] = None
    _data: ClassVar[Optional[Dict]] = None
    _timestamp: ClassVar[Optional[datetime]] = None
    _national_calendars: ClassVar[Set[str]] = set()
    _diocesan_calendars: ClassVar[Set[str]] = set()
    _general_locales: ClassVar[Set[str]] = set()
    _calendar_locales: ClassVar[Dict[str, Set[str]]] = {}
    _api_base_url: ClassVar[str] = API_BASE_URL
    _cache_expiry_hours: ClassVar[int] = CACHE_EXPIRY_HOURS

    def __new__(cls):
        raise RuntimeError(
            "Use CalendarMetadataCache.init() async class method (await it); this class uses only class methods and should not be instantiated."
        )

    @classmethod
    async def init(
        cls,
        http_client: httpx.AsyncClient | None = None,
        api_base_url: str = API_BASE_URL,
        cache_expiry_hours: int = CACHE_EXPIRY_HOURS,
    ) -> bool:
        """
        Ensure metadata cache is loaded and fresh.
        Args:
            http_client: Optional httpx.AsyncClient instance to use for requests
            api_base_url: URL to use for API requests
            cache_expiry_hours: Number of hours until cache expiry
        """
        cls._initialize_http_client(http_client)
        cls._configure_settings(api_base_url, cache_expiry_hours)

        if not cls.is_expired():
            return True

        return await cls._fetch_metadata()

    @classmethod
    def set_http_client(cls, http_client: httpx.AsyncClient | None) -> None:
        """
        Synchronously set or inject an httpx.AsyncClient to be used by the
        metadata cache. This allows callers to provide a shared client at
        module import time without awaiting the async `init` method.

        Note: If the cache has already initialized an http client, attempting
        to change it will log a warning and will not replace the existing
        client.
        """
        cls._initialize_http_client(http_client)

    @classmethod
    def _initialize_http_client(cls, http_client: httpx.AsyncClient | None) -> None:
        """Initialize or validate the HTTP client."""
        if cls._http_client is None:
            if http_client is None:
                logger.info("Instantiating http client seeing that none was provided")
                http_client = httpx.AsyncClient(http2=True)
            cls._http_client = http_client
        elif http_client is not None:
            logger.warning("Attempting to change http client after initialization")

    @classmethod
    def _configure_settings(cls, api_base_url: str, cache_expiry_hours: int) -> None:
        """Configure or validate API settings."""
        if cls._data is None:
            cls._set_initial_settings(api_base_url, cache_expiry_hours)
        else:
            cls._validate_settings(api_base_url, cache_expiry_hours)

    @classmethod
    def _set_initial_settings(cls, api_base_url: str, cache_expiry_hours: int) -> None:
        """Set initial configuration values."""
        if api_base_url != API_BASE_URL:
            logger.info("Setting custom API base URL: %s", api_base_url)
        cls._api_base_url = api_base_url

        if cache_expiry_hours != CACHE_EXPIRY_HOURS:
            logger.info("Setting custom cache expiry hours: %s", cache_expiry_hours)
        cls._cache_expiry_hours = cache_expiry_hours

    @classmethod
    def _validate_settings(cls, api_base_url: str, cache_expiry_hours: int) -> None:
        """Warn if settings are being changed after initialization."""
        if api_base_url != cls._api_base_url:
            logger.warning(
                "Attempting to change API URL from %s to %s after initialization",
                cls._api_base_url,
                api_base_url,
            )
        if cache_expiry_hours != cls._cache_expiry_hours:
            logger.warning(
                "Attempting to change cache expiry hours from %d to %d after initialization",
                cls._cache_expiry_hours,
                cache_expiry_hours,
            )

    @classmethod
    async def _fetch_metadata(cls) -> bool:
        """Fetch and cache metadata from the API."""
        logger.info("Cache expired or empty, fetching metadata...")
        try:
            url = f"{cls._api_base_url}/calendars"
            response = await cls._http_client.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            cls.update(data)
            return True
        except httpx.HTTPStatusError:
            logger.exception("HTTP error while requesting calendars metadata")
            return False
        except httpx.RequestError:
            logger.exception("Network error while requesting calendars metadata")
            return False
        except ValueError:
            logger.exception("Failed to parse metadata JSON")
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
    def update(cls, data: Dict) -> None:
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
        cls, calendar_type: CalendarType, calendar_id: str, requested_locale: str
    ) -> str:
        """
        Get the best matching locale for a calendar.
        Returns the requested locale if supported, otherwise falls back to 'en'.
        """
        if cls.is_expired():
            await cls.init()

        # Get available locales
        if calendar_type == CalendarType.GENERAL_ROMAN:
            available_locales = cls._general_locales
        else:
            key = f"{calendar_type.value}_{calendar_id}"
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
