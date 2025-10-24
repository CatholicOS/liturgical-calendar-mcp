#!/usr/bin/env python3
"""
Liturgical Calendar MCP Server - Provides access to Roman Catholic liturgical calendar data
"""

import sys
import logging
from datetime import datetime, timezone
import httpx
from mcp.server.fastmcp import FastMCP
import pycountry
from litcal_cache import CalendarMetadataCache

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("litcal-server")

# Initialize MCP server
mcp = FastMCP("litcal")

# Configuration
API_BASE_URL = "https://litcal.johnromanodorazio.com/api/dev"
DEFAULT_TIMEOUT = 30

# Initialize cache
metadata_cache = CalendarMetadataCache()

# === CACHE MANAGEMENT ===


async def ensure_cache_loaded() -> bool:
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


# === UTILITY FUNCTIONS ===


def format_event(event_data):
    """Format a single liturgical event for display."""
    name = event_data.get("name", "Unknown")
    date = event_data.get("date", "Unknown")
    color = ", ".join(event_data.get("color_lcl", []))
    grade = event_data.get("grade_lcl", "Unknown")

    return f"📅 {name}\n   Date: {date}\n   Grade: {grade}\n   Color: {color}"


def format_calendar_summary(data):
    """Format calendar data into a readable summary."""
    if not data or "litcal" not in data:
        return "No calendar data available"

    liturgical_events = data["litcal"]
    settings = data.get("settings", {})

    lines = []
    lines.append("=" * 60)
    lines.append("📖 LITURGICAL CALENDAR")
    lines.append("=" * 60)

    if settings:
        lines.append(f"Locale: {settings.get('locale', 'N/A')}")
        if settings.get("national_calendar"):
            lines.append(f"National Calendar: {settings['national_calendar']}")
        if settings.get("diocesan_calendar"):
            lines.append(f"Diocesan Calendar: {settings['diocesan_calendar']}")
        lines.append("")

    for event_data in liturgical_events[:50]:
        lines.append(format_event(event_data))
        lines.append("")

    if len(liturgical_events) > 50:
        lines.append(f"... and {len(liturgical_events) - 50} more events")

    lines.append("=" * 60)
    lines.append(f"Total events: {len(liturgical_events)}")

    return "\n".join(lines)


# === MCP TOOLS ===


@mcp.tool()
async def get_general_calendar(year: str = "", locale: str = "en") -> str:
    """
    Retrieve the General Roman Calendar for a specific year with optional locale.

    Parameters:
    - year: Four-digit year (e.g., "2024"). Defaults to current year if not provided.
    - locale: Locale code for translations (e.g., "en", "fr"). Defaults to "en".

    Example: locale='fr', year='2023'
    """
    logger.info(
        "Fetching General Roman Calendar for year %s and locale %s", year, locale
    )

    try:
        # Ensure cache is loaded
        await ensure_cache_loaded()

        # Validate and normalize inputs
        year_int = _validate_year(year)

        # Get best matching locale
        locale = metadata_cache.get_supported_locale("general", "", locale)

        # Make API request
        url = f"{API_BASE_URL}/calendar/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ General Roman Calendar for {year}:\n\n{format_calendar_summary(data)}"
    except ValueError as e:
        logger.error("Error: %s", e)
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(
                "General Roman Calendar with year %s and locale %s not found",
                year,
                locale,
            )
            return f"❌ General Roman Calendar with year {year} and locale {locale} not found"
        logger.error(
            "HTTP error fetching General Roman Calendar for year %s and locale %s: %s",
            year,
            locale,
            e,
        )
        return f"❌ HTTP error fetching General Roman Calendar for year {year} and locale {locale}: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error(
            "Network error fetching General Roman Calendar for year %s and locale %s: %s",
            year,
            locale,
            e,
        )
        return f"❌ Network error fetching General Roman Calendar for year {year} and locale {locale}: {str(e)}"


