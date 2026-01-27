import sys
import logging
import typer
import asyncio
import keyring
from typing import Optional
from . import bridge
from .auth_manager import SERVICE_ID 
from .version_manager import CLIENT_VERSION



# Logging configuration for stderr (safe for MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    stream=sys.stderr 
)

app = typer.Typer(no_args_is_help=True)

@app.command()
def start(mcp_url: str = typer.Option("https://api.platform.rappi.com/v1/devex-mcp", envvar="MCP_URL")):
    """
    Command used by Claude Desktop. Non-interactive.
    """
    if not keyring.get_password(SERVICE_ID, "username"):
        logging.error("❌ NO CREDENTIALS CONFIGURED.")
        logging.error("Please run the installer again.")
        sys.exit(1)

    try:
        asyncio.run(bridge.run_bridge_loop(mcp_url))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    app()