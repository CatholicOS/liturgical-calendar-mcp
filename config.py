"""
Configuration loader for the Liturgical Calendar MCP Server.

This module loads configuration from multiple sources in order of priority:
1. Environment variables (highest priority)
2. User configuration file (litcal.config.yaml or litcal.config.yml)
3. Default settings from settings.py (lowest priority)

Users can customize settings by creating a litcal.config.yaml file in the
project root directory. See litcal.config.example.yaml for a template.
"""

import os
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

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

logger = logging.getLogger("litcal.config")

# User configuration file path
CONFIG_FILE_YAML = Path(__file__).resolve().parent / "litcal.config.yaml"
CONFIG_FILE_YML = Path(__file__).resolve().parent / "litcal.config.yml"


def _get_config_file() -> Optional[Path]:
    """
    Return the user configuration file path if it exists, otherwise None.
    """
    if CONFIG_FILE_YAML.exists():
        return CONFIG_FILE_YAML
    if CONFIG_FILE_YML.exists():
        return CONFIG_FILE_YML
    return None


def _load_user_config(user_config_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load user configuration from a YAML file if it exists.

    Args:
        user_config_file: Path to the user configuration file. If None, no config is loaded.

    Returns:
        Dict containing user configuration, or empty dict if file doesn't exist.
    """
    if user_config_file is None or not user_config_file.exists():
        return {}

    if yaml is None:
        logger.warning("PyYAML is not installed. Cannot load %s", user_config_file)
        logger.info("Install with: pip install pyyaml")
        return {}

    try:
        with open(user_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config if isinstance(config, dict) else {}
    except yaml.YAMLError as e:
        # Log warning but don't fail - use defaults
        logger.warning("Could not parse %s: %s", user_config_file, e)
        return {}
    except OSError as e:
        # Log warning but don't fail - use defaults
        logger.warning("Could not read %s: %s", user_config_file, e)
        return {}


def _convert_type(value: str, value_type: type) -> Any:
    """
    Convert a string value to the specified type.

    Args:
        value: The string value to convert
        value_type: The type to convert to

    Returns:
        The converted value

    Raises:
        ValueError: If conversion fails
    """
    if value_type is int:
        return int(value)
    if value_type is float:
        return float(value)
    if value_type is bool:
        return value.lower() in ("true", "1", "yes", "on")
    if value_type is Path:
        return Path(value)
    return value


def _apply_transform(
    value: Any,
    transform: Optional[Callable[[Any], Any]],
    default: Any,
    config_name: str,
) -> Any:
    """
    Apply transform to a value with error handling.

    Args:
        value: The value to transform
        transform: The transform function to apply
        default: The default value to use if transform fails
        config_name: Name of the config for logging

    Returns:
        Transformed value or default if transform fails
    """
    if transform is None:
        return value

    try:
        return transform(value)
    except (ValueError, TypeError, AttributeError) as e:
        # Intentionally catch all exceptions to ensure config loading never fails
        logger.warning("Transform failed for %s: %s, using default", config_name, e)
        return default


def _get_config_value(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    key: str,
    default: Any,
    user_config: Dict[str, Any],
    env_var: Optional[str] = None,
    value_type: type = str,
    transform: Optional[Callable[[Any], Any]] = None,
) -> Any:
    """
    Get a configuration value from environment, user config, or default.

    Args:
        key: The configuration key to look up
        default: The default value to use
        user_config: Dictionary of user configuration
        env_var: Environment variable name to check (optional)
        value_type: Type to convert the value to
        transform: Optional callback to transform the value before returning

    Returns:
        The configuration value with priority ***env_var*** > ***user_config*** > ***default***
    """
    config_name = env_var or key

    # First check environment variable
    if env_var and env_var in os.environ:
        try:
            converted = _convert_type(os.environ[env_var], value_type)
            return _apply_transform(converted, transform, default, config_name)
        except (ValueError, TypeError):
            logger.warning("Invalid value for %s, using default", config_name)

    # Then check user config
    if key in user_config:
        value = user_config[key]
        if value_type is Path and isinstance(value, str):
            value = Path(value)
        return _apply_transform(value, transform, default, config_name)

    # Finally use default
    return default


# Load user configuration once at module import
config_file = _get_config_file()
_user_config = _load_user_config(config_file)


def _resolve_relative_path(path: Path) -> Path:
    """
    Resolve relative paths to be relative to the config module directory.

    Args:
        path: The path to resolve

    Returns:
        Absolute path (resolved relative to `config.py`'s directory if originally relative)
    """
    if not path.is_absolute():
        return Path(__file__).resolve().parent / path
    return path


def _validate_positive_integer(value: int, default: int) -> int:
    """
    Ensure value is positive.

    Args:
        value: The value to validate
        default: The default value to return if validation fails

    Returns:
        The value if positive, otherwise the default
    """
    if value <= 0:
        logger.warning("Invalid value %d, using default %d", value, default)
        return default
    return value


# =============================================================================
# API Configuration
# =============================================================================


# Base URL for the Liturgical Calendar API
API_BASE_URL = _get_config_value(
    key="api_base_url",
    default=DEFAULT_API_BASE_URL,
    user_config=_user_config,
    env_var="LITCAL_API_BASE_URL",
    value_type=str,
)

# Default timeout for API requests (in seconds)
DEFAULT_TIMEOUT = _get_config_value(
    key="default_timeout",
    default=DEFAULT_DEFAULT_TIMEOUT,
    user_config=_user_config,
    env_var="LITCAL_DEFAULT_TIMEOUT",
    value_type=int,
    transform=lambda v: _validate_positive_integer(v, DEFAULT_DEFAULT_TIMEOUT),
)

# =============================================================================
# Cache Configuration
# =============================================================================

# Cache expiry time for metadata (in hours)
METADATA_CACHE_EXPIRY_HOURS = _get_config_value(
    key="metadata_cache_expiry_hours",
    default=DEFAULT_METADATA_CACHE_EXPIRY_HOURS,
    user_config=_user_config,
    env_var="LITCAL_METADATA_CACHE_EXPIRY_HOURS",
    value_type=int,
    transform=lambda v: _validate_positive_integer(
        v, DEFAULT_METADATA_CACHE_EXPIRY_HOURS
    ),
)

# Cache expiry time for calendar data (in hours)
CALENDAR_CACHE_EXPIRY_HOURS = _get_config_value(
    key="calendar_cache_expiry_hours",
    default=DEFAULT_CALENDAR_CACHE_EXPIRY_HOURS,
    user_config=_user_config,
    env_var="LITCAL_CALENDAR_CACHE_EXPIRY_HOURS",
    value_type=int,
    transform=lambda v: _validate_positive_integer(
        v, DEFAULT_CALENDAR_CACHE_EXPIRY_HOURS
    ),
)

# Cache directory path (supports both absolute and relative paths)
CACHE_DIR = _get_config_value(
    key="cache_dir",
    default=DEFAULT_CACHE_DIR,
    user_config=_user_config,
    env_var="LITCAL_CACHE_DIR",
    value_type=Path,
    transform=_resolve_relative_path,
)


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
    if config_file is not None and config_file.exists():
        print(f"  User config loaded from: {config_file}")
    else:
        print("  User config: Not found (using defaults)")
    print("  Defaults from: settings.py")
    print("=" * 70 + "\n")
