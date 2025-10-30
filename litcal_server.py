#!/usr/bin/env python3
"""
Liturgical Calendar MCP Server - Provides access to Roman Catholic liturgical calendar data
"""
import calendar
import json
import locale
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import inflect
import httpx
from mcp.server.fastmcp import FastMCP
import pycountry
from litcal_cache import CalendarMetadataCache

# resolve incompatibility between inflect and typeguard under Python 3.12
os.environ["TYPEGUARD_DISABLE"] = "1"

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("litcal-server")

SERVER_SYSTEM_PROMPT = """
You are an MCP tool execution engine.
When a tool is invoked and returns a string, you MUST output that string to the user EXACTLY as returned,
without modification, paraphrasing, wrapping, or commentary.
Do not interpret or summarize tool output.
If the tool output includes formatting, punctuation, or line breaks, preserve them exactly.
"""

# Initialize MCP server
mcp = FastMCP("litcal")

# Configuration
API_BASE_URL = "https://litcal.johnromanodorazio.com/api/dev"
DEFAULT_TIMEOUT = 30

# Initialize cache
metadata_cache = CalendarMetadataCache()

NOVERITIS_DIR = Path(__file__).parent / "noveritis"

# === CACHE MANAGEMENT ===


async def _ensure_cache_loaded() -> bool:
    """Ensure metadata cache is loaded and fresh."""
    if not metadata_cache.is_expired():
        return True

    logger.info("Cache expired or empty, fetching metadata...")
    try:
        url = f"{API_BASE_URL}/calendars"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            metadata_cache.set(data)
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


# === MCP TOOLS ===


@mcp.tool()
async def get_general_calendar(year: str = "", target_locale: str = "en") -> str:
    """
    Retrieve the General Roman Calendar for a specific year with optional locale.

    Parameters:
    - year: Four-digit year (e.g., "2024"). Defaults to current year if not provided.
    - target_locale: Locale code for translations (e.g., "en", "fr"). Defaults to "en".

    Example: target_locale='fr', year='2023'
    """
    logger.info(
        "Fetching General Roman Calendar for year %s and locale %s", year, target_locale
    )

    try:
        # Ensure cache is loaded
        await _ensure_cache_loaded()

        # Validate and normalize inputs
        year_int = _validate_year(year)

        # Get best matching locale
        target_locale = metadata_cache.get_supported_locale(
            "general", "", target_locale
        )

        # Make API request
        url = f"{API_BASE_URL}/calendar/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": target_locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ General Roman Calendar for {year}:\n\n{_format_calendar_summary(data)}"
    except ValueError as e:
        logger.error("Error: %s", e)
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(
                "General Roman Calendar with year %s and locale %s not found",
                year,
                target_locale,
            )
            return f"❌ General Roman Calendar with year {year} and locale {target_locale} not found"
        logger.error(
            "HTTP error fetching General Roman Calendar for year %s and locale %s: %s",
            year,
            target_locale,
            e,
        )
        return f"❌ HTTP error fetching General Roman Calendar for year {year} and locale {target_locale}: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error(
            "Network error fetching General Roman Calendar for year %s and locale %s: %s",
            year,
            target_locale,
            e,
        )
        return f"❌ Network error fetching General Roman Calendar for year {year} and locale {target_locale}: {str(e)}"


@mcp.tool()
async def get_national_calendar(
    nation: str = "", year: str = "", target_locale: str = "en_US"
) -> str:
    """
    Retrieve the liturgical calendar for a specific nation and year, and optional locale.

    Parameters:
    - nation: Two-letter country code like 'CA' for Canada or 'US' for United States.
    - year: Four-digit year (e.g., "2024"). Defaults to current year if not provided.
    - target_locale: Use format like 'fr_CA' for French-Canadian; infer the regional format from the nation parameter. Defaults to 'en_US'.

    Example: nation='CA', target_locale='fr_CA', year='2023'
    """
    logger.info(
        "Fetching National Calendar for %s for the year %s (locale %s)",
        nation,
        year,
        target_locale,
    )

    try:
        # Ensure cache is loaded
        await _ensure_cache_loaded()

        # Validate and normalize inputs
        nation = _validate_nation(nation)
        year_int = _validate_year(year)
        target_locale = metadata_cache.get_supported_locale(
            "national", nation, target_locale
        )

        # Make API request
        url = f"{API_BASE_URL}/calendar/nation/{nation}/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": target_locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ National Calendar for {nation} ({year}):\n\n{_format_calendar_summary(data)}"
    except ValueError as e:
        logger.error("Error: %s", e)
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error("National calendar not found for nation: %s", nation)
            available = metadata_cache.get_national_calendars()
            return f"❌ National calendar not found for: {nation}\n💡 Available nations: {', '.join(available)}"
        logger.error("HTTP error fetching national calendar: %s", e)
        return f"❌ HTTP error fetching national calendar: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error("Network error fetching national calendar: %s", e)
        return f"❌ Network error fetching national calendar: {str(e)}"


