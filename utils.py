"""
Utility functions for the MCP tools.
"""

import locale
from datetime import datetime, timezone

from settings import (
    API_BASE_URL,
    DEFAULT_TIMEOUT,
    FESTIVE_CYCLE,
    FERIAL_CYCLE,
    NOVERITIS_DIR,
)


def build_calendar_url(calendar_type: str, calendar_id: str, year: int) -> str:
    """Build the appropriate API URL based on calendar type."""
    if calendar_type == "general":
        return f"{API_BASE_URL}/calendar/{year}"

    if calendar_type == "national":
        return f"{API_BASE_URL}/calendar/nation/{calendar_id}/{year}"

    # Diocesan calendar
    return f"{API_BASE_URL}/calendar/diocese/{calendar_id}/{year}"


def filter_celebrations_by_date(data: dict, target_date: datetime) -> list:
    """Filter liturgical celebrations for a specific date."""
    if "litcal" not in data:
        return None

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
