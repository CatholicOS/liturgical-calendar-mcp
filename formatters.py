"""
formatters.py

This module contains functions to format liturgical events for display.

The formatter functions are designed to be used by the Liturgical Calendar
MCP server to format data retrieved from the Liturgical Calendar API.

The functions included in this module are:

- _format_event(event_data: dict): Format a single liturgical event for display
- _format_header(): Format the header for a liturgical calendar
- _format_settings(settings: dict): Format calendar settings for display
- _format_holy_days(events: list): Format Holy Days of Obligation for display
- _format_liturgical_seasons(events: list): Format key liturgical season events for display
- _format_particular_celebrations(events: list): Format celebrations particular to the current calendar, for display
- _format_day_month(day: int, month: int): Format a day and month for display
- _format_reading_field(value: str | None, label: str): Format a single reading field with N/A for missing values
- _format_standard_readings(data: dict, indent: str): Format a standard readings block (ferial or festive)
- _format_easter_vigil_readings(readings: dict): Format Easter Vigil readings (seven readings with epistle)
- _format_christmas_readings(readings: dict): Format Christmas readings (night, dawn, day masses)
- _format_easter_sunday_readings(readings: dict): Format Easter Sunday readings (day and evening)
- _format_multiple_schema_readings(readings: dict): Format multiple schema readings (All Souls Day options)
- _format_seasonal_readings(readings: dict): Format seasonal readings (easter_season/outside_easter_season)
- _format_readings(readings: dict | str): Format readings data into human-readable text
- format_liturgy_response(data: dict): Format liturgy data into a readable summary
- format_announcement_response(data: dict): Format announcement data into a readable summary
- format_suppressed_reinstated_events(data: dict): Format suppressed and reinstated events for display
- format_calendar_summary(data: dict): Format calendar data into a readable summary
"""

from datetime import datetime
import logging
import locale
import calendar
import inflect
from utils import (
    calculate_year_cycles,
    get_base_locale,
    get_event,
    load_announcement_template,
)


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
    lines = ["## Holy Days of Obligation"]
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
        ("Advent1", "### Start of the Advent season"),
        ("Christmas", "### Start of the Christmas season"),
        ("Epiphany", None),
        (
            "BaptismOfTheLord",
            "### End of the Christmas season and start of Ordinary Time",
        ),
        ("AshWednesday", "### Start of the Lent season"),
        ("HolyThursday", "### Start of the Easter Triduum"),
        ("Easter", "### Start of the Easter season"),
        ("Pentecost", "### End of the Easter season and start of Ordinary Time"),
        ("ChristKing", "### Last Sunday of Ordinary Time"),
        ("OrdWeekday34Saturday", "### Last day of the liturgical year"),
    ]

    lines = ["## Start and end of liturgical seasons"]
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
    # Filter for events marked as particular to this calendar
    # The is_particular field is set by comparing with the General Roman Calendar
    particular_events = [
        e
        for e in events
        if e.get("is_particular", False) and not e.get("is_vigil_mass", False)
    ]
    if particular_events:
        lines = ["## Celebrations particular to this calendar"]
        for event in particular_events:
            lines.append(_format_event(event))
            lines.append("")
        lines.append("=" * 60)
        return lines
    return []


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
    month_name = calendar.month_name[month] if 1 <= month <= 12 else month_long
    return p.number_to_words(p.ordinal(day)), month_name


def format_suppressed_reinstated_events(data: dict) -> list:
    """Format suppressed or reinstated celebrations for display."""
    lines = []
    metadata = data.get("metadata", {})
    suppressed_events = metadata.get("suppressed_events", [])
    reinstated_events = metadata.get("reinstated_events", [])

    lines.append(
        "## Celebrations that have been superseded by celebrations of greater rank"
    )
    if suppressed_events:
        for event in suppressed_events:
            superseding_event = next(
                (e for e in data["litcal"] if e.get("date") == event.get("date")), None
            )
            if superseding_event:
                lines.append(
                    "- The liturgical event with key "
                    + event.get("event_key")
                    + " was suppressed on "
                    + event.get("date")
                    + " by the liturgical event:"
                )
                lines.append(_format_event(superseding_event))
                lines.append("")
    else:
        lines.append("  (none)")

    lines.append("=" * 60)

    lines.append(
        "## Celebrations that would have been suppressed or superseded but were finally reinstated"
    )

    if reinstated_events:
        for event in reinstated_events:
            reinstated_event = next(
                (
                    e
                    for e in data["litcal"]
                    if e.get("event_key") == event.get("event_key")
                ),
                None,
            )
            if reinstated_event:
                lines.append(_format_event(reinstated_event))
                lines.append("")
    else:
        lines.append("  (none)")

    lines.append("=" * 60)

    return lines


