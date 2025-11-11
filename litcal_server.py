#!/usr/bin/env python3
"""
Liturgical Calendar MCP Server - Provides access to Roman Catholic liturgical calendar data
"""

import sys
import logging
import httpx
from mcp.server.fastmcp import FastMCP
import pycountry
from litcal_metadata_cache import CalendarMetadataCache
from litcal_calendar_cache import CalendarDataCache
from enums import YearType, CalendarType
from formatters import (
    format_calendar_summary,
    format_liturgy_response,
    format_announcement_response,
)
from validators import (
    validate_year,
    validate_calendar_type,
    validate_target_date,
    validate_nation,
    validate_diocese,
    validate_calendar_id,
)
from utils import (
    filter_celebrations_by_date,
    fetch_calendar_data,
    mark_particular_celebrations,
)
from models import CalendarFetchRequest

# Create logger as a child of the main litcal logger
logger = logging.getLogger("litcal.server")

# Initialize MCP server
mcp = FastMCP(name="litcal")

# Initialize httpx client
http_client = httpx.AsyncClient(http2=True)

# Initialize caches
CalendarMetadataCache.set_http_client(http_client)
calendar_cache = CalendarDataCache()

# === MCP TOOLS ===


@mcp.tool()
async def get_general_calendar(year: int | None = None, locale: str = "en") -> str:
    """
    Retrieve the General Roman Calendar for a specific year with optional locale.

    Parameters:
    - year: Four-digit year (e.g., 2024). Defaults to current year if not provided.
    - locale: Locale code for translations (e.g., "en", "fr"). Defaults to "en".

    Example: locale='fr', year=2023
    """

    try:
        year_int = validate_year(year)
        locale = await CalendarMetadataCache.get_supported_locale(
            CalendarType.GENERAL_ROMAN, "", locale
        )
        logger.info(
            "Fetching General Calendar for year %d (locale %s)", year_int, locale
        )

        # Fetch calendar data using helper function
        request = CalendarFetchRequest(
            calendar_type=CalendarType.GENERAL_ROMAN,
            calendar_id="",
            year=year_int,
            target_locale=locale,
            year_type=YearType.LITURGICAL,
        )
        data = await fetch_calendar_data(request, calendar_cache, http_client)

        # Format and return response
        return format_calendar_summary(data)

    except ValueError as e:
        logger.exception("Error")
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(
                "General Roman Calendar with year %s and locale %s not found",
                year,
                locale,
            )
            return f"❌ General Roman Calendar with year {year} and locale {locale} not found"
        logger.exception(
            "HTTP error fetching General Roman Calendar for year %s and locale %s",
            year,
            locale,
        )
        return f"❌ HTTP error fetching General Roman Calendar for year {year} and locale {locale}: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.exception(
            "Network error fetching General Roman Calendar for year %s and locale %s",
            year,
            locale,
        )
        return f"❌ Network error fetching General Roman Calendar for year {year} and locale {locale}: {str(e)}"


@mcp.tool()
async def get_national_calendar(
    nation: str = "", year: int | None = None, locale: str = "en_US"
) -> str:
    """
    Retrieve the liturgical calendar for a specific nation and year, and optional locale.

    Parameters:
    - nation: Two-letter country code like 'CA' for Canada or 'US' for United States.
    - year: Four-digit year (e.g., 2024). Defaults to current year if not provided.
    - locale: Use format like 'fr_CA' for French-Canadian; infer the regional format from the nation parameter. Defaults to 'en_US'.

    Example: nation='CA', locale='fr_CA', year=2023
    """

    try:
        year_int = validate_year(year)
        nation_id = await validate_nation(nation)
        locale = await CalendarMetadataCache.get_supported_locale(
            CalendarType.NATIONAL, nation_id, locale
        )
        logger.info(
            "Fetching National Calendar for %s for year %d (locale %s)",
            nation_id,
            year_int,
            locale,
        )

        # Fetch national calendar data using helper function
        national_request = CalendarFetchRequest(
            calendar_type=CalendarType.NATIONAL,
            calendar_id=nation_id,
            year=year_int,
            target_locale=locale,
            year_type=YearType.LITURGICAL,
        )
        national_data = await fetch_calendar_data(
            national_request, calendar_cache, http_client
        )

        # Check if national calendar data was successfully fetched
        if national_data is None:
            return f"❌ Failed to fetch national calendar for {nation_id}"

        # Fetch general calendar for comparison to identify particular celebrations
        general_request = CalendarFetchRequest(
            calendar_type=CalendarType.GENERAL_ROMAN,
            calendar_id="",
            year=year_int,
            target_locale=locale,
            year_type=YearType.LITURGICAL,
        )
        general_data = await fetch_calendar_data(
            general_request, calendar_cache, http_client
        )

        # Check if general calendar data was successfully fetched
        if general_data is None:
            logger.warning(
                "Failed to fetch General Roman Calendar for comparison; "
                "particular celebrations will not be marked"
            )
            # Return national calendar without particular celebrations marked
            return format_calendar_summary(national_data)

        # Mark celebrations that are particular to this national calendar
        enriched_data = mark_particular_celebrations(national_data, general_data)

        # Format and return response
        return format_calendar_summary(enriched_data)

    except ValueError as e:
        logger.exception("Error")
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error("National calendar not found for nation: %s", nation)
            available = await CalendarMetadataCache.get_national_calendars()
            return f"❌ National calendar not found for: {nation}\n💡 Available nations: {', '.join(available)}"
        logger.exception("HTTP error fetching national calendar")
        return f"❌ HTTP error fetching national calendar: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.exception("Network error fetching national calendar")
        return f"❌ Network error fetching national calendar: {str(e)}"


