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

    if not year.strip():
        year = str(datetime.now().year)

    try:
        year_int = int(year)
        if year_int < 1970 or year_int > 9999:
            return "❌ Error: Year must be between 1970 and 9999"
    except ValueError:
        return f"❌ Error: Invalid year value: {year}"

    url = f"{API_BASE_URL}/calendar/{year}"

    headers = {
        "Accept": "application/json",
        "Accept-Language": locale if locale.strip() else "en",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ General Roman Calendar for {year}:\n\n{format_calendar_summary(data)}"
        except httpx.HTTPStatusError as e:
            return f"❌ API Error: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            logger.error("Network error fetching calendar: %s", e)
            return f"❌ Network error: {str(e)}"
        except ValueError as e:
            logger.error("JSON decoding error: %s", e)
            return f"❌ Error decoding response: {str(e)}"


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

    if not nation.strip():
        return "❌ Error: Nation code is required (e.g., IT, US, NL, VA, CA)"

    nation = nation.strip().upper()

    if not year.strip():
        year = str(datetime.now().year)

    try:
        year_int = int(year)
        if year_int < 1970 or year_int > 9999:
            return "❌ Error: Year must be between 1970 and 9999"
    except ValueError:
        return f"❌ Error: Invalid year value: {year}"

    url = f"{API_BASE_URL}/calendar/nation/{nation}/{year}"

    headers = {
        "Accept": "application/json",
        "Accept-Language": locale if locale.strip() else "en",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ National Calendar for {nation} ({year}):\n\n{format_calendar_summary(data)}"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"❌ National calendar not found for: {nation}\n💡 Available nations: IT, US, NL, VA, CA"
            return f"❌ API Error: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            logger.error("Network error fetching national calendar: %s", e)
            return f"❌ Network error: {str(e)}"
        except ValueError as e:
            logger.error("JSON decoding error: %s", e)
            return f"❌ Error decoding response: {str(e)}"


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

    if not diocese.strip():
        return "❌ Error: Diocese ID is required (e.g., romamo_it, boston_us)"

    diocese = diocese.strip().lower()

    if not year.strip():
        year = str(datetime.now().year)

    try:
        year_int = int(year)
        if year_int < 1970 or year_int > 9999:
            return "❌ Error: Year must be between 1970 and 9999"
    except ValueError:
        return f"❌ Error: Invalid year value: {year}"

    url = f"{API_BASE_URL}/calendar/diocese/{diocese}/{year}"

    headers = {
        "Accept": "application/json",
        "Accept-Language": locale if locale.strip() else "en",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return f"✅ Diocesan Calendar for {diocese} ({year}):\n\n{format_calendar_summary(data)}"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"❌ Diocesan calendar not found for: {diocese}\n💡 Use list_available_calendars to see available dioceses"
            logger.error("HTTP error fetching diocesan calendar: %s", e)
            return f"❌ API Error: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            logger.error("Network error fetching diocesan calendar: %s", e)
            return f"❌ Network error: {str(e)}"
        except ValueError as e:
            logger.error("JSON decoding error: %s", e)
            return f"❌ Error decoding response: {str(e)}"


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
                        lines.append(f"    Nation: {nation}")
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


# @mcp.tool()
# async def get_liturgical_events(calendar_type: str = "general", calendar_id: str = "", locale: str = "en") -> str:
#     """Retrieve all possible liturgical events for a calendar (general, national, or diocesan)."""
#     logger.info("Fetching liturgical events for %s calendar", calendar_type)

#     calendar_type = calendar_type.strip().lower()

#     if calendar_type == "general":
#         url = f"{API_BASE_URL}/events"
#     elif calendar_type == "nation":
#         if not calendar_id.strip():
#             return "❌ Error: Nation code is required for national calendar (e.g., IT, US, NL, VA, CA)"
#         url = f"{API_BASE_URL}/events/nation/{calendar_id.strip().upper()}"
#     elif calendar_type == "diocese":
#         if not calendar_id.strip():
#             return "❌ Error: Diocese ID is required for diocesan calendar (e.g., rome_it, boston_us)"
#         url = f"{API_BASE_URL}/events/diocese/{calendar_id.strip().lower()}"
#     else:
#         return "❌ Error: calendar_type must be 'general', 'nation', or 'diocese'"

#     headers = {
#         "Accept": "application/json",
#         "Accept-Language": locale if locale.strip() else "en"
#     }

#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
#             response.raise_for_status()
#             data = response.json()

#             if 'litcal_events' not in data:
#                 return "❌ No events data in response"

#             events = data['litcal_events']

#             lines = []
#             lines.append("=" * 60)
#             lines.append(f"📖 LITURGICAL EVENTS ({calendar_type.upper()})")
#             lines.append("=" * 60)
#             lines.append("")

#             sorted_events = sorted(events.items(), key=lambda x: (x[1].get('month', 0), x[1].get('day', 0)))

#             for event_key, event_data in sorted_events[:100]:
#                 month = event_data.get('month', 0)
#                 day = event_data.get('day', 0)
#                 name = event_data.get('name', 'Unknown')
#                 grade_map = {
#                     0: "Weekday",
#                     1: "Commemoration",
#                     2: "Optional Memorial",
#                     3: "Memorial",
#                     4: "Feast",
#                     5: "Feast of the Lord",
#                     6: "Solemnity",
#                     7: "Higher Solemnity"
#                 }
#                 grade = grade_map.get(event_data.get('grade', 0), "Unknown")

#                 lines.append(f"📅 {name}")
#                 lines.append(f"   Key: {event_key}")
#                 lines.append(f"   Date: {month}/{day}")
#                 lines.append(f"   Grade: {grade}")
#                 lines.append("")

#             if len(events) > 100:
#                 lines.append(f"... and {len(events) - 100} more events")

#             lines.append("=" * 60)
#             lines.append(f"Total events: {len(events)}")

#             return "✅ " + "\n".join(lines)
#         except httpx.HTTPStatusError as e:
#             return f"❌ API Error: {e.response.status_code} - {e.response.text}"
#         except httpx.RequestError as e:
#             logger.error("Network error fetching events: %s", e)
#             return f"❌ Network error: {str(e)}"

# === SERVER STARTUP ===

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
