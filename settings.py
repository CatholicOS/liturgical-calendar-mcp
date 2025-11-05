"""
Centralized configuration for the Liturgical Calendar MCP Server.

This module contains all configurable constants used throughout the application,
including API URLs, file paths, cache settings, and validation constants.
"""

from pathlib import Path

# =============================================================================
# API Configuration
# =============================================================================

# Base URL for the Liturgical Calendar API
API_BASE_URL = "https://litcal.johnromanodorazio.com/api/dev"

# Default timeout for API requests (in seconds)
DEFAULT_TIMEOUT = 30

# Default year type parameter for API requests
DEFAULT_YEAR_TYPE = "CIVIL"


# =============================================================================
# Cache Configuration
# =============================================================================

# Cache expiry time for metadata (in hours)
METADATA_CACHE_EXPIRY_HOURS = 24  # 1 day

# Cache expiry time for calendar data (in hours)
CALENDAR_CACHE_EXPIRY_HOURS = 24 * 7  # 1 week

# Cache directory path (relative to this file)
CACHE_DIR = Path(__file__).resolve().parent / "cache"


# =============================================================================
# Directory Paths
# =============================================================================

# Directory for noveritis locale templates
NOVERITIS_DIR = Path(__file__).parent / "noveritis"


# =============================================================================
# Calendar Constants
# =============================================================================

# Valid calendar types
VALID_CALENDAR_TYPES = ("general", "national", "diocesan")

# Festive cycle for Sundays (repeats every 3 years)
FESTIVE_CYCLE = ["A", "B", "C"]

# Ferial cycle for weekdays (repeats every 2 years)
FERIAL_CYCLE = ["I", "II"]


# =============================================================================
# Year Validation
# =============================================================================

# Minimum year supported by the API
MIN_YEAR = 1970

# Maximum year supported by the API
MAX_YEAR = 9999


# =============================================================================
# File Formats
# =============================================================================

# Cache file extension
CACHE_FILE_EXTENSION = ".json"

# Date format for date strings
DATE_FORMAT = "%Y-%m-%d"
