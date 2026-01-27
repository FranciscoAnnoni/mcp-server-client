"""Tests para MsCatalogApiRepository"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from devex_mcp.repositories.MsCatalogApiRepository import MsCatalogApiRepository

class TestMsCatalogApiRepository:
    """Test suite para el repositorio de Microservice Catalog API"""
    
    @pytest.mark.asyncio
    async def test_search_services_success(self):
        """Test que search_services retorna datos correctamente cuando la API responde OK"""
        mock_response_data = [
            {
                "service_name": "test-service",
                "repository": "git@github.com:rappi/test-service.git",
                "service_metadata": {"area": "test", "team": "test-team", "tier": 1}
            }
        ]
        
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = await MsCatalogApiRepository.search_services("test-service")
            
            assert len(results) == 1
            assert results[0]["service_name"] == "test-service"
            assert results[0]["repository"] == "git@github.com:rappi/test-service.git"
            assert results[0]["metadata"]["area"] == "test"

    @pytest.mark.asyncio
    async def test_search_services_normalization(self):
        """Test que search_services normaliza el input correctamente"""
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            await MsCatalogApiRepository.search_services("Test Service ")
            
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["service_name"] == "test-service"

    @pytest.mark.asyncio
    async def test_search_services_error(self):
        """Test que search_services propaga errores HTTP"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        error = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=mock_response
        )
        
        async def async_get(*args, **kwargs):
            raise error
            
        mock_client = MagicMock()
        mock_client.get = async_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await MsCatalogApiRepository.search_services("error-service")

    @pytest.mark.asyncio
    async def test_search_services_with_token(self):
        """Test que search_services usa el token del contexto cuando está disponible"""
        from devex_mcp.repositories.MsCatalogApiRepository import user_token_ctx
        
        mock_response_data = [{"service_name": "test", "repository": "repo", "service_metadata": {}}]
        
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Setear token en el contexto
        token = user_token_ctx.set("test-token-123")
        
        try:
            with patch('httpx.AsyncClient', return_value=mock_client):
                await MsCatalogApiRepository.search_services("test")
                
                # Verificar que el header Authorization fue incluido
                call_args = mock_client.get.call_args
                assert "headers" in call_args[1]
                assert call_args[1]["headers"]["Authorization"] == "Bearer test-token-123"
        finally:
            # Limpiar el contexto
            user_token_ctx.reset(token)
