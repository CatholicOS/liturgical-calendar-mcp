#!/usr/bin/env python3
"""Test script for get_diocesan_calendar tool."""

from test_utils import run_test

if __name__ == "__main__":
    run_test(
        "get_diocesan_calendar",
        {"year": 2024, "target_locale": "nl_NL", "diocese": "bredad_nl"},
    )