@mcp.tool()
async def get_diocesan_calendar(
    diocese: str = "", year: int | None = None, locale: str = "en_US"
) -> str:
    """
    Retrieve the liturgical calendar for a specific diocese and year, and optional locale.

    Parameters:
    - diocese: Diocese ID like 'romamo_it' for Diocese of Rome.
    - year: Four-digit year (e.g., 2024). Defaults to current year if not provided.
    - locale: Use format like 'fr_CA' for French-Canadian; infer the regional format from the nation that the diocese belongs to. Defaults to 'en_US'.

    Example: diocese='romamo_it', locale='it_IT', year=2023
    """

    try:
        year_int = validate_year(year)
        diocese_id = await validate_diocese(diocese)
        locale = await CalendarMetadataCache.get_supported_locale(
            CalendarType.DIOCESAN, diocese_id, locale
        )
        logger.info(
            "Fetching Diocesan Calendar for %s for the year %s (locale %s)",
            diocese_id,
            year_int,
            locale,
        )

        # Fetch diocesan calendar data using helper function
        diocesan_request = CalendarFetchRequest(
            calendar_type=CalendarType.DIOCESAN,
            calendar_id=diocese_id,
            year=year_int,
            target_locale=locale,
            year_type=YearType.LITURGICAL,
        )
        diocesan_data = await fetch_calendar_data(
            diocesan_request, calendar_cache, http_client
        )

        # Check if diocesan calendar data was successfully fetched
        if diocesan_data is None:
            return f"❌ Failed to fetch diocesan calendar for {diocese_id}"

        # Fetch general calendar for comparison to identify particular celebrations
        general_request = CalendarFetchRequest(
            calendar_type=CalendarType.GENERAL_ROMAN,
            calendar_id="",
            year=year_int,
            target_locale=locale,
            year_type=YearType.LITURGICAL,
        )
        general_data = await fetch_calendar_data(
            general_request, calendar_cache, http_client
        )

        # Check if general calendar data was successfully fetched
        if general_data is None:
            logger.warning(
                "Failed to fetch General Roman Calendar for comparison; "
                "particular celebrations will not be marked"
            )
            # Return diocesan calendar without particular celebrations marked
            return format_calendar_summary(diocesan_data)

        # Mark celebrations that are particular to this diocesan calendar
        enriched_data = mark_particular_celebrations(diocesan_data, general_data)

        # Format and return response
        return format_calendar_summary(enriched_data)

    except ValueError as e:
        logger.exception("Error")
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error("Diocesan calendar not found for diocese: %s", diocese)
            available = await CalendarMetadataCache.get_diocesan_calendars()
            return f"❌ Diocesan calendar not found for: {diocese}\n💡 Available diocese ids: {', '.join(available)}"
        logger.exception("HTTP error fetching diocesan calendar")
        return f"❌ HTTP error fetching diocesan calendar: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.exception("Network error fetching diocesan calendar")
        return f"❌ Network error fetching diocesan calendar: {str(e)}"


@mcp.tool()
async def list_available_calendars() -> str:
    """
    List all available national and diocesan calendars with their locales and settings.
    """
    logger.info("Fetching available calendars metadata")

    try:
        # Ensure cache is loaded
        data = await CalendarMetadataCache.get_data()
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
        logger.exception("Error accessing calendar metadata")
        return f"❌ Error accessing calendar data: {str(e)}"
    except (ValueError, LookupError) as e:
        logger.exception("Error processing calendar data")
        return f"❌ Error processing calendar data: {str(e)}"


