"""
Repository for interacting with the Descriptors Analyzer API.
"""
from typing import Dict, Any, List
import httpx
import os
import asyncio

BASE_URL = os.environ.get("DESCRIPTORS_API_URL")
DEFAULT_TIMEOUT = float(os.environ.get("DESCRIPTORS_API_TIMEOUT", "30.0"))


class DescriptorsApiRepository:
    """Repository for Descriptors Analyzer API operations."""
    
    @staticmethod
    async def get_swagger(microservice_name: str) -> Dict[str, Any]:
        """
        Fetches the OpenAPI/Swagger documentation for a microservice.
        
        Args:
            microservice_name: The name of the microservice
            
        Returns:
            dict: Raw API response
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        url = f"{BASE_URL}/descriptors/{microservice_name}/file/openapi"
        
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def fetch_bulk_readmes(service_names: List[str]) -> List[Dict[str, str]]:
        """
        Fetches READMEs for multiple microservices in parallel using asyncio.
        
        Args:
            service_names: List of microservice names
            
        Returns:
            List of dictionaries containing microservice name and readme content
        """
        async def fetch_readme(client: httpx.AsyncClient, name: str) -> Dict[str, str]:
            url = f"{BASE_URL}/descriptors/{name}/file/readme"
            try:
                response = await client.get(url)
                
                if response.status_code == 404:
                    return {"microservice": name, "readme": "No README found"}
                    
                response.raise_for_status()
                data = response.json()
                
                content = data.get("content", {}).get("markdown", "")
                if not content:
                    return {"microservice": name, "readme": "No README found"}
                    
                if len(content) > 2000:
                    content = content[:2000] + "...[truncated]"
                    
                return {"microservice": name, "readme": content}
                
            except Exception as e:
                return {"microservice": name, "readme": f"Error fetching README: {str(e)}"}

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            tasks = [fetch_readme(client, name) for name in service_names]
            results = await asyncio.gather(*tasks)
            
        return list(results)
