"""
Repository for interacting with the Microservice Catalog API.
"""
from typing import Dict, Any, List
import httpx
import os
import logging
from contextvars import ContextVar

logger = logging.getLogger(__name__)

user_token_ctx: ContextVar[str] = ContextVar("user_token", default="")

BASE_URL = os.environ.get("MS_CATALOG_API_URL")
DEFAULT_TIMEOUT = float(os.environ.get("MS_CATALOG_API_TIMEOUT", "30.0"))


class MsCatalogApiRepository:
    """Repository for Microservice Catalog API operations."""
    
    @staticmethod
    async def search_services(service_name: str) -> List[Dict[str, Any]]:
        """
        Searches for microservices by name using the Catalog API.
        
        Args:
            service_name: The name (or partial name) of the microservice to search for.
            
        Returns:
            List[Dict]: A list of simplified microservice objects.
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        url = BASE_URL
        
         # normaliza la consulta. "Order History " -> "order-history"
        if service_name:
            service_name = service_name.strip().lower().replace(" ", "-")
            
        token = user_token_ctx.get()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            logger.warning("No user token found in context. Request may fail if auth is required.")

        params = {"service_name": service_name}
        
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            simplified_services = []
            for service in data:
                simplified_services.append({
                    "service_name": service.get("service_name"),
                    "repository": service.get("repository"),
                    "metadata": service.get("service_metadata", {})
                })
                
            return simplified_services
