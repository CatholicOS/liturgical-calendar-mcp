# Liturgical Calendar MCP Server - Implementation Guide

## Overview

This MCP server provides access to the Roman Catholic Liturgical Calendar API, allowing Claude to retrieve detailed liturgical calendar information for any year between 1970 and 9999.

## Available Tools

### 1. get_general_calendar

Retrieves the General Roman Calendar for a specific year.

**Parameters:**

- `year` (optional): Year to retrieve (1970-9999). Defaults to current year.
- `locale` (optional): Language locale (de, en, es, fr, it, pt, la, nl). Defaults to "en".
- `epiphany_on_sunday` (optional): Whether Epiphany is transferred to Sunday. Defaults to "true".
- `ascension_on_sunday` (optional): Whether Ascension is transferred to Sunday. Defaults to "true".
- `corpus_christi_on_sunday` (optional): Whether Corpus Christi is transferred to Sunday. Defaults to "true".

**Example Usage:**

```txt
What are the liturgical celebrations for 2025?
Show me the General Roman Calendar for Easter 2024
What feasts are celebrated in December 2023?
```

### 2. get_national_calendar

Retrieves the liturgical calendar for a specific nation.

**Parameters:**

- `nation` (required): Two-letter nation code (IT, US, NL, VA, CA)
- `year` (optional): Year to retrieve (1970-9999). Defaults to current year.
- `locale` (optional): Language locale. Defaults to "en".

**Example Usage:**

```txt
Show me the US liturgical calendar for 2024
What are the feast days in Italy this year?
Display the Canadian Catholic calendar for 2025
```

### 3. get_diocesan_calendar

Retrieves the liturgical calendar for a specific diocese.

**Parameters:**

- `diocese` (required): Diocese ID (e.g., romamo_it, boston_us)
- `year` (optional): Year to retrieve. Defaults to current year.
- `locale` (optional): Language locale. Defaults to "en".

**Example Usage:**

```txt
Show me the calendar for the Diocese of Rome
What are the feast days in Boston this year?
Display the diocesan calendar for Turin, Italy
```

### 4. list_available_calendars

Lists all available national and diocesan calendars.

**Parameters:** None

**Example Usage:**

```txt
What liturgical calendars are available?
List all national Catholic calendars
Show me available dioceses
```

### 5. get_liturgy_of_the_day

Retrieves the liturgy of the day. Can optionally retrieve for a specific calendar, and for a specific date.

**Parameters:**

- `calendar_type` (optional): Type of calendar - "general", "national", or "diocesan". Defaults to "general".
- `calendar_id` (optional): ID for nation or diocese (required if calendar_type is not "general")
- `locale` (optional): Language locale. Defaults to "en".
- `date` (optional): Date in YYYY-MM-DD format (e.g., "2024-03-15"). Defaults to today if not provided.

**Example Usage:**

```txt
Show me all liturgical events in the General Roman Calendar for today
Show me the liturgy for the Diocese of Rome
What is the liturgy for the Diocese of Rome for 2024?
Show me the liturgical calendar for Canada in French
```

## Response Format

All tools return formatted text with:

- ✅ Success indicator
- 📅 Date and event markers
- 📖 Calendar section headers
- ❌ Error indicators when applicable
- Liturgical grade (Weekday, Memorial, Feast, Solemnity, etc.)
- Liturgical colors (green, red, white, purple, rose)
- Event names localized to requested locale

## Understanding Liturgical Data

### Liturgical Grades

Events are ranked by importance:

- **Weekday** (0): Regular weekdays
- **Commemoration** (1): Minor commemorations
- **Optional Memorial** (2): Optional celebrations
- **Memorial** (3): Obligatory memorials
- **Feast** (4): Feast days
- **Feast of the Lord** (5): Important feast days of Jesus
- **Solemnity** (6): Highest-ranking celebrations
- **Higher Solemnity** (7): Takes precedence over regular solemnities

### Liturgical Colors

- **White**: Christmas, Easter, celebrations of the Lord, Mary, angels, and non-martyred saints
- **Red**: Palm Sunday, Good Friday, Pentecost, celebrations of martyrs
- **Green**: Ordinary Time
- **Purple/Violet**: Advent and Lent
- **Rose**: Third Sunday of Advent (Gaudete Sunday) and Fourth Sunday of Lent (Laetare Sunday)

### Calendar Types

#### General Roman Calendar

The universal calendar for the entire Roman Catholic Church.

#### National Calendars

Include celebrations specific to a nation (patron saints, national holy days).

#### Diocesan Calendars

Include celebrations specific to a diocese (local patron saints, dedications of local churches).

## Best Practices

1. **Start with list_available_calendars** to see what's available before querying specific calendars
1. **Use appropriate locales** for the user's language preference
1. **Default to current year** when year is not specified
1. **Handle errors gracefully** - invalid nation/diocese codes will return helpful error messages
1. **Consider date ranges** - the API supports years 1970-9999
1. **Use General Calendar** for universal celebrations, national/diocesan for local variations

## Common Use Cases

### Planning Liturgical Celebrations

"What major solemnities are coming up in the next 3 months?"

### Educational Purposes

"Explain the liturgical season of Lent and its major celebrations"

### Parish Planning

"Show me the diocesan calendar for Boston for the entire year 2025"

### Cross-Cultural Understanding

"Compare the Italian and American liturgical calendars - what's different?"

## Limitations

- API is in development mode (dev endpoint)
- Some dioceses may not be available in all years
- Responses are truncated at 50 events for readability (full data still retrieved)
- Historical accuracy only from 1970 forward

## Error Handling

The server provides clear error messages:

- Invalid year ranges
- Unknown nation or diocese codes
- API connectivity issues
- Missing required parameters

Always check error messages for guidance on correct usage.

## Technical Notes

- No authentication required
- Public API with no rate limiting specified
- Timeout set to 30 seconds for requests
- All responses in JSON format from API
- Formatted for readability by the MCP server

---

For more information about the Liturgical Calendar API, visit:
[https://litcal.johnromanodorazio.com](https://litcal.johnromanodorazio.com).
