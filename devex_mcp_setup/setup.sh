#!/bin/bash

# Force UTF-8 for emoji support
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' 

echo -e "${CYAN}🚀 Initializing DevEx MCP Installation...${NC}"

# 1. Install UV if not present
if ! command -v uv &> /dev/null; then
    echo -e "📦 Installing 'uv'..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

# 2. Verify UV is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ Error: 'uv' is still not found in PATH.${NC}"
    echo -e "   Please restart your terminal or run: source \$HOME/.cargo/env"
    exit 1
fi

# 3. Configure repository URLs
BRANCH="master"
SETUP_REPO_URL="git+ssh://git@github.com/rappi-inc/devex-mcp.git@${BRANCH}#subdirectory=devex_mcp_setup"
CLIENT_REPO_URL="git+ssh://git@github.com/rappi-inc/devex-mcp.git@${BRANCH}#subdirectory=devex_mcp_client"

# Export for installer to use when configuring IDE
export DEVEX_CLIENT_REPO_URL="$CLIENT_REPO_URL"

# 4. Run installer directly from repository using uvx
echo -e "🔮 Running installer from repository..."
uvx --from "$SETUP_REPO_URL" devex-mcp-installer < /dev/tty

# Check exit code and show appropriate message
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "\n${RED}❌ Installation failed or was cancelled.${NC}"
    exit $EXIT_CODE
fi