def format_calendar_summary(data: dict) -> str:
    """Format calendar data into a readable summary."""
    if not data or "litcal" not in data:
        return "No calendar data available"

    liturgical_events = data["litcal"]
    settings = data.get("settings", {})

    lines = []
    lines.extend(_format_header())
    lines.extend(_format_holy_days(liturgical_events))
    lines.extend(_format_liturgical_seasons(liturgical_events))
    lines.extend(_format_particular_celebrations(liturgical_events))
    # the LLM is sometimes confusing info from suppressed events with info from particular celebrations,
    # so we might as well not show it at all until we find a better way
    # lines.extend(_format_suppressed_reinstated_events(data))
    # lines.append("=" * 60)
    lines.append(f"Total events: {len(liturgical_events)}")
    # the lectionary cycles are available for single events, but not to the calendar as a whole,
    # so if we want to see this info, we can just calculate it
    year_cycles = calculate_year_cycles(settings.get("year", datetime.now().year))
    lines.append(f"Festive Lectionary cycle: YEAR {year_cycles['festive_year_cycle']}")
    lines.append(f"Ferial Lectionary cycle: YEAR {year_cycles['ferial_year_cycle']}")
    lines.extend(_format_settings(settings))

    return "\n".join(lines)


def _format_reading_field(value: str | None, label: str) -> str:
    """Format a single reading field with N/A for missing values."""
    return f"{label}: {value if value else 'N/A'}"


def _format_standard_readings(data: dict, indent: str = "   ") -> list:
    """Format a standard readings block (ferial or festive)."""
    block = []
    if "palm_gospel" in data:
        block.append(
            _format_reading_field(data.get("palm_gospel"), f"{indent}Palm Gospel")
        )
    if "first_reading" in data:
        block.append(
            _format_reading_field(data.get("first_reading"), f"{indent}First Reading")
        )
    if "responsorial_psalm" in data:
        block.append(
            _format_reading_field(
                data.get("responsorial_psalm"), f"{indent}Responsorial Psalm"
            )
        )
    if "second_reading" in data:
        block.append(
            _format_reading_field(data.get("second_reading"), f"{indent}Second Reading")
        )
    if "gospel_acclamation" in data:
        block.append(
            _format_reading_field(
                data.get("gospel_acclamation"), f"{indent}Gospel Acclamation"
            )
        )
    if "gospel" in data:
        block.append(_format_reading_field(data.get("gospel"), f"{indent}Gospel"))
    return block


def _format_easter_vigil_readings(readings: dict) -> list:
    """Format Easter Vigil readings (seven readings with epistle)."""
    lines = ["   Readings (Easter Vigil):"]
    ordinal_numbers = [
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
    ]
    for i in range(1, 8):
        reading = readings.get(f"{ordinal_numbers[i-1]}_reading")
        # First psalm is 'responsorial_psalm', others are 'responsorial_psalm_2' through 'responsorial_psalm_7'
        psalm_key = "responsorial_psalm" if i == 1 else f"responsorial_psalm_{i}"
        psalm = readings.get(psalm_key)
        lines.append(f"      Reading {i}: {reading if reading else 'N/A'}")
        lines.append(f"      Responsorial Psalm {i}: {psalm if psalm else 'N/A'}")
    lines.append(_format_reading_field(readings.get("epistle"), "      Epistle"))
    lines.append(
        _format_reading_field(
            readings.get("responsorial_psalm_epistle"),
            "      Responsorial Psalm (Epistle)",
        )
    )
    lines.append(
        _format_reading_field(
            readings.get("gospel_acclamation"), "      Gospel Acclamation"
        )
    )
    lines.append(_format_reading_field(readings.get("gospel"), "      Gospel"))
    return lines


def _format_christmas_readings(readings: dict) -> list:
    """Format Christmas readings (night, dawn, day masses)."""
    lines = ["   Readings (Christmas):"]
    for mass_time in ["night", "dawn", "day"]:
        mass_data = readings.get(mass_time, {})
        if mass_data:
            lines.append(f"      {mass_time.title()} Mass:")
            lines.extend(_format_standard_readings(mass_data, "         "))
    return lines


