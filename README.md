# DevEx-MCP
**Team:** core-services  
**Created by:** Francisco Annoni  
**Environment:** Shared Services (DevEX)

📚 **[Full Documentation on Confluence](https://rappidev.atlassian.net/wiki/spaces/SHS/pages/4864868376/MCP+DevEx)**

## 📖 Description

**DevEx-MCP** is the tool that connects your AI agent (GitHub Copilot, Claude, etc.) with Rappi's microservices documentation.

<img width="786" height="245" alt="Captura de pantalla 2026-01-26 a la(s) 10 43 04 p  m" src="https://github.com/user-attachments/assets/6ab98640-3963-453f-ad98-81f88e1fc195" />


This MCP (Model Context Protocol) server allows LLMs (Large Language Models) to automatically query and analyze:
- 📋 OpenAPI/Swagger specifications of microservices
- 📚 Rappi Microservices Catalog
- 📖 Service READMEs

## 🎯 Goal

**To save you time.** You no longer need to manually search for documentation or copy and paste context. This tool allows the LLM to automatically consult Swaggers, Contracts, and READMEs of microservices to understand requirements and generate the perfect function for you.

### ⚠️ Important Clarification

The MCP can only obtain information from microservices that are correctly documented.

**Your documentation is key:** By keeping it up to date, you improve the functionality of this MCP and future ecosystem tools. If your microservice is not documented or you simply don't know how to do it, check the documentation guide.

👉 **[Guide: How to correctly document microservices](https://rappidev.atlassian.net/wiki/spaces/SHS/pages/4864868376/MCP+DevEx)**

# 🚀 Installation

### Installation Steps

1. **Connect to Rappi VPN** 🔒 (dev/prod - it doesn't matter)

2. **Run the following command** in your terminal and follow the installer steps:

**macOS:**
```bash
curl https://api.platform.rappi.com/v1/devex-mcp/install | bash
```

**Windows (PowerShell):**
```powershell
irm https://api.platform.rappi.com/v1/devex-mcp/install.ps1 | iex
```

The installer will handle:
- ✅ Installing the MCP client
- ✅ Automatically configuring your IDE (VS Code, Cursor, etc.)
- ✅ Establishing the connection with the server

# 🏗️ Project Composition

This repository is mainly composed of **two main components** and an **installation module**:

## 1. 🖥️ Server (`devex_mcp/`)

The MCP server that exposes tools so that LLMs can query information about microservices.

#### Available Tools

The server provides **3 main tools**:

##### 🔍 `search_microservices`
Searches for microservices in the Rappi Catalog based on a name, partial match, or description.

**When to use:**
- As the FIRST step when the request is vague (e.g., "something for payments")
- To find the exact kebab-case name if the user provides a readable name

**Parameters:**
- `possible_service_name` (string): Search term (e.g., 'order', 'payment', 'cms-gateway')

**Returns:**
```json
{
  "service_name": "service-name",
  "repository": "https://github.com/rappi/...",
  "metadata": {
    "area": "...",
    "team": "...",
    "tier": "..."
  }
}
```

**🔐 Authentication:** Requires user token (header `X-Rappi-Token`)

---

##### 📖 `fetch_readmes`
Retrieves the README files for a list of microservices to analyze their functionality in depth.

**When to use:**
- To disambiguate between similar services found in the search
- When the user asks "What does service X do?" or "How to use X?"

**Parameters:**
- `service_names` (List[str]): List of exact microservice names

**Returns:**
```json
[
  {
    "microservice": "service-name",
    "readme": "Full or truncated content of the README"
  }
]
```

**💡 Tip:** Do not fetch READMEs for ALL search results. Select only the Top 3-5 most promising candidates.

**🔐 Authentication:** Does not require token

---

##### 📋 `fetch_api_swagger`
Retrieves the complete OpenAPI/Swagger specification for a specific Rappi microservice.

**When to use:**
- ONLY when the correct microservice has been identified
- Essential for tasks requiring specific endpoints, payload structures, or authentication methods

**Parameters:**
- `microservice_name` (string): Exact name of the microservice (e.g., 'delayed-tasks-api')

**Returns:**
```json
{
  "microservice": "API Title",
  "version": "1.0.0",
  "last_updated": "2025-11-06T12:00:00.000Z",
  "openapi_spec": {
    "openapi": "3.0.0",
    "info": { ... },
    "paths": { ... },
    "components": {
      "schemas": { ... }
    }
  }
}
```

**Included Information:**
- ✅ API Title and Version
- ✅ Last Update Date
- ✅ Complete list of endpoints with HTTP methods
- ✅ Input Parameters (query, path, body)
- ✅ Request/Response Schemas
- ✅ Response Codes (200, 400, 500, etc.)
- ✅ Data Models (schemas)

**🔐 Authentication:** Does not require token

---

## 2. 💻 Client (`devex_mcp_client/`)

The MCP client that is installed on your machine and connects with your IDE to communicate with the server.

📚 **[View full client documentation](devex_mcp_client/README.md)**

The client is responsible for:
- Establishing the connection with the MCP server
- Managing user authentication
- Keeping the session active
- Auto-updating when there are new versions

---

## 3. ⚙️ Installer (`devex_mcp_setup/`)

Auto-installation component that automatically configures the tool on users' computers.

**Installation Files:**
- `setup.sh` - Installation script for macOS/Linux
- `setup.ps1` - Installation script for Windows (PowerShell)

These scripts are automatically served from the server at:
- `https://api.platform.rappi.com/v1/devex-mcp/install` (macOS/Linux)
- `https://api.platform.rappi.com/v1/devex-mcp/install.ps1` (Windows)

---
---

# 🛠️ Development

### Prerequisites

- Python 3.10+
- `uv` (package manager)
- Docker (optional, for containerized development)

### Development Installation

```bash
# 1. Clone the repository
git clone https://github.com/rappi-inc/devex-mcp.git
cd devex-mcp

# 2. Install dependencies
uv sync

# 3. Run in development mode
uv run mcp dev devex_mcp/server.py
```

### Environment Variables

Environment variables are configured in `docker-compose.yml` for production. For local development, you can create a `.env` file:

```bash
# Transport mode (stdio for local development)
TRANSPORT=stdio
```

### Run with Docker

```bash
# Start the container
docker-compose up --build -d

# View logs
docker-compose logs -f devex-mcp

# Health check
curl http://localhost:8000/api/devex-mcp/health
```

## 🧪 Testing and Code Quality

This project meets DevEX production requirements:

- **Unit Tests**: 25 tests implemented
- **Coverage**: **100%** 🎯
- **SonarQube Configuration**: ✅

### Testing Commands

```bash
# Sync dependencies (including pytest)
uv sync --all-extras

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=devex_mcp --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html

# SonarQube Analysis
uv run pytest --cov=devex_mcp --cov-report=xml
sonar-scanner
```

## 📞 Need Help?

As always, we are available for any questions or feedback you may have:
- 💬 Ask in the team's Slack channel
- 🏷️ Mention `@platform-product-guild`

---

**Created by Francisco Annoni**
