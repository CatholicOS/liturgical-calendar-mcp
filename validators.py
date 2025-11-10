"""
validators.py

This module contains a collection of functions for validating input data.

The functions are:

- `validate_calendar_type(calendar_type: str) -> str`: Validate calendar type
- `validate_target_date(date_str: str) -> datetime`: Validate and parse target date
- `validate_nation(nation: str) -> str`: Validate and normalize nation code
- `validate_diocese(diocese: str) -> str`: Validate and normalize diocese ID
- `validate_year(year: int | None) -> int`: Validate and normalize year value
"""

from datetime import datetime
from litcal_metadata_cache import CalendarMetadataCache
from enums import CalendarType
from constants import MIN_YEAR, MAX_YEAR, DATE_FORMAT


def validate_calendar_type(calendar_type: str) -> CalendarType:
    """Validate calendar type."""
    calendar_type_normalized = calendar_type.strip().upper()
    if calendar_type_normalized not in (ct.value for ct in CalendarType):
        raise ValueError(
            f"Invalid calendar type: {calendar_type_normalized}. Must be one of {', '.join(repr(ct.value) for ct in CalendarType)}"
        )
    return CalendarType(calendar_type_normalized)


def validate_target_date(date_str: str) -> datetime:
    """Validate and parse target date."""
    if not date_str.strip():
        return datetime.now()

    try:
        target_date = datetime.strptime(date_str.strip(), DATE_FORMAT)
        return target_date
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD") from e


async def validate_nation(nation: str) -> str:
    """Validate and normalize nation code."""
    normalized = nation.strip()
    if not normalized:
        raise ValueError("Nation code is required")

    # Validate nation against cache
    normalized_upper = normalized.upper()
    if not await CalendarMetadataCache.is_valid_national(normalized_upper):
        available = await CalendarMetadataCache.get_national_calendars()
        raise ValueError(
            f"❌ National calendar not found for: {normalized_upper}\n"
            f"💡 Available nations: {', '.join(available)}"
        )

    return normalized_upper


async def validate_diocese(diocese: str) -> str:
    """Validate and normalize diocese ID."""
    normalized = diocese.strip()
    if not normalized:
        raise ValueError("Diocese ID is required")

    # Validate diocese against cache
    normalized_lower = normalized.lower()
    if not await CalendarMetadataCache.is_valid_diocesan(normalized_lower):
        available = await CalendarMetadataCache.get_diocesan_calendars()
        raise ValueError(
            f"❌ Diocesan calendar not found for: {normalized_lower}\n"
            f"💡 Available dioceses: {', '.join(available)}"
        )

    return normalized_lower


async def validate_calendar_id(calendar_type: CalendarType, calendar_id: str) -> str:
    """Validate calendar ID based on calendar type."""
    if calendar_type == CalendarType.NATIONAL:
        return await validate_nation(calendar_id)
    if calendar_type == CalendarType.DIOCESAN:
        return await validate_diocese(calendar_id)
    return calendar_id


def validate_year(year: int | None) -> int:
    """Validate and normalize year value."""
    if year is None:
        return datetime.now().year

    if year < MIN_YEAR or year > MAX_YEAR:
        raise ValueError(f"Year must be between {MIN_YEAR} and {MAX_YEAR}")

    return year