@mcp.tool()
async def get_diocesan_calendar(
    diocese: str = "", year: str = "", target_locale: str = "en_US"
) -> str:
    """
    Retrieve the liturgical calendar for a specific diocese and year, and optional locale.

    Parameters:
    - diocese: Diocese ID like 'romamo_it' for Diocese of Rome.
    - year: Four-digit year (e.g., "2024"). Defaults to current year if not provided.
    - target_locale: Use format like 'fr_CA' for French-Canadian; infer the regional format from the nation that the diocese belongs to. Defaults to 'en_US'.

    Example: diocese='romamo_it', target_locale='it_IT', year='2023'
    """
    logger.info(
        "Fetching Diocesan Calendar for %s for the year %s (locale %s)",
        diocese,
        year,
        target_locale,
    )

    try:
        # Ensure cache is loaded
        await _ensure_cache_loaded()

        # Validate and normalize inputs
        diocese = _validate_diocese(diocese)
        year_int = _validate_year(year)
        target_locale = metadata_cache.get_supported_locale(
            "diocesan", diocese, target_locale
        )

        # Make API request
        url = f"{API_BASE_URL}/calendar/diocese/{diocese}/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": target_locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ Diocesan Calendar for {diocese} ({year}):\n\n{_format_calendar_summary(data)}"
    except ValueError as e:
        logger.error("Error: %s", e)
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error("Diocesan calendar not found for diocese: %s", diocese)
            available = metadata_cache.get_diocesan_calendars()
            return f"❌ Diocesan calendar not found for: {diocese}\n💡 Available diocese ids: {', '.join(available)}"
        logger.error("HTTP error fetching diocesan calendar: %s", e)
        return f"❌ HTTP error fetching diocesan calendar: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error("Network error fetching diocesan calendar: %s", e)
        return f"❌ Network error fetching diocesan calendar: {str(e)}"


@mcp.tool()
async def list_available_calendars() -> str:
    """
    List all available national and diocesan calendars with their locales and settings.
    """
    logger.info("Fetching available calendars metadata")

    try:
        # Ensure cache is loaded
        await _ensure_cache_loaded()

        data = metadata_cache.get_data()
        if not data:
            return "❌ Unable to retrieve calendar metadata"

        lines = []
        lines.append("=" * 60)
        lines.append("📚 AVAILABLE LITURGICAL CALENDARS")
        lines.append("=" * 60)
        lines.append("")

        if "litcal_metadata" in data:
            metadata = data["litcal_metadata"]

            if "national_calendars" in metadata:
                lines.append("🌍 NATIONAL CALENDARS:")
                lines.append("")
                for item in metadata.get("national_calendars", []):
                    calendar_id = item.get("calendar_id", "Unknown")
                    lines.append(
                        f"  • {calendar_id}: {pycountry.countries.get(alpha_2=calendar_id).name}"
                    )
                    if "locales" in item:
                        lines.append(f"    Locales: {', '.join(item['locales'])}")
                lines.append("")

            if "diocesan_calendars" in metadata:
                lines.append("⛪ DIOCESAN CALENDARS:")
                lines.append("")
                for item in metadata.get("diocesan_calendars", []):
                    calendar_id = item.get("calendar_id", "Unknown")
                    diocese_name = item.get("diocese", "Unknown")
                    lines.append(f"  • {calendar_id}: {diocese_name}")
                    nation_id = item.get("nation", "Unknown")
                    nation = pycountry.countries.get(alpha_2=nation_id).name
                    lines.append(f"    Nation: {nation_id} ({nation})")
                    if "locales" in item:
                        lines.append(f"    Locales: {', '.join(item['locales'])}")
                lines.append("")

            if "locales" in metadata:
                lines.append("🌐 AVAILABLE LOCALES for the General Roman Calendar:")
                lines.append(f"  {', '.join(metadata['locales'])}")
                lines.append("")

        lines.append("=" * 60)

        return "✅ " + "\n".join(lines)
    except (KeyError, AttributeError) as e:
        logger.error("Error accessing calendar metadata: %s", e)
        return f"❌ Error accessing calendar data: {str(e)}"
    except (ValueError, LookupError) as e:
        logger.error("Error processing calendar data: %s", e)
        return f"❌ Error processing calendar data: {str(e)}"


