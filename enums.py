"""
enums.py - Contains enums used across the liturgical calendar MCP.
"""

from enum import Enum


class YearType(Enum):
    """Represents the `year_type` parameter for the Liturgical Calendar API."""

    LITURGICAL = "LITURGICAL"
    CIVIL = "CIVIL"


class CalendarType(Enum):
    """Represents the types of calendars that can be requested from the Liturgical Calendar API."""

    GENERAL_ROMAN = "general"
    NATIONAL = "national"
    DIOCESAN = "diocesan"
