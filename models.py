"""Model classes for the liturgical calendar MCP."""

from dataclasses import dataclass
from enums import CalendarType, YearType


@dataclass
class CalendarFetchRequest:
    """Container for parameters required to fetch calendar data.

    Grouping these into a small dataclass reduces the number of positional
    arguments and makes call sites clearer while keeping type hints.
    """

    calendar_type: CalendarType
    calendar_id: str
    year: int
    target_locale: str
    year_type: YearType


@dataclass(frozen=True)
class CalendarCacheKey:
    """
    Immutable key for identifying cached calendar data.

    Attributes:
        calendar_type: Type of calendar (`CalendarType.GENERAL_ROMAN`, `CalendarType.NATIONAL`, or `CalendarType.DIOCESAN`)
        calendar_id: Calendar identifier (nation code or diocese id, empty for general)
        year: Calendar year
        locale: Locale code for the calendar content (default: "en")
        year_type: Type of year (`YearType.LITURGICAL` or `YearType.CIVIL`, default: `YearType.LITURGICAL`)
    """

    calendar_type: CalendarType
    calendar_id: str
    year: int
    locale: str = "en"
    year_type: YearType = YearType.LITURGICAL

    def __post_init__(self):
        """Validate the calendar type and year type."""
        if self.calendar_type not in CalendarType:
            raise ValueError(
                f"Invalid calendar type: {self.calendar_type.value}. "
                f"Must be one of {', '.join(repr(ct.value) for ct in CalendarType)}"
            )

        if self.year_type not in YearType:
            raise ValueError(
                f"Invalid year type: {self.year_type.value}. "
                f"Must be one of {', '.join(repr(ct.value) for ct in YearType)}"
            )

    def to_cache_filename(self) -> str:
        """
        Build a unique cache filename for this key.

        Returns:
            A unique cache key string including all parameters
        """
        locale_part = self.locale.replace("-", "_")  # Normalize locale format
        year_type_part = self.year_type.value.lower()

        if self.calendar_type == CalendarType.GENERAL_ROMAN:
            return f"general_{self.year}_{year_type_part}_{locale_part}"
        if self.calendar_type == CalendarType.NATIONAL:
            return f"national_{self.calendar_id.upper()}_{self.year}_{year_type_part}_{locale_part}"
        # diocesan
        return f"diocesan_{self.calendar_id.lower()}_{self.year}_{year_type_part}_{locale_part}"