@mcp.tool()
async def get_liturgy_of_the_day(
    date: str = "",
    calendar_type: str = "general",
    calendar_id: str = "",
    target_locale: str = "en",
) -> str:
    """
    Retrieve the liturgical celebrations for a specific date from any calendar.

    Parameters:
    - date: Date in YYYY-MM-DD format (e.g., "2024-03-15"). Defaults to today if not provided.
    - calendar_type: Type of calendar - "general", "national", or "diocesan". Defaults to "general".
    - calendar_id: Calendar identifier (nation code like 'US' or diocese id like 'romamo_it').
                   Required for national/diocesan calendars, ignored for general calendar.
    - target_locale: Locale code for translations (e.g., "en", "fr_CA"). Must have a regional identifier for national or diocesan calendars. Defaults to "en".

    Examples:
    - Today's liturgy in the general roman calendar: date='', calendar_type='general'
    - Liturgy for a specific date in US: date='2024-12-25', calendar_type='national', calendar_id='US', target_locale='en_US'
    - Liturgy for a specific date in Rome diocese: date='2024-06-29', calendar_type='diocesan', calendar_id='romamo_it', target_locale='it_IT'
    - Today's liturgy in the calendar for Canada in French: date='', calendar_type='national', calendar_id='CA', target_locale='fr_CA'
    """
    logger.info(
        "Fetching liturgy of the day for date %s, calendar_type %s, calendar_id %s, locale %s",
        date,
        calendar_type,
        calendar_id,
        target_locale,
    )

    try:
        # Ensure cache is loaded
        await _ensure_cache_loaded()

        # Validate and normalize inputs
        calendar_type = _validate_calendar_type(calendar_type)
        target_date = _validate_target_date(date)

        # Validate calendar ID if needed
        if calendar_type == "national":
            calendar_id = _validate_nation(calendar_id)
        elif calendar_type == "diocesan":
            calendar_id = _validate_diocese(calendar_id)

        # Build URL and get locale
        url = _build_calendar_url(calendar_type, calendar_id, target_date.year)
        target_locale = metadata_cache.get_supported_locale(
            calendar_type, calendar_id, target_locale
        )

        # Make API request
        headers = {
            "Accept": "application/json",
            "Accept-Language": target_locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params={"year_type": "CIVIL"},
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            # Filter celebrations for target date
            celebrations = _filter_celebrations_by_date(data, target_date)

            if celebrations is None:
                return "❌ No liturgical calendar data found in response"

            if not celebrations:
                formatted_date = target_date.strftime("%B %d, %Y")
                return f"❌ No liturgical celebrations found for {formatted_date}"

            # Format and return response
            return _format_liturgy_response(
                celebrations, target_date, data.get("settings", {})
            )

    except ValueError as e:
        logger.error("Error: %s", e)
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching liturgy: %s", e)
        return f"❌ HTTP error: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error("Network error fetching liturgy: %s", e)
        return f"❌ Network error: {str(e)}"


@mcp.tool()
async def get_announcement_easter_and_moveable_feasts(
    calendar_type: str = "general",
    calendar_id: str = "",
    target_locale: str = "en",
    year: str = "",
) -> str:
    """
    Produce the Epiphany announcement (Noveritis) for the dates of Easter and other moveable feasts for a specific year from any calendar.
    The response MUST be output exactly as returned, without reformatting, paraphrasing, summarization, or additional commentary.
    Preserve all markdown formatting, punctuation, and line breaks exactly as in the response, including any links.

    Parameters:
    - calendar_type: Type of calendar - "general", "national", or "diocesan". Defaults to "general".
    - calendar_id: Calendar identifier (nation code like 'US' or diocese id like 'romamo_it').
                   Required for national/diocesan calendars, ignored for general calendar.
    - target_locale: Locale code for translations (e.g., "en", "fr_CA"). Must have a regional identifier for national or diocesan calendars. Defaults to "en".
    - year: Four-digit year (e.g., "2024"). Defaults to current year if not provided.
    """
    logger.info("Fetching Easter and moveable feasts for year %s", year)

    try:
        # Ensure cache is loaded
        await _ensure_cache_loaded()

        # Validate and normalize inputs
        year_int = _validate_year(year)
        calendar_type = _validate_calendar_type(calendar_type)

        # Validate calendar ID if needed
        if calendar_type == "national":
            calendar_id = _validate_nation(calendar_id)
        elif calendar_type == "diocesan":
            calendar_id = _validate_diocese(calendar_id)

        # Build URL and get locale
        url = _build_calendar_url(calendar_type, calendar_id, year_int)
        target_locale = metadata_cache.get_supported_locale(
            calendar_type, calendar_id, target_locale
        )

        # Make API request
        headers = {
            "Accept": "application/json",
            "Accept-Language": target_locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params={"year_type": "CIVIL"},
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            # Format and return response
            return _format_announcement_response(data, year_int)

    except ValueError as e:
        logger.error("Error: %s", e)
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching moveable feasts: %s", e)
        return f"❌ HTTP error fetching moveable feasts: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error("Network error fetching moveable feasts: %s", e)
        return f"❌ Network error fetching moveable feasts: {str(e)}"


# === INPUT VALIDATION HELPERS ===


def _validate_calendar_type(calendar_type: str) -> str:
    """Validate calendar type."""
    valid_types = ["general", "national", "diocesan"]
    if calendar_type.strip().lower() not in valid_types:
        raise ValueError(
            f"Invalid calendar type: {calendar_type}. Must be one of {', '.join(valid_types)}"
        )
    return calendar_type.strip().lower()


def _validate_target_date(date_str: str) -> datetime:
    """Validate and parse target date."""
    if not date_str.strip():
        return datetime.now()

    try:
        target_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return target_date
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD") from e


def _validate_nation(nation: str) -> str:
    """Validate and normalize nation code."""
    if not nation.strip():
        raise ValueError("Nation code is required")

    # Validate nation against cache
    if not metadata_cache.is_valid_national(nation):
        available = metadata_cache.get_national_calendars()
        return f"❌ National calendar not found for: {nation}\n💡 Available nations: {', '.join(available)}"

    return nation.strip().upper()


def _validate_diocese(diocese: str) -> str:
    """Validate and normalize diocese ID."""
    if not diocese.strip():
        raise ValueError("Diocese ID is required")

    # Validate diocese against cache
    if not metadata_cache.is_valid_diocesan(diocese):
        available = metadata_cache.get_diocesan_calendars()
        return f"❌ Diocesan calendar not found for: {diocese}\n💡 Available dioceses: {', '.join(available)}"

    return diocese.strip().lower()


def _validate_year(year: str) -> int:
    """Validate and normalize year value."""
    if not year.strip():
        return datetime.now().year

    try:
        year_int = int(year)
        if year_int < 1970 or year_int > 9999:
            raise ValueError("Year must be between 1970 and 9999")
        return year_int
    except ValueError as e:
        if "invalid literal" in str(e).lower():
            raise ValueError(f"Invalid year value: {year}") from e
        raise


# === UTILITY FUNCTIONS ===


def _format_event(event_data: dict) -> str:
    """Format a single liturgical event for display."""
    name = event_data.get("name", "Unknown")
    date = event_data.get("date", "Unknown")
    color = ", ".join(event_data.get("color_lcl", []))
    grade = event_data.get("grade_lcl", "Unknown")

    return f"📅 {name}\n   Date: {date}\n   Grade: {grade}\n   Color: {color}"


def _format_header() -> list:
    """Format calendar header for display."""
    return ["=" * 60, "📖 LITURGICAL CALENDAR", "=" * 60]


def _format_settings(settings: dict) -> list:
    """Format calendar settings for display."""
    lines = []
    if settings:
        lines.append(f"Locale: {settings.get('locale', 'N/A')}")
        for key, label in [
            ("national_calendar", "National Calendar"),
            ("diocesan_calendar", "Diocesan Calendar"),
        ]:
            if settings.get(key):
                lines.append(f"{label}: {settings[key]}")
        lines.append("=" * 60)
    return lines


def _format_holy_days(events: list) -> list:
    """Format Holy Days of Obligation for display."""
    lines = ["Holy Days of Obligation:"]
    holy_days = [
        e
        for e in events
        if e.get("holy_day_of_obligation", False) and not e.get("is_vigil_mass", False)
    ]
    for event in holy_days:
        lines.append(_format_event(event))
        lines.append("")
    lines.append("=" * 60)
    return lines


def _format_liturgical_seasons(events: list) -> list:
    """Format key liturgical season events for display."""
    season_events = [
        ("Advent1", "Start of the Advent season:"),
        ("Christmas", "Start of the Christmas season:"),
        ("Epiphany", None),
        ("BaptismOfTheLord", "End of the Christmas season and start of Ordinary Time:"),
        ("AshWednesday", "Start of the Lent season:"),
        ("HolyThursday", "Start of the Easter Triduum:"),
        ("Easter", "Start of the Easter season:"),
        ("Pentecost", "End of the Easter season and start of Ordinary Time:"),
        ("ChristKing", "Last Sunday of Ordinary Time:"),
        ("OrdWeekday34Saturday", "Last day of the liturgical year:"),
    ]

    lines = ["Start and end of liturgical seasons:"]
    for key, label in season_events:
        event = next((e for e in events if e.get("event_key") == key), None)
        if event:
            if label:
                lines.append(label)
            lines.append(_format_event(event))
            lines.append("")
    lines.append("=" * 60)
    return lines


def _format_particular_celebrations(events: list) -> list:
    """Format celebrations particular to the current calendar, for display."""
    particular_events = [e for e in events if re.match(r'^\[.*\]', e.get("name", "")) and not e.get("is_vigil_mass", False)]
    if particular_events:
        lines = ["Celebrations particular to this calendar:"]
        for event in particular_events:
            lines.append(_format_event(event))
            lines.append("")
        lines.append("=" * 60)
        return lines
    return []


def _format_calendar_summary(data: dict) -> str:
    """Format calendar data into a readable summary."""
    if not data or "litcal" not in data:
        return "No calendar data available"

    liturgical_events = data["litcal"]
    settings = data.get("settings", {})

    lines = []
    lines.extend(_format_header())
    lines.extend(_format_settings(settings))
    lines.extend(_format_holy_days(liturgical_events))
    lines.extend(_format_liturgical_seasons(liturgical_events))
    lines.extend(_format_particular_celebrations(liturgical_events))
    lines.append("=" * 60)
    lines.append(f"Total events: {len(liturgical_events)}")

    return "\n".join(lines)


def _build_calendar_url(calendar_type: str, calendar_id: str, year: int) -> str:
    """Build the appropriate API URL based on calendar type."""
    if calendar_type == "general":
        return f"{API_BASE_URL}/calendar/{year}"

    if calendar_type == "national":
        return f"{API_BASE_URL}/calendar/nation/{calendar_id}/{year}"

    # Diocesan calendar
    return f"{API_BASE_URL}/calendar/diocese/{calendar_id}/{year}"


def _filter_celebrations_by_date(data: dict, target_date: datetime) -> list:
    """Filter liturgical celebrations for a specific date."""
    if "litcal" not in data:
        return None

    # Format target date to RFC 3339 timestamp at midnight UTC
    target_date_str = target_date.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    ).isoformat()

    return [event for event in data["litcal"] if event.get("date") == target_date_str]


def _format_liturgy_response(
    celebrations: list, target_date: datetime, settings: dict
) -> str:
    """Format the liturgy of the day response."""
    formatted_date = target_date.strftime("%A, %B %d, %Y")
    lines = [
        "=" * 60,
        f"📖 LITURGY OF THE DAY - {formatted_date}",
        "=" * 60,
    ]

    if settings:
        lines.append(f"Locale: {settings.get('locale', 'N/A')}")
        if settings.get("national_calendar"):
            lines.append(f"National Calendar: {settings['national_calendar']}")
        if settings.get("diocesan_calendar"):
            lines.append(f"Diocesan Calendar: {settings['diocesan_calendar']}")
        lines.append("")

    for celebration in celebrations:
        lines.append(_format_event(celebration))
        if celebration.get("common"):
            lines.append(f"   Common: {celebration.get('common_lcl')}")
        if celebration.get("liturgical_year"):
            lines.append(f"   Liturgical Year: {celebration['liturgical_year']}")
        if celebration.get("readings"):
            lines.append(f"   Readings: {json.dumps(celebration['readings'])}")
        lines.append("")

    lines.append("=" * 60)
    return "✅ " + "\n".join(lines)


def _format_announcement_response(data: dict, year: int) -> str:
    """Format the announcement response."""
    settings = data.get("settings", {})
    celebrations = data.get("litcal", [])
    if not celebrations:
        return "❌ No liturgical calendar data found in response"

    p = inflect.engine()
    base_locale = _get_base_locale(settings.get("locale", "en"))

    logging.info("Formatting announcement in locale: %s", base_locale)

    # Set locale (try multiple candidates)
    candidates = [
        f"{base_locale}_{base_locale.upper()}.UTF-8",  # Unix
        f"{locale.windows_locale.get(base_locale, '')}",  # Windows
    ]
    for loc in candidates:
        try:
            locale.setlocale(locale.LC_ALL, loc)
            break
        except locale.Error:
            continue

    # Extract events
    keys = [
        "AshWednesday",
        "Easter",
        "Ascension",
        "Pentecost",
        "CorpusChristi",
        "Advent1",
    ]
    events = {key: _get_event(celebrations, key) for key in keys}

    if any(v is None for v in events.values()):
        return "❌ No liturgical calendar data found in response"

    # Format day/month for all events
    formatted = {
        key: _format_day_month(evt, base_locale, p) for key, evt in events.items()
    }

    lines = [
        f"# Epiphany announcement of Easter and Moveable Feasts for the year {year}",
    ]

    announcement_template_lcl = _load_announcement_template(base_locale)
    lines.append(
        announcement_template_lcl.format(
            ash_wednesday_day=formatted["AshWednesday"][0],
            ash_wednesday_month=formatted["AshWednesday"][1],
            easter_day=formatted["Easter"][0],
            easter_month=formatted["Easter"][1],
            ascension_day=formatted["Ascension"][0],
            ascension_month=formatted["Ascension"][1],
            pentecost_day=formatted["Pentecost"][0],
            pentecost_month=formatted["Pentecost"][1],
            corpus_christi_day=formatted["CorpusChristi"][0],
            corpus_christi_month=formatted["CorpusChristi"][1],
            first_sunday_of_advent_day=formatted["Advent1"][0],
            first_sunday_of_advent_month=formatted["Advent1"][1],
        )
    )

    if settings:
        lines.append("")
        lines.append(f"*Locale: {settings.get('locale', 'N/A')}*  ")
        if settings.get("national_calendar"):
            lines.append(f"*National Calendar: {settings['national_calendar']}*  ")
        if settings.get("diocesan_calendar"):
            lines.append(f"*Diocesan Calendar: {settings['diocesan_calendar']}*  ")

    return "\n".join(lines)


def _get_base_locale(locale_str: str) -> str:
    """Extract base language code from locale string."""
    return (
        locale.normalize(locale_str).split(".")[0].split("_")[0].split("-")[0].lower()
    )


def _format_day_month(
    event: dict, locale_code: str, p: inflect.engine
) -> tuple[str, str]:
    """Return formatted day and month based on locale."""
    day = event.get("day")
    month = event.get("month")
    month_long = event.get("month_long")

    if locale_code in ["fr", "it", "de", "pt"]:
        return str(day), month_long
    if locale_code in ["es", "en"]:
        return p.number_to_words(p.ordinal(day)), month_long
    # fallback: English words with calendar.month_name
    return p.number_to_words(p.ordinal(day)), calendar.month_name[month]


def _load_announcement_template(base_locale: str) -> str:
    """Load the Noveritis announcement template for a given base locale."""
    path = NOVERITIS_DIR / f"{base_locale}.txt"
    if not path.exists():
        path = NOVERITIS_DIR / "en.txt"
    if not path.exists():
        raise ValueError(f"No translation found for locale '{base_locale}'")
    return path.read_text(encoding="utf-8")


def _get_event(events: list, key: str) -> dict | None:
    """Return the first event matching the key, or None."""
    return next((e for e in events if e.get("event_key") == key), None)


# === MAIN ENTRY POINT ===


if __name__ == "__main__":
    logger.info("Starting Liturgical Calendar MCP server...")

    try:
        mcp.run(transport="stdio")
    except (KeyboardInterrupt, SystemExit) as e:
        logger.error("Server interrupted: %s", e, exc_info=True)
        sys.exit(1)
    except RuntimeError as e:
        logger.error("Runtime error: %s", e, exc_info=True)
        sys.exit(1)
