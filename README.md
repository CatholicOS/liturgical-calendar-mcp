# Liturgical Calendar MCP Server

A **Model Context Protocol (MCP)** server that exposes the [Liturgical Calendar API](https://github.com/Liturgical-Calendar/LiturgicalCalendarAPI) as a structured toolset for AI agents. This enables compliant AI systems (like ChatGPT MCP clients, LangChain agents, and custom LLM runtimes) to reason over liturgical dates, seasons, feasts, saints, and liturgical rankings with full contextual intelligence.

## 🌟 Key Features

- ✅ Fully implements the **Model Context Protocol**
- 📅 Provides **structured tool calls** to query liturgical calendar data
- 🔄 Handles communication with the upstream **Liturgical Calendar API**
- 🧠 Enables AI agents to reason about liturgical celebrations for any given day in the context of the Catholic liturgy

## 📘 What is MCP?

The **Model Context Protocol** is an emerging open standard that allows language models to interface with external tools, APIs, or data sources using a uniform schema. MCP servers expose “tools” that LLMs can discover and call programmatically.

> *This repository is an MCP server that exposes the Liturgical Calendar as a tool the AI can reason about.*

## 📚 Tech Stack

| Language | Framework/Library | Notes |
|---------|-------------------|-------|
| **Python** | FastAPI with MCP wrapper | Good for data-heavy or scientific workloads |

## 🔧 Getting Started

### 📦 Prerequisites

- Python 3.12+
- An MCP-enabled AI client

### 🚀 Development

If you don't have Python 3.12+ installed, there are a few ways to install it.

- Download and install from [python.org](https://www.python.org/downloads/)

- Use your system package manager, e.g. `sudo apt install python3.12` on Debian/Ubuntu.
  If you're on macOS, use `brew install python@3.12`.
  If the package is not available for your Debian/Ubuntu distribution, you can add the deadsnakes PPA:

  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update
  sudo apt install python3.12
  ```

- [pyenv](https://github.com/pyenv/pyenv) - a tool for managing multiple versions of Python on a system.

Once you have Python 3.12+ installed and ready, you can clone the repository and set up the virtual environment:

```bash
git clone https://github.com/YourOrg/Liturgical-Calendar-MCP.git
cd Liturgical-Calendar-MCP
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To run the server:

```bash
python main.py
```
