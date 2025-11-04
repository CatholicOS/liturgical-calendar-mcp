"""
Utility functions for the MCP tools.
"""

import locale
import logging
from datetime import datetime, timezone
from pathlib import Path
from httpx import AsyncClient
from enums import CalendarType
from litcal_calendar_cache import CalendarDataCache
from models import CalendarFetchRequest, CalendarCacheKey


FESTIVE_CYCLE = ["A", "B", "C"]
FERIAL_CYCLE = ["I", "II"]

# === CONFIGURATION ===
NOVERITIS_DIR = Path(__file__).parent / "noveritis"
API_BASE_URL = "https://litcal.johnromanodorazio.com/api/dev"
DEFAULT_TIMEOUT = 30

# Create logger as a child of the main litcal logger
logger = logging.getLogger("litcal.utils")


def build_calendar_url(calendar_type: CalendarType, calendar_id: str, year: int) -> str:
    """Build the appropriate API URL based on calendar type."""
    if calendar_type == CalendarType.GENERAL_ROMAN:
        return f"{API_BASE_URL}/calendar/{year}"

    if calendar_type == CalendarType.NATIONAL:
        return f"{API_BASE_URL}/calendar/nation/{calendar_id}/{year}"

    # Diocesan calendar
    return f"{API_BASE_URL}/calendar/diocese/{calendar_id}/{year}"


def filter_celebrations_by_date(data: dict, target_date: datetime) -> list:
    """Filter celebrations by target date."""
    # Format target date to RFC 3339 timestamp at midnight UTC
    target_date_str = target_date.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    ).isoformat()

    return [event for event in data["litcal"] if event.get("date") == target_date_str]


def get_base_locale(locale_str: str) -> str:
    """Extract base language code from locale string."""
    return (
        locale.normalize(locale_str).split(".")[0].split("_")[0].split("-")[0].lower()
    )


def load_announcement_template(base_locale: str) -> str:
    """Load the Noveritis announcement template for a given base locale."""
    path = NOVERITIS_DIR / f"{base_locale}.txt"
    if not path.exists():
        path = NOVERITIS_DIR / "en.txt"
    if not path.exists():
        raise ValueError(f"No translation found for locale '{base_locale}'")
    return path.read_text(encoding="utf-8")


def get_event(events: list, key: str) -> dict | None:
    """Return the first event matching the key, or None."""
    return next((e for e in events if e.get("event_key") == key), None)


def calculate_year_cycles(year: int) -> dict:
    """
    Calculate festive and ferial liturgical year cycle,
    respectively for weekdays, and for Sundays / Solemnities / Feasts of the Lord,
    for a given year.
    """
    # Festive year cycle (A, B, C)
    festive_cycle_index = (year - 1) % 3
    festive_year_cycle = FESTIVE_CYCLE[festive_cycle_index]

    # Ferial year cycle (I, II)
    ferial_cycle_index = (year - 1) % 2
    ferial_year_cycle = FERIAL_CYCLE[ferial_cycle_index]

    return {
        "festive_year_cycle": festive_year_cycle,
        "ferial_year_cycle": ferial_year_cycle,
    }


async def fetch_calendar_data(
    request: CalendarFetchRequest,
    calendar_cache: CalendarDataCache,
    http_client: AsyncClient,
) -> dict:
    """
    Fetch calendar data either from cache or from API.

    Args:
        request: `CalendarFetchRequest` containing parameters to fetch calendar data
        calendar_cache: Instance of `CalendarDataCache`
        http_client: Instance of `httpx.AsyncClient`

    Returns:
        dict: Calendar data either from cache or freshly fetched from API

    Raises:
        httpx.HTTPStatusError: On HTTP errors from the API
        httpx.RequestError: On network errors
    """
    # Try to get from cache first (calendar_cache is required - dependency injected)
    cache_key = CalendarCacheKey(
        request.calendar_type,
        request.calendar_id,
        request.year,
        request.target_locale,
        request.year_type,
    )
    cached_data = await calendar_cache.async_get(cache_key)
    if cached_data is not None:
        logger.info(
            "Fetched calendar data from cache %s", cache_key.to_cache_filename()
        )
        return cached_data

    # Make API request if not in cache
    url = build_calendar_url(request.calendar_type, request.calendar_id, request.year)
    headers = {
        "Accept": "application/json",
        "Accept-Language": request.target_locale,
    }

    response = await http_client.get(
        url,
        params={"year_type": request.year_type.value},
        headers=headers,
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    logger.info("Fetched calendar data from API at URL %s", url)

    # Cache the response (off the event loop)
    await calendar_cache.async_update(cache_key, data)

    return data