def _format_easter_sunday_readings(readings: dict) -> list:
    """Format Easter Sunday readings (day and evening)."""
    lines = ["   Readings (Easter Sunday):", "      Day:"]
    lines.extend(_format_standard_readings(readings.get("day", {}), "         "))
    lines.append("      Evening:")
    lines.extend(_format_standard_readings(readings.get("evening", {}), "         "))
    return lines


def _format_multiple_schema_readings(readings: dict) -> list:
    """Format multiple schema readings (All Souls Day options)."""
    lines = ["   Readings (Multiple Options):"]
    for schema_name in ["schema_one", "schema_two", "schema_three"]:
        schema_data = readings.get(schema_name)
        if schema_data:
            lines.append(f"      {schema_name.replace('_', ' ').title()}:")
            lines.extend(_format_standard_readings(schema_data, "         "))
    return lines


def _format_seasonal_readings(readings: dict) -> list:
    """Format seasonal readings (easter_season/outside_easter_season)."""
    lines = ["   Readings (Seasonal):"]
    if "easter_season" in readings:
        lines.append("      Easter Season:")
        lines.extend(
            _format_standard_readings(readings.get("easter_season", {}), "         ")
        )
    if "outside_easter_season" in readings:
        lines.append("      Outside Easter Season:")
        lines.extend(
            _format_standard_readings(
                readings.get("outside_easter_season", {}), "         "
            )
        )
    return lines


def _format_readings(readings: dict | str) -> list:
    """Format readings data into human-readable text.

    Handles multiple reading structures from the Liturgical Calendar API:
    - ReadingsFerial (weekday)
    - ReadingsFestive (feast days with second reading)
    - ReadingsPalmSunday (includes palm_gospel)
    - ReadingsEasterVigil (seven readings with epistle)
    - ReadingsChristmas (night, dawn, day masses)
    - ReadingsWithEvening (day and evening)
    - ReadingsMultipleSchemas (multiple schema options)
    - ReadingsCommons (string reference to commons)
    - ReadingsSeasonal (easter_season/outside_easter_season)
    """
    if not readings:
        return ["   Readings: N/A"]

    if isinstance(readings, str):
        return [f"   Readings: {readings}"]

    # Check for specialized structures
    if "first_reading" in readings and "seventh_reading" in readings:
        return _format_easter_vigil_readings(readings)

    if "day" in readings and "evening" in readings:
        return _format_easter_sunday_readings(readings)

    if all(mass_time in readings for mass_time in ["night", "dawn", "day"]):
        return _format_christmas_readings(readings)
    if any(
        schema in readings for schema in ["schema_one", "schema_two", "schema_three"]
    ):
        return _format_multiple_schema_readings(readings)

    if "easter_season" in readings or "outside_easter_season" in readings:
        return _format_seasonal_readings(readings)

    # Standard readings (ferial or festive)
    lines = ["   Readings:"]
    lines.extend(_format_standard_readings(readings, "      "))
    return lines


def format_liturgy_response(
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
            lines.extend(_format_readings(celebration["readings"]))
        lines.append("")

    lines.append("=" * 60)
    return "✅ " + "\n".join(lines)


def format_announcement_response(data: dict, year: int) -> str:
    """Format the announcement response."""
    settings: dict = data.get("settings", {})
    celebrations = data.get("litcal", [])
    if not celebrations:
        return "❌ No liturgical calendar data found in response"

    p = inflect.engine()
    base_locale = get_base_locale(settings.get("locale", "en"))

    logging.info("Formatting announcement in locale: %s", base_locale)
    previous_locale = locale.setlocale(locale.LC_ALL)

    try:
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
        events = {key: get_event(celebrations, key) for key in keys}

        if any(v is None for v in events.values()):
            return "❌ No liturgical calendar data found in response"

        # Format day/month for all events
        formatted = {
            key: _format_day_month(evt, base_locale, p) for key, evt in events.items()
        }

        lines = [
            f"# Epiphany announcement of Easter and Moveable Feasts for the year {year}",
        ]

        announcement_template_lcl = load_announcement_template(base_locale)
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
    finally:
        locale.setlocale(locale.LC_ALL, previous_locale)