@mcp.tool()
async def get_national_calendar(
    nation: str = "", year: str = "", locale: str = "en_US"
) -> str:
    """
    Retrieve the liturgical calendar for a specific nation and year, and optional locale.

    Parameters:
    - nation: Two-letter country code like 'CA' for Canada or 'US' for United States.
    - year: Four-digit year (e.g., "2024"). Defaults to current year if not provided.
    - locale: Use format like 'fr_CA' for French-Canadian; infer the regional format from the nation parameter. Defaults to 'en_US'.

    Example: nation='CA', locale='fr_CA', year='2023'
    """
    logger.info(
        "Fetching National Calendar for %s for the year %s (locale %s)",
        nation,
        year,
        locale,
    )

    try:
        # Ensure cache is loaded
        await ensure_cache_loaded()

        # Validate and normalize inputs
        nation = _validate_nation(nation)
        year_int = _validate_year(year)
        locale = metadata_cache.get_supported_locale("national", nation, locale)

        # Make API request
        url = f"{API_BASE_URL}/calendar/nation/{nation}/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ National Calendar for {nation} ({year}):\n\n{format_calendar_summary(data)}"
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
    diocese: str = "", year: str = "", locale: str = "en_US"
) -> str:
    """
    Retrieve the liturgical calendar for a specific diocese and year, and optional locale.

    Parameters:
    - diocese: Diocese ID like 'romamo_it' for Diocese of Rome.
    - year: Four-digit year (e.g., "2024"). Defaults to current year if not provided.
    - locale: Use format like 'fr_CA' for French-Canadian; infer the regional format from the nation that the diocese belongs to. Defaults to 'en_US'.

    Example: diocese='romamo_it', locale='it_IT', year='2023'
    """
    logger.info(
        "Fetching Diocesan Calendar for %s for the year %s (locale %s)",
        diocese,
        year,
        locale,
    )

    try:
        # Ensure cache is loaded
        await ensure_cache_loaded()

        # Validate and normalize inputs
        diocese = _validate_diocese(diocese)
        year_int = _validate_year(year)
        locale = metadata_cache.get_supported_locale("diocesan", diocese, locale)

        # Make API request
        url = f"{API_BASE_URL}/calendar/diocese/{diocese}/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ Diocesan Calendar for {diocese} ({year}):\n\n{format_calendar_summary(data)}"
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
        await ensure_cache_loaded()

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
    locale: str = "en"
) -> str:
    """
    Retrieve the liturgical celebrations for a specific date from any calendar.

    Parameters:
    - date: Date in YYYY-MM-DD format (e.g., "2024-03-15"). Defaults to today if not provided.
    - calendar_type: Type of calendar - "general", "national", or "diocesan". Defaults to "general".
    - calendar_id: Calendar identifier (nation code like 'US' or diocese id like 'romamo_it').
                   Required for national/diocesan calendars, ignored for general calendar.
    - locale: Locale code for translations (e.g., "en", "fr_CA"). Must have a regional identifier for national or diocesan calendars. Defaults to "en".

    Examples:
    - Today's liturgy in the general roman calendar: date='', calendar_type='general'
    - Liturgy for a specific date in US: date='2024-12-25', calendar_type='national', calendar_id='US', locale='en_US'
    - Liturgy for a specific date in Rome diocese: date='2024-06-29', calendar_type='diocesan', calendar_id='romamo_it', locale='it_IT'
    - Today's liturgy in the calendar for Canada in French: date='', calendar_type='national', calendar_id='CA', locale='fr_CA'
    """
    logger.info(
        "Fetching liturgy of the day for date %s, calendar_type %s, calendar_id %s, locale %s",
        date, calendar_type, calendar_id, locale
    )

    try:
        # Ensure cache is loaded
        await ensure_cache_loaded()

        # Validate and normalize inputs
        calendar_type = _validate_calendar_type(calendar_type)
        target_date = _validate_target_date(date)
        year = target_date.year

        # Build API URL based on calendar type
        if calendar_type == "general":
            url = f"{API_BASE_URL}/calendar/{year}"
            locale = metadata_cache.get_supported_locale("general", "", locale)
        elif calendar_type == "national":
            calendar_id = _validate_nation(calendar_id)
            url = f"{API_BASE_URL}/calendar/nation/{calendar_id}/{year}"
            locale = metadata_cache.get_supported_locale("national", calendar_id, locale)
        else:  # diocesan
            calendar_id = _validate_diocese(calendar_id)
            url = f"{API_BASE_URL}/calendar/diocese/{calendar_id}/{year}"
            locale = metadata_cache.get_supported_locale("diocesan", calendar_id, locale)

        # Make API request
        headers = {
            "Accept": "application/json",
            "Accept-Language": locale,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Filter for the specific date
            if "litcal" not in data:
                return "❌ No liturgical calendar data found in response"

            # Convert target date to Unix timestamp (matching the API format)
            target_timestamp = int(target_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc).timestamp())

            # Filter celebrations for the target date
            celebrations = [
                event for event in data["litcal"]
                if event.get("date") == target_timestamp
            ]

            if not celebrations:
                formatted_date = target_date.strftime("%B %d, %Y")
                return f"❌ No liturgical celebrations found for {formatted_date}"

            # Format the results
            formatted_date = target_date.strftime("%A, %B %d, %Y")
            lines = []
            lines.append("=" * 60)
            lines.append(f"📖 LITURGY OF THE DAY - {formatted_date}")
            lines.append("=" * 60)

            settings = data.get("settings", {})
            if settings:
                lines.append(f"Locale: {settings.get('locale', 'N/A')}")
                if settings.get("national_calendar"):
                    lines.append(f"National Calendar: {settings['national_calendar']}")
                if settings.get("diocesan_calendar"):
                    lines.append(f"Diocesan Calendar: {settings['diocesan_calendar']}")
                lines.append("")

            for celebration in celebrations:
                lines.append(format_event(celebration))
                if celebration.get("common"):
                    common_text = ", ".join(celebration.get("common_lcl", celebration.get("common", [])))
                    lines.append(f"   Common: {common_text}")
                if celebration.get("liturgical_year"):
                    lines.append(f"   Liturgical Year: {celebration['liturgical_year']}")
                lines.append("")

            lines.append("=" * 60)

            return "✅ " + "\n".join(lines)

    except ValueError as e:
        logger.error("Error: %s", e)
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching liturgy: %s", e)
        return f"❌ HTTP error: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error("Network error fetching liturgy: %s", e)
        return f"❌ Network error: {str(e)}"


def _validate_calendar_type(calendar_type: str) -> str:
    """Validate calendar type."""
    valid_types = ["general", "national", "diocesan"]
    if calendar_type.strip().lower() not in valid_types:
        raise ValueError(f"Invalid calendar type: {calendar_type}. Must be one of {', '.join(valid_types)}")
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