@mcp.tool()
async def get_liturgy_of_the_day(
    date: str = "",
    calendar_type: str = CalendarType.GENERAL_ROMAN.value,
    calendar_id: str = "",
    locale: str = "en",
) -> str:
    """
    Retrieve the liturgical celebrations for a specific date from any calendar.

    Parameters:
    - date: Date in YYYY-MM-DD format (e.g., "2024-03-15"). Defaults to today if not provided.
    - calendar_type: Type of calendar - "GENERAL_ROMAN", "NATIONAL", or "DIOCESAN". Defaults to "GENERAL_ROMAN".
    - calendar_id: Calendar identifier (nation code like 'US' or diocese id like 'romamo_it').
                   Required for national/diocesan calendars, ignored for general calendar.
    - locale: Locale code for translations (e.g., "en", "fr_CA"). Must have a regional identifier for national or diocesan calendars. Defaults to "en".

    Examples:
    - Today's liturgy in the general roman calendar: date='', calendar_type='GENERAL_ROMAN'
    - Liturgy for a specific date in US: date='2024-12-25', calendar_type='NATIONAL', calendar_id='US', locale='en_US'
    - Liturgy for a specific date in Rome diocese: date='2024-06-29', calendar_type='DIOCESAN', calendar_id='romamo_it', locale='it_IT'
    - Today's liturgy in the calendar for Canada in French: date='', calendar_type='NATIONAL', calendar_id='CA', locale='fr_CA'

    Important: When presenting the readings to the user, do not summarize them. Output them in a readable format,
    maintaining the original structure and the title for each reading. If there is a pipe character (|),
    it should be interpreted as an alternative reading.
    """

    try:
        # Validate and normalize inputs
        calendar_type_case = validate_calendar_type(calendar_type)
        target_date = validate_target_date(date)
        calendar_id = await validate_calendar_id(calendar_type_case, calendar_id)
        locale = await CalendarMetadataCache.get_supported_locale(
            calendar_type_case, calendar_id, locale
        )
        logger.info(
            "Fetching liturgy of the day for date %s, calendar_type %s, calendar_id %s, locale %s",
            target_date,
            calendar_type_case.value,
            calendar_id,
            locale,
        )

        # Fetch calendar data using helper function
        request = CalendarFetchRequest(
            calendar_type=calendar_type_case,
            calendar_id=calendar_id,
            year=target_date.year,
            target_locale=locale,
            year_type=YearType.CIVIL,
        )
        data = await fetch_calendar_data(request, calendar_cache, http_client)

        # Filter celebrations for target date
        celebrations = filter_celebrations_by_date(data, target_date)

        if not celebrations:
            formatted_date = target_date.strftime("%B %d, %Y")
            return f"❌ No liturgical celebrations found for {formatted_date}"

        # Format and return response
        return format_liturgy_response(
            celebrations, target_date, data.get("settings", {})
        )

    except ValueError as e:
        logger.exception("Error")
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(
                "Calendar not found for type %s, id %s, year %s",
                calendar_type_case.value,
                calendar_id,
                target_date.year,
            )
            return f"❌ Calendar not found for {calendar_type_case.value} calendar"
        logger.exception("HTTP error fetching liturgy")
        return f"❌ HTTP error: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.exception("Network error fetching liturgy")
        return f"❌ Network error: {str(e)}"


@mcp.tool()
async def get_announcement_easter_and_moveable_feasts(
    calendar_type: str = CalendarType.GENERAL_ROMAN.value,
    calendar_id: str = "",
    locale: str = "en",
    year: int | None = None,
) -> str:
    """
    Produce the Epiphany announcement (Noveritis) for the dates of Easter and other moveable feasts for a specific year from any calendar.
    The response MUST be output exactly as returned, without reformatting, paraphrasing, summarization, or additional commentary.
    Preserve all markdown formatting, punctuation, and line breaks exactly as in the response, including any links.

    Parameters:
    - calendar_type: Type of calendar - "GENERAL_ROMAN", "NATIONAL", or "DIOCESAN". Defaults to "GENERAL_ROMAN".
    - calendar_id: Calendar identifier (nation code like 'US' or diocese id like 'romamo_it').
                   Required for national/diocesan calendars, ignored for general calendar.
    - locale: Locale code for translations (e.g., "en", "fr_CA"). Must have a regional identifier for national or diocesan calendars. Defaults to "en".
    - year: Four-digit year (e.g., 2024). Defaults to current year if not provided.
    """

    try:
        # Validate and normalize inputs
        year_int = validate_year(year)
        calendar_type_case = validate_calendar_type(calendar_type)
        calendar_id = await validate_calendar_id(calendar_type_case, calendar_id)
        locale = await CalendarMetadataCache.get_supported_locale(
            calendar_type_case, calendar_id, locale
        )
        logger.info(
            "Fetching Easter and moveable feasts for calendar type %s, calendar_id %s, locale %s, year %d",
            calendar_type_case.value,
            calendar_id,
            locale,
            year_int,
        )

        # Fetch calendar data using helper function
        request = CalendarFetchRequest(
            calendar_type=calendar_type_case,
            calendar_id=calendar_id,
            year=year_int,
            target_locale=locale,
            year_type=YearType.CIVIL,
        )
        data = await fetch_calendar_data(request, calendar_cache, http_client)

        # Format and return response
        return format_announcement_response(data, year_int)

    except ValueError as e:
        logger.exception("Error")
        return f"❌ Error: {str(e)}"
    except httpx.HTTPStatusError as e:
        logger.exception("HTTP error fetching moveable feasts")
        return f"❌ HTTP error fetching moveable feasts: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logger.exception("Network error fetching moveable feasts")
        return f"❌ Network error fetching moveable feasts: {str(e)}"


# === MAIN ENTRY POINT ===


if __name__ == "__main__":
    # Configure logging to stderr only when run as a script
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    logger.info("Starting Liturgical Calendar MCP server...")

    try:
        mcp.run(transport="stdio")
    except (KeyboardInterrupt, SystemExit):
        logger.exception("Server interrupted")
        sys.exit(1)
    except RuntimeError:
        logger.exception("Runtime error")
        sys.exit(1)
