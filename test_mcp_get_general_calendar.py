#!/usr/bin/env python3
import json
import sys

# Messages to send
messages = [
    {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"}
        },
        "id": 1
    },
    {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "get_general_calendar", "arguments": {}},
        "id": 2
    }
]

# Send messages
for msg in messages:
    print(json.dumps(msg), flush=True)

# Keep reading responses
for line in sys.stdin:
    try:
        resp = json.loads(line)
        print("RESPONSE:", json.dumps(resp, indent=2))
    except json.JSONDecodeError as e:
        print("ERROR PARSING RESPONSE:", e)
