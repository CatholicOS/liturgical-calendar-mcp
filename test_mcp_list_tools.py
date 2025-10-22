#!/usr/bin/env python3
import json
import sys

# Define MCP messages to send
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
        "method": "tools/list",
        "params": {},
        "id": 2
    }
]

# Send messages to server
for msg in messages:
    # print as compact JSON on a single line
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()
