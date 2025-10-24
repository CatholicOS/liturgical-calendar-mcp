#!/usr/bin/env python3
"""Test script for get_liturgy_of_the_day tool."""

from test_utils import run_test

if __name__ == "__main__":
    run_test("get_liturgy_of_the_day", {
        "calendar_id": "CA",
        "calendar_type": "national",
        "date": "",
        "locale": "fr_CA"
    })
