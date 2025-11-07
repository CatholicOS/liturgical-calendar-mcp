"""
constants.py - Contains constants used across the liturgical calendar MCP.
"""

from pathlib import Path


# =============================================================================
# Directory Paths
# =============================================================================

# Directory for noveritis locale templates
NOVERITIS_DIR = Path(__file__).resolve().parent / "noveritis"


# =============================================================================
# Calendar Constants
# =============================================================================

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

# Expected date format for date strings
DATE_FORMAT = "%Y-%m-%d"
