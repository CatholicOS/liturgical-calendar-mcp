#!/usr/bin/env python3
"""Test script for get_national_calendar tool."""

from test_utils import run_test

if __name__ == "__main__":
    run_test(
        "get_national_calendar",
        {"year": "2024", "target_locale": "fr_CA", "nation": "CA"},
    )
