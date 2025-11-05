#!/usr/bin/env python3
"""Unit test for mark_particular_celebrations function."""

from utils import mark_particular_celebrations


def test_mark_particular_celebrations():
    """Test that particular celebrations are correctly identified."""

    # Mock General Roman Calendar data
    general_calendar = {
        "litcal": [
            {"event_key": "Easter", "name": "Easter Sunday"},
            {"event_key": "Christmas", "name": "The Nativity of the Lord"},
            {"event_key": "AllSaints", "name": "All Saints' Day"},
            {"event_key": "Pentecost", "name": "Pentecost Sunday"},
        ]
    }

    # Mock National Calendar (USA) data with particular celebrations
    # Note: USA has some events with square brackets, some without
    national_calendar_usa = {
        "litcal": [
            {"event_key": "Easter", "name": "Easter Sunday"},  # In general calendar
            {
                "event_key": "Christmas",
                "name": "The Nativity of the Lord",
            },  # In general calendar
            {
                "event_key": "ImmaculateConceptionUSA",
                "name": "Immaculate Conception",
            },  # Particular to USA
            {
                "event_key": "StPatrick",
                "name": "[ USA ] Saint Patrick",
            },  # Particular with brackets
            {
                "event_key": "OurLadyOfGuadalupe",
                "name": "Our Lady of Guadalupe",
            },  # Particular without brackets
        ]
    }

    # Mock National Calendar (Italy) data
    # Note: Italy doesn't use square brackets for particular celebrations
    national_calendar_italy = {
        "litcal": [
            {"event_key": "Easter", "name": "Easter Sunday"},  # In general calendar
            {
                "event_key": "AllSaints",
                "name": "All Saints' Day",
            },  # In general calendar
            {
                "event_key": "StFrancisOfAssisi",
                "name": "San Francesco d'Assisi",
            },  # Particular, no brackets
            {
                "event_key": "StCatherineOfSiena",
                "name": "Santa Caterina da Siena, Patrona d'Italia",
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
        result_usa["litcal"][0]["is_particular"] == False
    ), "Easter should not be particular"
    assert (
        result_usa["litcal"][1]["is_particular"] == False
    ), "Christmas should not be particular"
    assert (
        result_usa["litcal"][2]["is_particular"] == True
    ), "Immaculate Conception USA should be particular"
    assert (
        result_usa["litcal"][3]["is_particular"] == True
    ), "St Patrick USA should be particular"
    assert (
        result_usa["litcal"][4]["is_particular"] == True
    ), "Our Lady of Guadalupe should be particular"

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
        result_italy["litcal"][0]["is_particular"] == False
    ), "Easter should not be particular"
    assert (
        result_italy["litcal"][1]["is_particular"] == False
    ), "All Saints should not be particular"
    assert (
        result_italy["litcal"][2]["is_particular"] == True
    ), "St Francis should be particular"
    assert (
        result_italy["litcal"][3]["is_particular"] == True
    ), "St Catherine should be particular"

    print("\n✅ Italy calendar: All assertions passed!")

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe fix successfully identifies particular celebrations by:")
    print("1. Comparing event_key values with the General Roman Calendar")
    print("2. Works regardless of whether names have square brackets")
    print("3. Handles both USA (with brackets) and Italy (without brackets)")


if __name__ == "__main__":
    test_mark_particular_celebrations()
