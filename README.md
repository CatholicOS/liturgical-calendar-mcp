# Liturgical Calendar MCP Server

A **Model Context Protocol (MCP)** server that provides access to the [Roman Catholic Liturgical Calendar API](https://github.com/Liturgical-Calendar/LiturgicalCalendarAPI)
allowing retrieval of liturgical calendar data for any year, or for various nations, or dioceses.

The MCP server is a secure interface for AI assistants to access liturgical calendar data, providing a unified interface
as a structured toolset for AI agents. This enables compliant AI systems (like ChatGPT MCP clients, LangChain agents, and custom LLM runtimes)
to reason over liturgical dates, seasons, feasts, saints, and liturgical rankings with full contextual intelligence.

## Purpose

This MCP server provides a secure interface for AI assistants to access liturgical calendar data from the Liturgical Calendar API maintained by Rev. John R. D'Orazio.
It supports querying the General Roman Calendar, national calendars, and diocesan calendars with historical accuracy from 1970 to 9999.

## Features

### Current Implementation

- **`get_general_calendar`** - Retrieve the General Roman Calendar for a specific year with optional locale
- **`get_national_calendar`** - Retrieve the liturgical calendar for a specific nation (IT, US, NL, VA, CA) and year
- **`get_diocesan_calendar`** - Retrieve the liturgical calendar for a specific diocese and year
- **`list_available_calendars`** - List all available national and diocesan calendars with their locales and settings
- **`get_liturgical_events`** - Retrieve all possible liturgical events for a calendar type (general, national, or diocesan)

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- No authentication required - the API is publicly accessible

## Installation

1. **Install Docker Desktop**

   Download and install Docker Desktop from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).

2. **Enable Docker MCP Toolkit**

   Open the Docker Desktop settings and enable the MCP Toolkit under the "Beta Features" tab.
   You should now see the "MCP Toolkit" icon in the Docker Desktop left sidebar.
   Perhaps try enabling a tool from the catalog as a proof of concept, for example "Obsidian".
   Then connect the MCP Toolkit to a client like Claude Desktop.
   After restarting Claude Desktop, when clicking on the "Tools" icon below the chat prompt,
   you should see an "MCP_DOCKER" category, and clicking on the arrow next to that
   you should see available tool calls (for example obsidian tool calls if you enabled the Obsidian tool from the Docker MCP catalog).

3. **Clone the repository**

   ```bash
   git clone https://github.com/CatholicOS/liturgical-calendar-mcp.git
   cd liturgical-calendar-mcp
   ```

4. **Build the Docker image**

   ```bash
   docker build -t liturgical-calendar-mcp .
   ```

5. **Update the Docker Desktop MCP catalog**

Edit the file `%USERPROFILE%\.docker\mcp\catalogs\docker-mcp.yaml`, and paste this at the end:

```yaml
  litcal:
    description: "Access Roman Catholic Liturgical Calendar data for any year, nation, or diocese from 1970-9999"
    title: "Liturgical Calendar"
    type: server
    dateAdded: "2025-10-22T00:00:00Z"
    image: litcal-mcp-server:latest
    ref: ""
    readme: ""
    toolsUrl: ""
    source: ""
    upstream: ""
    icon: ""
    tools:
      - name: get_general_calendar
      - name: get_national_calendar
      - name: get_diocesan_calendar
      - name: list_available_calendars
      - name: get_liturgical_events
    metadata:
      category: integration
      tags:
        - catholic
        - liturgy
        - calendar
        - religious
      license: MIT
      owner: local
```

`litcal` should be a descendant of `registry`.

Edit the file `%USERPROFILE%\.docker\mcp\registry.yaml`, and paste this at the end:

```yaml
  litcal:
    ref: ""
```

Again, `litcal` should be a descendant of `registry`.

No need to start any containers, Docker MCP Toolkit will spin up the tool container on demand when an agent attempts to access the tool.

Try with Claude Desktop: if it was already started, exit Claude Desktop completely (make sure it is not running in the background in the tray) and start it again.

You should now see the "Liturgical Calendar" tool in the tools list under `MCP_DOCKER` category.

## Usage Examples

In Claude Desktop, you can ask:

