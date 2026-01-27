import asyncio
import httpx
import logging
import sys
from typing import Any, List
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource



from .auth_manager import AuthManager, AuthenticationError
from .version_manager import check_for_update, CLIENT_VERSION

logger = logging.getLogger("devex_client")

MAX_RETRIES = 3
BASE_DELAY = 2  # seconds

async def run_bridge_session(url: str, auth_manager: AuthManager):
    """
    Runs a session. If the token expires, this function will fail and allow
    the main loop to re-authenticate.
    """
    # 1. Get Fresh Token
    try:
        token = await auth_manager.get_token()
        logger.info("🔑 Token obtained/refreshed successfully.")
    except Exception as e:
        check_for_update(e)
        raise e 

    headers = {
        "X-Rappi-Token": token,
        "X-Client-Version": CLIENT_VERSION
    }

    # 2. Connect
    try:
        async with streamablehttp_client(url, headers=headers) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                
                remote_list = await client.list_tools()
                remote_tools = remote_list.tools
                
                # --- Local Server (Proxy) ---
                server = Server("devex-mcp-bridge")

                @server.list_tools()
                async def list_tools() -> List[Tool]:
                    return remote_tools

                @server.call_tool()
                async def call_tool(name: str, arguments: Any) -> List[TextContent | ImageContent | EmbeddedResource]:
                    try:
                        result = await client.call_tool(name, arguments)
                        return result.content
                    except httpx.HTTPStatusError as e:
                        check_for_update(e)
                        if e.response.status_code == 401:
                            logger.warning("⚠️ Expired token detected during tool use (401).")
                            raise ConnectionAbortedError("TokenExpired")
                        raise e
                    except Exception as e:
                        check_for_update(e)
                        raise e

                # Start the stdio server.
                options = server.create_initialization_options()
                async with stdio_server() as (read, write):
                    await server.run(read, write, options)

    except httpx.HTTPStatusError as e:
        check_for_update(e)
        raise e

async def run_bridge_loop(url: str):
    """
    Infinite loop that keeps the service alive and refreshes tokens.
    Exits on fatal auth errors or max retries.
    """
    auth = AuthManager()
    
    try:
        auth.ensure_credentials()
    except ValueError as e:
        logger.error(f"❌ Startup Error: {e}")
        sys.exit(1)

    retries = 0

    while True:
        start_time = asyncio.get_event_loop().time()
        try:
            await run_bridge_session(url, auth)
        
        except AuthenticationError:
            logger.error("🛑 Fatal Authentication Error. Could not authenticate with current credentials.")
            logger.error("Please run the installer again if you changed your password.")
            sys.exit(1)

        except ConnectionAbortedError:
            # Token expired, this is normal flow. Immediate retry.
            logger.info("🔄 Restarting session to refresh token...")
            retries = 0  # Reset retries for token refresh
            await asyncio.sleep(1) 
            continue 

        except Exception as e:
            uptime = asyncio.get_event_loop().time() - start_time
            if uptime > 60:
                retries = 0

            retries += 1
            if retries > MAX_RETRIES:
                 logger.error(f"❌ Max retries ({MAX_RETRIES}) exceeded. Exiting to prevent loop.")
                 sys.exit(1)
            
            # Exponential backoff: 2s, 4s, 8s, 16s, 32s
            delay = BASE_DELAY * (2 ** (retries - 1))
            logger.warning(f"⚠️ Connection failed: {e}. Retrying in {delay}s ({retries}/{MAX_RETRIES})...")
            await asyncio.sleep(delay)
 