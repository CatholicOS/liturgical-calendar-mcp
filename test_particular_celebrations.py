#!/usr/bin/env python3
"""Test script to verify particular celebrations are correctly identified."""

import asyncio
import sys
from litcal_server import mcp


async def test_national_calendar(nation: str, year: int = 2024):
    """Test particular celebrations detection for a national calendar."""
    print(f"\n{'='*60}")
    print(f"Testing {nation} National Calendar for {year}")
    print('='*60)

    # Get the national calendar
    result = await mcp.call_tool(
        "get_national_calendar",
        {"nation": nation, "year": year, "locale": "en"}
    )

    # Extract and print the result
    if hasattr(result, 'content') and len(result.content) > 0:
        text_content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])

        # Find the "Celebrations particular to this calendar" section
        if "## Celebrations particular to this calendar" in text_content:
            lines = text_content.split('\n')
            in_particular_section = False
            particular_celebrations = []

            for line in lines:
                if "## Celebrations particular to this calendar" in line:
                    in_particular_section = True
                    continue
                elif in_particular_section:
                    if line.startswith("==="):
                        break
                    if line.startswith("📅"):
                        particular_celebrations.append(line)

            print(f"\nFound {len(particular_celebrations)} particular celebration(s):")
            for celebration in particular_celebrations[:10]:  # Show first 10
                print(f"  {celebration}")

            if len(particular_celebrations) > 10:
                print(f"  ... and {len(particular_celebrations) - 10} more")
        else:
            print("\n⚠️  No particular celebrations found in output")
            # Print a sample of the output
            print("\nSample output:")
            print(text_content[:1000])
    else:
        print(f"\n❌ Error: {result}")


async def main():
    """Run tests for different national calendars."""
    # Test USA (has square brackets with variations)
    await test_national_calendar("US", 2024)

    # Test Italy (no square brackets)
    await test_national_calendar("IT", 2024)

    # Test Canada for comparison
    await test_national_calendar("CA", 2024)


if __name__ == "__main__":
    asyncio.run(main())