- "What are the liturgical celebrations for Easter 2025?"
- "Show me the liturgical calendar for the United States in 2024"
- "What is the calendar for the Diocese of Rome for this year?"
- "List all available national liturgical calendars"
- "What are the major feast days in the Italian liturgical calendar?"
- "Show me all optional memorials in the General Roman Calendar"
- "What liturgical events are celebrated in Canada?"

## Architecture

```mermaid
flowchart LR
  ClaudeDesktop --> MCPGateway --> LiturgicalCalendarMCPServer --> LiturgicalCalendarAPI
```

## API Information

- **Base URL**: [https://litcal.johnromanodorazio.com/api/dev](https://litcal.johnromanodorazio.com/api/dev)
- **Documentation**: [openapi.json](https://raw.githubusercontent.com/Liturgical-Calendar/LiturgicalCalendarAPI/refs/heads/development/jsondata/schemas/openapi.json)
   Based on OpenAPI 3.1.0 specification
- **License**: Apache 2.0
- **Maintainer**: Rev. John R. D'Orazio
- **Supported Years**: 1970-9999
- **Available Locales**: de, en, es, fr, it, pt, la, nl

## Calendar Types

### General Roman Calendar

The universal calendar for the Roman Catholic Church

### National Calendars

- **IT** - Italy
- **US** - United States
- **NL** - Netherlands
- **VA** - Vatican
- **CA** - Canada

### Diocesan Calendars

Various dioceses within national territories (use `list_available_calendars` to see all)

## Development

### Local Testing

```bash
# Run directly
python3.12 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
python litcal_server.py
# Ctrl+C to stop (you may have to do so a few times)

# Test MCP protocol
python test_mcp_list_tools.py | python litcal_server.py | jq
# This should output, in pretty-printed JSON format, the tools made available by the MCP server
```

### Adding New Tools

1. Add the function to `litcal_server.py`
1. Decorate with `@mcp.tool()`
1. Use single-line docstrings
1. Ensure all parameters have empty string defaults
1. Return formatted strings with emojis
1. Update the catalog entry with the new tool name
1. Rebuild the Docker image

## Troubleshooting

### Tools Not Appearing

- Verify Docker image built successfully: `docker images | grep litcal`
- Check catalog and registry files for correct formatting
- Ensure Docker Desktop MCP config files include the `litcal` tool
- Restart Claude Desktop completely

### Connection Errors

- Verify internet connectivity
- Check API status at [https://litcal.johnromanodorazio.com/api/dev](https://litcal.johnromanodorazio.com/api/dev)

### Invalid Calendar IDs

- Use `list_available_calendars` to see valid nation and diocese codes
- Nation codes must be uppercase (IT, US, NL, VA, CA)
- Diocese codes are lowercase with underscore (rome_it, boston_us)

## Data Accuracy

The Liturgical Calendar API strives for historical accuracy:

- Based on original sources (Roman Missals, Vatican decrees)
- Memorials and feast days only generated from their introduction year
- Follows Mysterii Paschalis and other liturgical documents
- Not copied from potentially inaccurate online sources

## Liturgical Grades

Events are graded by importance (0-7):

- **0** - Weekday
- **1** - Commemoration
- **2** - Optional Memorial
- **3** - Memorial
- **4** - Feast
- **5** - Feast of the Lord
- **6** - Solemnity
- **7** - Higher Solemnity (takes precedence over regular solemnities)

## Security Considerations

- No authentication required (public API)
- Running as non-root user in container
- All data is read-only
- No sensitive information handled

## License

Apache 2.0 License

## Credits

Liturgical Calendar API created and maintained by Rev. John R. D'Orazio
API Documentation: [Swagger UI](https://litcal.johnromanodorazio.com/dist)

---

**Note**: This server accesses a development API endpoint. For production use, consider using the stable API endpoint when available.

## 🙏 Mission

This MCP server is part of a broader initiative to make the liturgical, biblical, and canonical patrimony of the Church accessible to AI systems in a faithful and structured way.

> “Missionaries have always gone with Christ to new frontiers, while the Holy Spirit pushed and preceded them” (SR 17c).
> We can only regard this so-called new continent with the zeal of a Francis Xavier or a Mother Cabrini.
> — **Cardinal Michael Czerny**, [A New World and a New Mission](https://www.humandevelopment.va/content/dam/sviluppoumano/news/2024-news/09-settembre/missione-digitale/pdf/A-new-World-and-a-new-Mission.pdf)
