"""
litcal_cache.py - Simple in-memory cache for liturgical calendar metadata.
"""

import sys
import logging
from typing import Optional, Dict, Set, List
from datetime import datetime, timedelta

# === CONFIGURATION ===
CACHE_EXPIRY_HOURS = 24

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("litcal-cache")

# === CACHE STORAGE ===


class CalendarMetadataCache:
    """Simple in-memory cache for calendar metadata."""

    def __init__(self):
        self._data: Optional[Dict] = None
        self._timestamp: Optional[datetime] = None
        self._national_calendars: Set[str] = set()
        self._diocesan_calendars: Set[str] = set()
        self._general_locales: Set[str] = set()
        self._calendar_locales: Dict[str, Set[str]] = {}

    def is_expired(self) -> bool:
        """Check if cache has expired."""
        if self._timestamp is None:
            return True
        return datetime.now() - self._timestamp > timedelta(hours=CACHE_EXPIRY_HOURS)

    def set(self, data: Dict) -> None:
        """Store metadata and extract useful information."""
        self._data = data
        self._timestamp = datetime.now()

        # Clear existing parsed data
        self._national_calendars.clear()
        self._diocesan_calendars.clear()
        self._general_locales.clear()
        self._calendar_locales.clear()

        metadata = data.get("litcal_metadata", {})

        # Parse national calendars
        for item in metadata.get("national_calendars", []):
            calendar_id = item.get("calendar_id", "").upper()
            if calendar_id:
                self._national_calendars.add(calendar_id)
                locales = set(item.get("locales", []))
                self._calendar_locales[f"national_{calendar_id}"] = locales

        # Parse diocesan calendars
        for item in metadata.get("diocesan_calendars", []):
            calendar_id = item.get("calendar_id", "").lower()
            if calendar_id:
                self._diocesan_calendars.add(calendar_id)
                locales = set(item.get("locales", []))
                self._calendar_locales[f"diocesan_{calendar_id}"] = locales

        # Parse general calendar locales
        self._general_locales = set(metadata.get("locales", []))

        logger.info(
            "Cache updated: %d national, %d diocesan calendars, %d general locales",
            len(self._national_calendars),
            len(self._diocesan_calendars),
            len(self._general_locales),
        )

    def get_data(self) -> Optional[Dict]:
        """Get raw cached data."""
        return self._data

    def is_valid_national(self, nation: str) -> bool:
        """Check if a nation code is valid."""
        return nation.upper() in self._national_calendars

    def is_valid_diocesan(self, diocese: str) -> bool:
        """Check if a diocese ID is valid."""
        return diocese.lower() in self._diocesan_calendars

    def get_supported_locale(
        self, calendar_type: str, calendar_id: str, requested_locale: str
    ) -> str:
        """
        Get the best matching locale for a calendar.
        Returns the requested locale if supported, otherwise falls back to 'en'.
        """
        if calendar_type == "general":
            available_locales = self._general_locales
        else:
            key = f"{calendar_type}_{calendar_id}"
            available_locales = self._calendar_locales.get(key, set())

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

    def get_national_calendars(self) -> List[str]:
        """Get list of valid national calendar codes."""
        return sorted(self._national_calendars)

    def get_diocesan_calendars(self) -> List[str]:
        """Get list of valid diocesan calendar IDs."""
        return sorted(self._diocesan_calendars)
