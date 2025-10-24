# Local Installation Guide

This guide explains how to add the Liturgical Calendar MCP server to Claude Desktop and VS Code.

## Prerequisites

- Python 3.8+ installed and in your PATH
- Claude Desktop (macOS/Windows) or VS Code with GitHub Copilot extension
- If using a virtual environment, note the path to `venv/bin/python` (or `venv\Scripts\python.exe` on Windows)
- Test the server works: `python litcal_server.py` should start without errors

⚠️ **Security**: MCP servers can access sensitive data. Only use trusted implementations.

## Claude Desktop - macOS

1. Open **Claude menu > Settings > Developer**
2. Click **Edit Config** to open `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Add your server configuration:

   **Without virtual environment:**

   ```json
   {
     "mcpServers": {
       "litcal": {
         "command": "python",
         "args": ["/absolute/path/to/litcal_server.py"]
       }
     }
   }
   ```

   **With virtual environment (recommended):**

   ```json
   {
     "mcpServers": {
       "litcal": {
         "command": "/absolute/path/to/venv/bin/python",
         "args": ["/absolute/path/to/litcal_server.py"]
       }
     }
   }
   ```

4. Save, quit Claude Desktop completely, and relaunch
5. Verify: Click the hammer icon (🔨) in the input box to see available tools

**Troubleshooting**: Check logs at `~/Library/Logs/Claude/mcp*.log`

## Claude Desktop - Windows

1. Open **Claude menu > Settings > Developer**
2. Click **Edit Config** to open `%APPDATA%\Claude\claude_desktop_config.json`
3. Add your server configuration:

   **Without virtual environment:**

   ```json
   {
     "mcpServers": {
       "litcal": {
         "command": "python",
         "args": ["C:\\absolute\\path\\to\\litcal_server.py"]
       }
     }
   }
   ```

   **With virtual environment (recommended):**

   ```json
   {
     "mcpServers": {
       "litcal": {
         "command": "C:\\absolute\\path\\to\\venv\\Scripts\\python.exe",
         "args": ["C:\\absolute\\path\\to\\litcal_server.py"]
       }
     }
   }
   ```

   *Note: Use double backslashes (`\\`) or forward slashes (`/`) in paths*

4. Save, exit Claude Desktop fully, and relaunch
5. Verify: Click the hammer icon (🔨) in the input box to see available tools

**Troubleshooting**: Check logs at `%APPDATA%\Claude\logs\mcp*.log`

## Claude Desktop - Linux

⚠️ Claude Desktop is not officially supported on Linux. Use VS Code instead (see below).

If however you are developing on WSL, you can use the following configuration:

  ```json
  {
    "mcpServers": {
      "litcal": {
        "command": "wsl.exe",
          "args": [
            "bash",
            "-c",
            "~/[path]/liturgical-calendar-mcp/venv/bin/python ~/[path]/liturgical-calendar-mcp/litcal_server.py"
          ]
      }
    }
  }
  ```

## VS Code (macOS, Windows, Linux)

### Workspace Configuration (Project-Specific)

1. Open your project in VS Code
2. Create `.vscode/mcp.json` in the project root
3. Add your server configuration:

   **Without virtual environment:**

   ```json
   {
     "servers": {
       "litcal": {
         "type": "stdio",
         "command": "python",
         "args": ["${workspaceFolder}/litcal_server.py"]
       }
     }
   }
   ```

   **With virtual environment (recommended):**

   ```json
   {
     "servers": {
       "litcal": {
         "type": "stdio",
         "command": "${workspaceFolder}/venv/bin/python",
         "args": ["${workspaceFolder}/litcal_server.py"]
       }
     }
   }
   ```

   *Windows: Use `"${workspaceFolder}/venv/Scripts/python.exe"`*

4. Save the file. VS Code will prompt to trust and start the server
5. Verify: Open Copilot Chat (`Ctrl+Alt+I` / `⌃⌘I`) and ask "What liturgical tools are available?"

### Global Configuration (All Workspaces)

1. Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) > **MCP: Add Server** > **Global**
2. Enter the command and arguments when prompted
3. Verify in Copilot Chat

**Troubleshooting**: View logs via **MCP: List Servers** > select server > **Show Output**

## Configuration Reference

| Platform | Config File | Auto-Start |
|----------|-------------|------------|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` | Yes |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` | Yes |
| VS Code (Workspace) | `.vscode/mcp.json` | On use |
| VS Code (Global) | User `settings.json` (`mcp.servers`) | On use |

## Testing the Server

Once configured, test with these prompts:

- "What liturgical calendars are available?"
- "Get the general Roman calendar for 2025"
- "Show me the liturgical calendar for Italy this year"

The server provides these tools:

- `get_general_calendar` - General Roman Calendar by year
- `get_national_calendar` - National calendar (IT, US, NL, VA, CA, etc.)
- `get_diocesan_calendar` - Diocesan calendar by ID
- `list_available_calendars` - List all available calendars
