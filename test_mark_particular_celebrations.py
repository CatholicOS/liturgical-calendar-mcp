"""Unit test for mark_particular_celebrations function."""

from utils import mark_particular_celebrations


def test_mark_particular_celebrations():
    """Test that particular celebrations are correctly identified."""

    # Mock General Roman Calendar data
    general_calendar = {
        "litcal": [
            {"event_key": "Easter", "name": "Easter Sunday", "grade": 7},
            {"event_key": "Christmas", "name": "The Nativity of the Lord", "grade": 7},
            {"event_key": "AllSaints", "name": "All Saints' Day", "grade": 6},
            {"event_key": "Pentecost", "name": "Pentecost Sunday", "grade": 6},
            {
                "event_key": "ImmaculateConception",
                "name": "Immaculate Conception of the Blessed Virgin Mary",
                "grade": 6,
            },
        ]
    }

    # Mock National Calendar (USA) data with particular celebrations
    # Note: USA has some events with square brackets, some without
    national_calendar_usa = {
        "litcal": [
            {
                "event_key": "Easter",
                "name": "Easter Sunday",
                "grade": 7,
            },  # In general calendar
            {
                "event_key": "Christmas",
                "name": "The Nativity of the Lord",
                "grade": 7,
            },  # In general calendar
            {
                "event_key": "ImmaculateConception",
                "name": "Immaculate Conception [USA - Patronal Feast]",
                "grade": 6,
            },  # Same event_key as general, but marked particular by brackets
            {
                "event_key": "StPatrick",
                "name": "[ USA ] Saint Patrick",
                "grade": 3,
            },  # Particular with brackets
            {
                "event_key": "OurLadyOfGuadalupe",
                "name": "Our Lady of Guadalupe",
                "grade": 4,
            },  # Particular without brackets
            {
                "event_key": "ChristmasWeekdayUSA",
                "name": "December 26 - Weekday after Christmas",
                "grade": 0,
            },  # Weekday - should NOT be marked as particular despite being unique
        ]
    }

    # Mock National Calendar (Italy) data
    # Note: Italy doesn't use square brackets for particular celebrations
    national_calendar_italy = {
        "litcal": [
            {
                "event_key": "Easter",
                "name": "Easter Sunday",
                "grade": 7,
            },  # In general calendar
            {
                "event_key": "AllSaints",
                "name": "All Saints' Day",
                "grade": 6,
            },  # In general calendar
            {
                "event_key": "StFrancisOfAssisi",
                "name": "San Francesco d'Assisi",
                "grade": 4,
            },  # Particular, no brackets
            {
                "event_key": "StCatherineOfSiena",
                "name": "Santa Caterina da Siena, Patrona d'Italia",
                "grade": 4,
            },  # Particular, modified name
        ]
    }

    # Test USA calendar
    print("Testing USA National Calendar:")
    print("=" * 60)
    result_usa = mark_particular_celebrations(national_calendar_usa, general_calendar)
    for event in result_usa["litcal"]:
        is_particular = event.get("is_particular", False)
        marker = "✓ PARTICULAR" if is_particular else "  (general)"
        print(f"{marker}: {event['name']}")

    # Verify USA results
    assert (
        result_usa["litcal"][0]["is_particular"] is False
    ), "Easter should not be particular"
    assert (
        result_usa["litcal"][1]["is_particular"] is False
    ), "Christmas should not be particular"
    assert (
        result_usa["litcal"][2]["is_particular"] is True
    ), "Immaculate Conception with brackets should be particular despite same event_key"
    assert (
        result_usa["litcal"][3]["is_particular"] is True
    ), "St Patrick USA should be particular"
    assert (
        result_usa["litcal"][4]["is_particular"] is True
    ), "Our Lady of Guadalupe should be particular"
    assert (
        result_usa["litcal"][5]["is_particular"] is False
    ), "Weekday events (grade=0) should not be marked as particular even if unique to calendar"

    print("\n✅ USA calendar: All assertions passed!")

    # Test Italy calendar
    print("\nTesting Italy National Calendar:")
    print("=" * 60)
    result_italy = mark_particular_celebrations(
        national_calendar_italy, general_calendar
    )
    for event in result_italy["litcal"]:
        is_particular = event.get("is_particular", False)
        marker = "✓ PARTICULAR" if is_particular else "  (general)"
        print(f"{marker}: {event['name']}")

    # Verify Italy results
    assert (
        result_italy["litcal"][0]["is_particular"] is False
    ), "Easter should not be particular"
    assert (
        result_italy["litcal"][1]["is_particular"] is False
    ), "All Saints should not be particular"
    assert (
        result_italy["litcal"][2]["is_particular"] is True
    ), "St Francis should be particular"
    assert (
        result_italy["litcal"][3]["is_particular"] is True
    ), "St Catherine should be particular"

    print("\n✅ Italy calendar: All assertions passed!")

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe hybrid approach successfully identifies particular celebrations by:")
    print("1. Comparing event_key values with the General Roman Calendar")
    print("2. Detecting square brackets in event names (e.g., [USA], [Diocese])")
    print("3. Marking as particular if EITHER condition is true")
    print("4. Handles both USA (with brackets) and Italy (without brackets)")
    print(
        "5. Correctly filters out weekday events (grade=0) from particular celebrations"
    )


if __name__ == "__main__":
    test_mark_particular_celebrations()
