#!/usr/bin/env python3
"""
Simple Liturgical Calendar MCP Server - Provides access to Roman Catholic liturgical calendar data
"""

import sys
import logging
from datetime import datetime
import httpx
from mcp.server.fastmcp import FastMCP
import pycountry

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
    """Retrieve the General Roman Calendar for a specific year with optional locale."""
    logger.info(
        "Fetching General Roman Calendar for year %s and locale %s", year, locale
    )

    try:
        # Validate and normalize inputs
        year_int = _validate_year(year)

        # Make API request
        url = f"{API_BASE_URL}/calendar/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": locale if locale.strip() else "en",
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
    nation: str = "", year: str = "", locale: str = "en"
) -> str:
    """Retrieve the liturgical calendar for a specific nation and year, and optional locale."""
    logger.info(
        "Fetching National Calendar for %s for the year %s (locale %s)",
        nation,
        year,
        locale,
    )

    try:
        # Validate and normalize inputs
        nation = _validate_nation(nation)
        year_int = _validate_year(year)

        # Make API request
        url = f"{API_BASE_URL}/calendar/nation/{nation}/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": locale if locale.strip() else "en",
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
            return f"❌ National calendar not found for: {nation}\n💡 Available nations: IT, US, NL, VA, CA"
        logger.error("HTTP error fetching national calendar: %s", e)
        return f"❌ HTTP error fetching national calendar: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error("Network error fetching national calendar: %s", e)
        return f"❌ Network error fetching national calendar: {str(e)}"


@mcp.tool()
async def get_diocesan_calendar(
    diocese: str = "", year: str = "", locale: str = "en"
) -> str:
    """Retrieve the liturgical calendar for a specific diocese and year, and optional locale."""
    logger.info(
        "Fetching Diocesan Calendar for %s for the year %s (locale %s)",
        diocese,
        year,
        locale,
    )

    try:
        # Validate and normalize inputs
        diocese = _validate_diocese(diocese)
        year_int = _validate_year(year)

        # Make API request
        url = f"{API_BASE_URL}/calendar/diocese/{diocese}/{year_int}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": locale if locale.strip() else "en",
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
            return f"❌ Diocesan calendar not found for: {diocese}\n💡 Available diocese ids: romamo_it, boston_us, charlo_ca"
        logger.error("HTTP error fetching diocesan calendar: %s", e)
        return f"❌ HTTP error fetching diocesan calendar: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.error("Network error fetching diocesan calendar: %s", e)
        return f"❌ Network error fetching diocesan calendar: {str(e)}"


@mcp.tool()
async def list_available_calendars() -> str:
    """List all available national and diocesan calendars with their locales and settings."""
    logger.info("Fetching available calendars metadata")

    url = f"{API_BASE_URL}/calendars"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()

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
        except httpx.HTTPStatusError as e:
            return f"❌ API Error: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            logger.error("Network error fetching metadata: %s", e)
            return f"❌ Network error: {str(e)}"
        except ValueError as e:
            logger.error("JSON decoding error: %s", e)
            return f"❌ Error decoding response: {str(e)}"


def _validate_nation(nation: str) -> str:
    """Validate and normalize nation code."""
    if not nation.strip():
        raise ValueError("Nation code is required (e.g., IT, US, NL, VA, CA)")
    return nation.strip().upper()


def _validate_diocese(diocese: str) -> str:
    """Validate and normalize diocese ID."""
    if not diocese.strip():
        raise ValueError("Diocese ID is required (e.g., romamo_it, boston_us)")
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
