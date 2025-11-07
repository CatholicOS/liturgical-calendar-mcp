"""
Centralized configuration for the Liturgical Calendar MCP Server.

This module contains all configurable constants used throughout the application,
including API URLs, file paths, cache settings...
"""

from pathlib import Path

# =============================================================================
# API Configuration
# =============================================================================

# Base URL for the Liturgical Calendar API
API_BASE_URL = "https://litcal.johnromanodorazio.com/api/dev"

# Default timeout for API requests (in seconds)
DEFAULT_TIMEOUT = 30


# =============================================================================
# Cache Configuration
# =============================================================================

# Cache expiry time for metadata (in hours)
METADATA_CACHE_EXPIRY_HOURS = 24  # 1 day

# Cache expiry time for calendar data (in hours)
CALENDAR_CACHE_EXPIRY_HOURS = 24 * 7  # 1 week

# Cache directory path (relative to this file)
CACHE_DIR = Path(__file__).resolve().parent / "cache"
