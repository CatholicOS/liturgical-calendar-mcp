#!/usr/bin/env python3
"""Test script for get_liturgy_of_the_day tool."""

from test_utils import run_test

if __name__ == "__main__":

    run_test(
        "get_liturgy_of_the_day",
        {
            "date": "3056-12-18",
            "target_locale": "nl_NL",
            "calendar_id": "NL",
            "calendar_type": "national",
        },
    )
