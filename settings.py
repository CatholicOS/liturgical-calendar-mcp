"""
Default settings for the Liturgical Calendar MCP Server.

This module contains the default configuration values used throughout the application.

IMPORTANT: DO NOT modify this file directly to customize settings!
Instead, create a 'litcal.config.yaml' file in the project root.
See 'litcal.config.example.yaml' for a template.

The config.py module will load your custom settings from litcal.config.yaml
and merge them with these defaults. You can also use environment variables
to override any setting (highest priority).

Configuration priority:
1. Environment variables (e.g., LITCAL_API_BASE_URL)
2. User config file (litcal.config.yaml)
3. This file (settings.py - defaults)
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
