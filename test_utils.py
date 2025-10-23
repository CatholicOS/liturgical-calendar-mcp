#!/usr/bin/env python3
"""Common utilities for MCP tool testing."""

import json
import sys
from typing import Any


def send_initialize_message(message_id: int = 1) -> None:
    """Send the standard initialize message."""
    msg = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"},
        },
        "id": message_id,
    }
    print(json.dumps(msg), flush=True)


def send_tool_call(
    tool_name: str, arguments: dict[str, Any] | None = None, message_id: int = 2
) -> None:
    """Send a tool call message."""
    msg = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments or {}},
        "id": message_id,
    }
    print(json.dumps(msg), flush=True)


def list_tools(message_id: int = 2) -> None:
    """Send a tools/list message."""
    msg = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": message_id,
    }
    print(json.dumps(msg), flush=True)


def read_responses() -> None:
    """Read and print all responses from stdin."""
    for line in sys.stdin:
        try:
            resp = json.loads(line)
            print("RESPONSE:", json.dumps(resp, indent=2))
        except json.JSONDecodeError as e:
            print("ERROR PARSING RESPONSE:", e)


def run_test(tool_name: str, arguments: dict[str, Any] | None = None) -> None:
    """Run a complete test: initialize, call tool, read responses."""
    send_initialize_message()
    send_tool_call(tool_name, arguments)
    read_responses()


def run_list_tools_test() -> None:
    """Run a test to list available tools."""
    send_initialize_message()
    list_tools()
    read_responses()
