"""
Configuration loader for the Liturgical Calendar MCP Server.

This module loads configuration from multiple sources in order of priority:
1. Environment variables (highest priority)
2. User configuration file (litcal.config.yaml)
3. Default settings from settings.py (lowest priority)

Users can customize settings by creating a litcal.config.yaml file in the
project root directory. See litcal.config.example.yaml for a template.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

# Import defaults from settings
from settings import (
    API_BASE_URL as DEFAULT_API_BASE_URL,
    DEFAULT_TIMEOUT as DEFAULT_DEFAULT_TIMEOUT,
    METADATA_CACHE_EXPIRY_HOURS as DEFAULT_METADATA_CACHE_EXPIRY_HOURS,
    CALENDAR_CACHE_EXPIRY_HOURS as DEFAULT_CALENDAR_CACHE_EXPIRY_HOURS,
    CACHE_DIR as DEFAULT_CACHE_DIR,
)

# User configuration file path
CONFIG_FILE = Path(__file__).resolve().parent / "litcal.config.yaml"


def load_user_config() -> Dict[str, Any]:
    """
    Load user configuration from litcal.config.yaml if it exists.

    Returns:
        Dict containing user configuration, or empty dict if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return {}

    if yaml is None:
        print(f"Warning: PyYAML is not installed. Cannot load {CONFIG_FILE}", file=sys.stderr)
        print("Install with: pip install pyyaml", file=sys.stderr)
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config if isinstance(config, dict) else {}
    except yaml.YAMLError as e:
        # Log warning but don't fail - use defaults
        print(f"Warning: Could not parse {CONFIG_FILE}: {e}", file=sys.stderr)
        return {}
    except OSError as e:
        # Log warning but don't fail - use defaults
        print(f"Warning: Could not read {CONFIG_FILE}: {e}", file=sys.stderr)
        return {}


def get_config_value(
    key: str,
    default: Any,
    user_config: Dict[str, Any],
    env_var: Optional[str] = None,
    value_type: type = str,
) -> Any:
    """
    Get a configuration value from environment, user config, or default.

    Args:
        key: The configuration key to look up
        default: The default value to use
        user_config: Dictionary of user configuration
        env_var: Environment variable name to check (optional)
        value_type: Type to convert the value to

    Returns:
        The configuration value with priority: env_var > user_config > default
    """
    # First check environment variable
    if env_var and env_var in os.environ:
        value = os.environ[env_var]
        try:
            if value_type is int:
                return int(value)
            if value_type is float:
                return float(value)
            if value_type is bool:
                return value.lower() in ("true", "1", "yes", "on")
            if value_type is Path:
                return Path(value)
            return value
        except (ValueError, TypeError):
            print(f"Warning: Invalid value for {env_var}, using default", file=sys.stderr)

    # Then check user config
    if key in user_config:
        value = user_config[key]
        if value_type is Path and isinstance(value, str):
            return Path(value)
        return value

    # Finally use default
    return default


# Load user configuration once at module import
_user_config = load_user_config()

# =============================================================================
# API Configuration
# =============================================================================

# Base URL for the Liturgical Calendar API
API_BASE_URL = get_config_value(
    key="api_base_url",
    default=DEFAULT_API_BASE_URL,
    user_config=_user_config,
    env_var="LITCAL_API_BASE_URL",
    value_type=str,
)

# Default timeout for API requests (in seconds)
DEFAULT_TIMEOUT = get_config_value(
    key="default_timeout",
    default=DEFAULT_DEFAULT_TIMEOUT,
    user_config=_user_config,
    env_var="LITCAL_DEFAULT_TIMEOUT",
    value_type=int,
)

# =============================================================================
# Cache Configuration
# =============================================================================

# Cache expiry time for metadata (in hours)
METADATA_CACHE_EXPIRY_HOURS = get_config_value(
    key="metadata_cache_expiry_hours",
    default=DEFAULT_METADATA_CACHE_EXPIRY_HOURS,
    user_config=_user_config,
    env_var="LITCAL_METADATA_CACHE_EXPIRY_HOURS",
    value_type=int,
)

# Cache expiry time for calendar data (in hours)
CALENDAR_CACHE_EXPIRY_HOURS = get_config_value(
    key="calendar_cache_expiry_hours",
    default=DEFAULT_CALENDAR_CACHE_EXPIRY_HOURS,
    user_config=_user_config,
    env_var="LITCAL_CALENDAR_CACHE_EXPIRY_HOURS",
    value_type=int,
)

# Cache directory path
_cache_dir_default = DEFAULT_CACHE_DIR
if "LITCAL_CACHE_DIR" in os.environ:
    _cache_path = Path(os.environ["LITCAL_CACHE_DIR"])
    if not _cache_path.is_absolute():
        _cache_path = Path(__file__).resolve().parent / _cache_path
    CACHE_DIR = _cache_path
elif "cache_dir" in _user_config:
    _cache_dir_value = _user_config["cache_dir"]
    if isinstance(_cache_dir_value, str):
        # Support both absolute and relative paths
        _cache_path = Path(_cache_dir_value)
        if not _cache_path.is_absolute():
            # Make relative paths relative to the project root
            _cache_path = Path(__file__).resolve().parent / _cache_path
        CACHE_DIR = _cache_path
    else:
        CACHE_DIR = _cache_dir_default
else:
    CACHE_DIR = _cache_dir_default


# =============================================================================
# Configuration Summary (for debugging)
# =============================================================================


def print_config_summary() -> None:
    """Print a summary of the active configuration (for debugging purposes)."""
    print("\n" + "=" * 70)
    print("Liturgical Calendar MCP Server - Configuration Summary")
    print("=" * 70)
    print("\nAPI Configuration:")
    print(f"  API_BASE_URL: {API_BASE_URL}")
    print(f"  DEFAULT_TIMEOUT: {DEFAULT_TIMEOUT}s")
    print("\nCache Configuration:")
    print(f"  METADATA_CACHE_EXPIRY_HOURS: {METADATA_CACHE_EXPIRY_HOURS}h")
    print(f"  CALENDAR_CACHE_EXPIRY_HOURS: {CALENDAR_CACHE_EXPIRY_HOURS}h")
    print(f"  CACHE_DIR: {CACHE_DIR}")
    print("\nConfiguration Sources:")
    if CONFIG_FILE.exists():
        print(f"  User config loaded from: {CONFIG_FILE}")
    else:
        print("  User config: Not found (using defaults)")
    print("  Defaults from: settings.py")
    print("=" * 70 + "\n")
