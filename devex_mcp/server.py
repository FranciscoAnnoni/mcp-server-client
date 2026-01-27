import os
from typing import List
from mcp.server.fastmcp import FastMCP
from devex_mcp.repositories.DescriptorsApiRepository import DescriptorsApiRepository
from devex_mcp.repositories.MsCatalogApiRepository import MsCatalogApiRepository, user_token_ctx
from devex_mcp.libs.ResponseApiError import ResponseApiErrors
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uvicorn
import json

DEFAULT_HTTP_PATH = "/v1/devex-mcp"
MIN_CLIENT_VERSION = "1.0.3"

mcp = FastMCP(
    "devex-mcp",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
    streamable_http_path=os.getenv("HTTP_PATH", DEFAULT_HTTP_PATH),
    stateless_http=(os.getenv("TRANSPORT") == "streamable-http")
)

import logging

logging.basicConfig(level=logging.INFO)

def serve_installer(request):
    """Sirve el script de instalación para Mac/Linux (Bash)"""
    file_path = "devex_mcp_setup/setup.sh"
    try:
        with open(file_path, "r") as f:
            content = f.read()
        return PlainTextResponse(content, media_type="text/plain")
    except FileNotFoundError:
        return JSONResponse({"error": "Installer not found"}, status_code=404)

def serve_installer_win(request):
    """Sirve el script de instalación para Windows (PowerShell)"""
    file_path = "devex_mcp_setup/setup.ps1"
    try:
        with open(file_path, "r") as f:
            content = f.read()
        return PlainTextResponse(content, media_type="text/plain")
    except FileNotFoundError:
        return JSONResponse({"error": "Windows installer not found"}, status_code=404)


def parse_version(v):
    try:
        return tuple(map(int, v.split(".")))
    except ValueError:
        return (0, 0, 0)

# Define AuthMiddleware
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        http_path = os.getenv("HTTP_PATH", DEFAULT_HTTP_PATH).rstrip("/")
        public_paths = ["/health", f"{http_path}/install", f"{http_path}/install.ps1"]
        
        if request.url.path in public_paths:
            return await call_next(request)

        # Version Check
        client_version = request.headers.get("X-Client-Version")
        if not client_version or parse_version(client_version) < parse_version(MIN_CLIENT_VERSION):
                 return JSONResponse(
                    {
                        "error": "Client outdated", 
                        "min_version": MIN_CLIENT_VERSION,
                        "message": "El cliente del DevEx-MCP se está actualizando... Por favor espere mientras reiniciamos la conexión."
                    }, 
                    status_code=426 # Upgrade Required
                )

        token = request.headers.get("X-Rappi-Token") or request.headers.get("Authorization")
        
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
            
        token_token = None
        if token:
            token_token = user_token_ctx.set(token)
        
        try:
            response = await call_next(request)
            return response
        finally:
            if token_token:
                user_token_ctx.reset(token_token)

@mcp.tool()
async def fetch_api_swagger(microservice_name: str) -> dict:
    """
    Retrieves the complete OpenAPI/Swagger specification for a specific Rappi microservice.
    
    WHEN TO USE:
    - Use this tool ONLY when you have identified the single correct microservice.
    - Essential for tasks requiring specific endpoints, payload structures, creating modules, or understanding authentication methods.

    WORKFLOW HINT:
    - This returns a large JSON. Use it to extract schemas or paths needed to answer the user's technical request.
    
    Args:
        microservice_name: The exact microservice name (e.g., 'delayed-tasks-api').
    
    Returns:
        JSON containing:
        - microservice: API title.
        - version: API version.
        - last_updated: Last modification date.
        - openapi_spec: Complete OpenAPI 3.0 specification with paths, components, and schemas.
    """
    try:
        data = await DescriptorsApiRepository.get_swagger(microservice_name)
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(data, ensure_ascii=False)
            }]
        }
        
    except Exception as e:
        return ResponseApiErrors.format_error(e)


@mcp.tool()
async def search_microservices(possible_service_name: str) -> dict:
    """
    Searches for microservices in the Rappi Microservice Catalog based on a name, partial match, or description.
    
    WHEN TO USE:
    - Use this as the FIRST step when the user's request is vague (e.g., "something for payments") or implies a domain.
    - Also use it to find the exact kebab-case name if the user provides a human-readable name (e.g., "Order History" -> "order-history").

    WORKFLOW HINT:
    - This tool returns a list of candidates. Do not assume the first result is the correct one.
    - After getting results, usually the next step is to filter the most relevant ones and call 'fetch_readmes'.

    Args:
        possible_service_name: The search term (e.g.,'order', 'payment', 'cms-gateway').
    
    Returns:
        JSON containing a list of matching microservices, where each item includes:
        - service_name: The normalized kebab-case identifier.
        - repository: Link to the code repository.
        - metadata: Object containing area, team, and tier info.
    """
    try:
        data = await MsCatalogApiRepository.search_services(possible_service_name)
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(data, ensure_ascii=False)
            }]
        }
        
    except Exception as e:
        return ResponseApiErrors.format_error(e)

@mcp.tool()
async def fetch_readmes(service_names: List[str]) -> dict:
    """
    Fetches the README files for a list of microservices to analyze their functionality in depth.
    
    WHEN TO USE:
    - Use this to disambiguate between similar services found in search (e.g., deciding between 'orders-api' and 'orders-worker').
    - Use directly if the user asks "What does X service do?" or "How to use X?".

    WORKFLOW HINT:
    - TOKEN SAVING: Do not fetch readmes for ALL search results. Select only the top 3-5 most promising candidates from the previous step.
    - This content helps you decide which single microservice is the correct target for implementation.

    Args:
        service_names: A list of exact microservice names to fetch.
        
    Returns:
        JSON containing a list of objects, each with:
        - microservice: The name of the service.
        - readme: The full or truncated content of the README file.
    """
    try:
        data = await DescriptorsApiRepository.fetch_bulk_readmes(service_names)
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(data, ensure_ascii=False)
            }]
        }
        
    except Exception as e:
        return ResponseApiErrors.format_error(e)

def health_check(request):
    return JSONResponse({"status": "ok", "service": "devex-mcp-server"})

if __name__ == "__main__": # pragma: no cover 
    transport = os.getenv("TRANSPORT", "stdio")
    
    if transport == "streamable-http":
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        http_path = os.getenv("HTTP_PATH", DEFAULT_HTTP_PATH)
        
        # creacion del seridor mcp
        mcp_app = mcp.streamable_http_app()
        mcp_app.add_middleware(AuthMiddleware)
        
        mcp_app.routes.insert(0, Route(f"{http_path.rstrip('/')}/install", endpoint=serve_installer, methods=["GET"]))
        mcp_app.routes.insert(0, Route(f"{http_path.rstrip('/')}/install.ps1", endpoint=serve_installer_win, methods=["GET"]))
        mcp_app.routes.insert(0, Route("/health", endpoint=health_check, methods=["GET"]))
        
        print(f"Server running on http://{host}:{port}")
        print(f"Health check: http://{host}:{port}/health")
        print(f"MCP endpoint: http://{host}:{port}{http_path}/")
        
        uvicorn.run(
            mcp_app,
            host=host,
            port=port,
            timeout_keep_alive=60,
            timeout_graceful_shutdown=10,
            log_level="info"
        )
    else:
        print(f"Running server with {transport} transport")
        mcp.run(transport=transport)
