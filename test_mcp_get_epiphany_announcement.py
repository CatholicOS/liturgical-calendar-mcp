#!/usr/bin/env python3
"""Test script for get_announcement_easter_and_moveable_feasts tool."""

from test_utils import run_test

if __name__ == "__main__":

    run_test(
        "get_announcement_easter_and_moveable_feasts",
        {
            "year": "2023",
            "target_locale": "fr_CA",
            "calendar_id": "CA",
            "calendar_type": "national",
        },
    )
