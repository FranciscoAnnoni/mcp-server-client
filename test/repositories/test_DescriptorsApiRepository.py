"""Tests para DescriptorsApiRepository"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from devex_mcp.repositories.DescriptorsApiRepository import DescriptorsApiRepository


class TestDescriptorsApiRepository:
    """Test suite para el repositorio de Descriptors API"""
    
    @pytest.mark.asyncio
    async def test_get_swagger_success(self):
        """Test que get_swagger retorna datos correctamente cuando la API responde OK"""
        mock_response_data = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/test": {"get": {"summary": "Test endpoint"}}}
        }
        
        # Crear mock de response
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        # Crear async context manager para el client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await DescriptorsApiRepository.get_swagger("test-service")
            assert result == mock_response_data
    
    @pytest.mark.asyncio
    async def test_get_swagger_http_error(self):
        """Test que get_swagger lanza HTTPStatusError cuando la API retorna error"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        error = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response
        )
        
        def async_get(*args, **kwargs):
            raise error
        
        mock_client = MagicMock()
        mock_client.get = async_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await DescriptorsApiRepository.get_swagger("non-existent-service")
    
    @pytest.mark.asyncio
    async def test_get_swagger_timeout(self):
        """Test que get_swagger lanza TimeoutException cuando la API tarda mucho"""
        def async_get(*args, **kwargs):
            raise httpx.TimeoutException("Timeout")
        
        mock_client = MagicMock()
        mock_client.get = async_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(httpx.TimeoutException):
                await DescriptorsApiRepository.get_swagger("slow-service")
    
    @pytest.mark.asyncio
    async def test_get_swagger_connection_error(self):
        """Test que get_swagger lanza ConnectError cuando no puede conectar a la API"""
        def async_get(*args, **kwargs):
            raise httpx.ConnectError("Connection failed")
        
        mock_client = MagicMock()
        mock_client.get = async_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(httpx.ConnectError):
                await DescriptorsApiRepository.get_swagger("unreachable-service")

    @pytest.mark.asyncio
    async def test_fetch_bulk_readmes_success(self):
        """Test que fetch_bulk_readmes retorna readmes correctamente"""
        service_names = ["service-1", "service-2"]
        
        # Mock responses
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {"content": {"markdown": "Readme 1"}}
        mock_response_1.raise_for_status = MagicMock()
        
        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {"content": {"markdown": "Readme 2"}}
        mock_response_2.raise_for_status = MagicMock()
        
        # Mock client.get to return different responses based on URL
        def side_effect(url, **kwargs):
            if "service-1" in url:
                return mock_response_1
            elif "service-2" in url:
                return mock_response_2
            return MagicMock(status_code=404)
            
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=side_effect)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = await DescriptorsApiRepository.fetch_bulk_readmes(service_names)
            
            assert len(results) == 2
            assert results[0]["microservice"] == "service-1"
            assert results[0]["readme"] == "Readme 1"
            assert results[1]["microservice"] == "service-2"
            assert results[1]["readme"] == "Readme 2"

    @pytest.mark.asyncio
    async def test_fetch_bulk_readmes_404(self):
        """Test que fetch_bulk_readmes maneja 404 correctamente"""
        service_names = ["non-existent"]
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = await DescriptorsApiRepository.fetch_bulk_readmes(service_names)
            
            assert len(results) == 1
            assert results[0]["microservice"] == "non-existent"
            assert results[0]["readme"] == "No README found"

    @pytest.mark.asyncio
    async def test_fetch_bulk_readmes_truncated(self):
        """Test que fetch_bulk_readmes trunca readmes largos"""
        service_names = ["long-readme"]
        long_content = "A" * 2500 # > 2000 chars
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": {"markdown": long_content}}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = await DescriptorsApiRepository.fetch_bulk_readmes(service_names)
            
            assert len(results) == 1
            assert len(results[0]["readme"]) < 2100 # 2000 + "...[truncated]"
            assert "...[truncated]" in results[0]["readme"]

    @pytest.mark.asyncio
    async def test_fetch_bulk_readmes_no_content(self):
        """Test que fetch_bulk_readmes maneja respuesta sin 'content'"""
        service_names = ["no-content"]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Sin "content"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = await DescriptorsApiRepository.fetch_bulk_readmes(service_names)
            
            assert len(results) == 1
            assert results[0]["readme"] == "No README found"

    @pytest.mark.asyncio
    async def test_fetch_bulk_readmes_no_markdown(self):
        """Test que fetch_bulk_readmes maneja 'content' sin 'markdown'"""
        service_names = ["no-markdown"]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": {}}  # content sin markdown
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = await DescriptorsApiRepository.fetch_bulk_readmes(service_names)
            
            assert len(results) == 1
            assert results[0]["readme"] == "No README found"

    @pytest.mark.asyncio
    async def test_fetch_bulk_readmes_exception(self):
        """Test que fetch_bulk_readmes maneja excepciones en fetch individual"""
        service_names = ["error-service"]
        
        def raise_error(*args, **kwargs):
            raise httpx.ConnectError("Connection failed")
        
        mock_client = MagicMock()
        mock_client.get = raise_error
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            results = await DescriptorsApiRepository.fetch_bulk_readmes(service_names)
            
            assert len(results) == 1
            assert "Error fetching README" in results[0]["readme"]
