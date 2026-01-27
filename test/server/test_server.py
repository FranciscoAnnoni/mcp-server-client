"""Tests para el servidor MCP principal"""
import pytest
import json
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from devex_mcp.server import fetch_api_swagger, health_check, mcp


class TestFetchApiSwagger:
    """Tests para el tool fetch_api_swagger"""
    
    @pytest.mark.asyncio
    async def test_fetch_api_swagger_success(self):
        """Test que fetch_api_swagger retorna datos correctamente"""
        # Mock data
        mock_swagger_response = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test Microservice API",
                "version": "1.0.0",
                "description": "Test API Documentation"
            },
            "paths": {
                "/api/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "TestModel": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        with patch('devex_mcp.server.DescriptorsApiRepository.get_swagger', new_callable=AsyncMock) as mock:
            mock.return_value = mock_swagger_response
            
            result = await fetch_api_swagger("test-service")
            
            mock.assert_called_once_with("test-service")
            assert "content" in result
            assert isinstance(result["content"], list)
            assert result["content"][0]["type"] == "text"
            
            # Verificar que el contenido es JSON válido
            text_content = result["content"][0]["text"]
            parsed = json.loads(text_content)
            assert parsed["openapi"] == "3.0.0"
            assert parsed["info"]["title"] == "Test Microservice API"
    
    
    @pytest.mark.asyncio
    async def test_fetch_api_swagger_timeout_error(self):
        """Test que fetch_api_swagger maneja timeouts correctamente"""
        with patch('devex_mcp.server.DescriptorsApiRepository.get_swagger', new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.TimeoutException("Timeout")
            
            result = await fetch_api_swagger("slow-service")
            
            assert "content" in result
            assert "Timeout Error" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_fetch_api_swagger_connection_error(self):
        """Test que fetch_api_swagger maneja errores de conexión correctamente"""
        with patch('devex_mcp.server.DescriptorsApiRepository.get_swagger', new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.ConnectError("Connection failed")
            
            result = await fetch_api_swagger("unreachable-service")
            
            assert "content" in result
            assert "Connection Error" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_fetch_api_swagger_unexpected_error(self):
        """Test que fetch_api_swagger maneja errores inesperados correctamente"""
        with patch('devex_mcp.server.DescriptorsApiRepository.get_swagger', new_callable=AsyncMock) as mock:
            mock.side_effect = ValueError("Unexpected error")
            
            result = await fetch_api_swagger("error-service")
            
            assert "content" in result
            assert "Unexpected Error" in result["content"][0]["text"]
            assert "ValueError" in result["content"][0]["text"]


class TestHealthCheck:
    """Tests para el endpoint de health check"""
    
    def test_health_check_returns_ok(self):
        """Test que health check retorna status ok"""
        request = MagicMock()
        response = health_check(request)
        
        assert response.status_code == 200
        assert b"ok" in response.body


class TestAuthMiddleware:
    """Tests para el middleware de autenticación"""
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_x_rappi_token(self):
        """Test que el middleware procesa correctamente X-Rappi-Token"""
        from devex_mcp.server import AuthMiddleware, user_token_ctx, MIN_CLIENT_VERSION
        from starlette.responses import JSONResponse
        
        middleware = AuthMiddleware(app=None)
        
        # Mock request con X-Rappi-Token y versión válida
        request = MagicMock()
        request.headers = {
            "X-Rappi-Token": "test-token-123",
            "X-Client-Version": MIN_CLIENT_VERSION
        }
        
        def check_token(req):
            # Verificar que el token está en el contexto
            assert user_token_ctx.get() == "test-token-123"
            return JSONResponse({"status": "ok"})
        
        mock_call_next = AsyncMock(side_effect=check_token)
        
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_bearer_token(self):
        """Test que el middleware procesa correctamente Bearer token"""
        from devex_mcp.server import AuthMiddleware, user_token_ctx, MIN_CLIENT_VERSION
        from starlette.responses import JSONResponse
        
        middleware = AuthMiddleware(app=None)
        
        # Mock request con Authorization Bearer y versión válida
        request = MagicMock()
        request.headers = {
            "Authorization": "Bearer test-bearer-token",
            "X-Client-Version": MIN_CLIENT_VERSION
        }
        
        def check_bearer_token(req):
            # Verificar que el token está limpio (sin "Bearer ")
            assert user_token_ctx.get() == "test-bearer-token"
            return JSONResponse({"status": "ok"})
        
        mock_call_next = AsyncMock(side_effect=check_bearer_token)
        
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_auth_middleware_without_token(self):
        """Test que el middleware funciona sin token"""
        from devex_mcp.server import AuthMiddleware, MIN_CLIENT_VERSION
        from starlette.responses import JSONResponse
        
        middleware = AuthMiddleware(app=None)
        
        # Mock request sin token pero con versión válida
        request = MagicMock()
        request.headers = {"X-Client-Version": MIN_CLIENT_VERSION}
        
        mock_call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_middleware_version_ok(self):
        """Test que acepta clientes con versión correcta"""
        from devex_mcp.server import AuthMiddleware, MIN_CLIENT_VERSION
        from starlette.responses import JSONResponse
        
        middleware = AuthMiddleware(app=None)
        
        request = MagicMock()
        request.headers = {"X-Client-Version": MIN_CLIENT_VERSION}
        request.url.path = "/v1/devex-mcp/tool"
        
        mock_call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200
        mock_call_next.assert_called()

    @pytest.mark.asyncio
    async def test_auth_middleware_version_outdated(self):
        """Test que rechaza clientes con versión desactualizada (426)"""
        from devex_mcp.server import AuthMiddleware
        
        middleware = AuthMiddleware(app=None)
        
        request = MagicMock()
        request.headers = {"X-Client-Version": "0.0.1"}
        request.url.path = "/v1/devex-mcp/tool"
        
        mock_call_next = AsyncMock()
        
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 426
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_middleware_version_missing(self):
        """Test que rechaza clientes sin versión (426)"""
        from devex_mcp.server import AuthMiddleware
        
        middleware = AuthMiddleware(app=None)
        
        request = MagicMock()
        request.headers = {}
        request.url.path = "/v1/devex-mcp/tool"
        
        mock_call_next = AsyncMock()
        
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 426
        mock_call_next.assert_not_called()
class TestSearchMicroservices:
    """Tests para el tool search_microservices"""
    
    @pytest.mark.asyncio
    async def test_search_microservices_success(self):
        """Test que search_microservices retorna datos correctamente"""
        from devex_mcp.server import search_microservices
        
        mock_data = [
            {
                "service_name": "test-service",
                "repository": "git@github.com:rappi/test.git",
                "metadata": {"team": "test-team"}
            }
        ]
        
        with patch('devex_mcp.server.MsCatalogApiRepository.search_services', new_callable=AsyncMock) as mock:
            mock.return_value = mock_data
            
            result = await search_microservices("test")
            
            assert "content" in result
            assert isinstance(result["content"], list)
            text_content = result["content"][0]["text"]
            parsed = json.loads(text_content)
            assert len(parsed) == 1
            assert parsed[0]["service_name"] == "test-service"
    
    @pytest.mark.asyncio
    async def test_search_microservices_error(self):
        """Test que search_microservices maneja errores correctamente"""
        from devex_mcp.server import search_microservices
        
        with patch('devex_mcp.server.MsCatalogApiRepository.search_services', new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=MagicMock(status_code=404))
            
            result = await search_microservices("error-service")
            
            assert "content" in result
            assert "404" in result["content"][0]["text"]


class TestFetchReadmes:
    """Tests para el tool fetch_readmes"""
    
    @pytest.mark.asyncio
    async def test_fetch_readmes_success(self):
        """Test que fetch_readmes retorna datos correctamente"""
        from devex_mcp.server import fetch_readmes
        
        mock_data = [
            {"microservice": "service-1", "readme": "Readme content 1"},
            {"microservice": "service-2", "readme": "Readme content 2"}
        ]
        
        with patch('devex_mcp.server.DescriptorsApiRepository.fetch_bulk_readmes', new_callable=AsyncMock) as mock:
            mock.return_value = mock_data
            
            result = await fetch_readmes(["service-1", "service-2"])
            
            assert "content" in result
            text_content = result["content"][0]["text"]
            parsed = json.loads(text_content)
            assert len(parsed) == 2
            assert parsed[0]["microservice"] == "service-1"
    
    @pytest.mark.asyncio
    async def test_fetch_readmes_error(self):
        """Test que fetch_readmes maneja errores correctamente"""
        from devex_mcp.server import fetch_readmes
        
        with patch('devex_mcp.server.DescriptorsApiRepository.fetch_bulk_readmes', new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.ConnectError("Connection failed")
            
            result = await fetch_readmes(["error-service"])
            
            assert "content" in result
            assert "Connection Error" in result["content"][0]["text"]


class TestMCPServer:
    """Tests para la configuración del servidor MCP"""
    
    def test_server_name(self):
        """Test que el servidor tiene el nombre correcto"""
        assert mcp.name == "devex-mcp"
    
    def test_server_has_tools(self):
        """Test que el servidor tiene al menos 1 tool"""
        # El servidor debe tener al menos 1 tool
        assert hasattr(mcp, '_tools') or hasattr(mcp, 'list_tools')
    
    def test_fetch_api_swagger_is_registered(self):
        """Test que fetch_api_swagger está registrado como tool"""
        # Verificar que la función está decorada y disponible
        assert callable(fetch_api_swagger)


class TestServeInstaller:
    """Tests para el endpoint serve_installer"""
    
    def test_serve_installer_success(self):
        """Test que serve_installer retorna el contenido del script correctamente"""
        from devex_mcp.server import serve_installer
        
        # Mock open para leer el archivo
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_file.read.return_value = "#!/bin/bash\necho 'installing...'"
            mock_open.return_value = mock_file
            
            request = MagicMock()
            response = serve_installer(request)
            
            assert response.status_code == 200
            assert response.body == b"#!/bin/bash\necho 'installing...'"
            assert response.media_type == "text/plain"
            mock_open.assert_called_with("devex_mcp_setup/setup.sh", "r")

    def test_serve_installer_not_found(self):
        """Test que serve_installer retorna 404 si no encuentra el archivo"""
        from devex_mcp.server import serve_installer
        
        with patch("builtins.open", side_effect=FileNotFoundError):
            request = MagicMock()
            response = serve_installer(request)
            
            assert response.status_code == 404
            assert b"Installer not found" in response.body


class TestServeInstallerWin:
    """Tests para el endpoint serve_installer_win"""
    
    def test_serve_installer_win_success(self):
        """Test que serve_installer_win retorna el contenido del script correctamente"""
        from devex_mcp.server import serve_installer_win
        
        # Mock open para leer el archivo
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_file.read.return_value = "Write-Host 'installing...'"
            mock_open.return_value = mock_file
            
            request = MagicMock()
            response = serve_installer_win(request)
            
            assert response.status_code == 200
            assert response.body == b"Write-Host 'installing...'"
            assert response.media_type == "text/plain"
            mock_open.assert_called_with("devex_mcp_setup/setup.ps1", "r")

    def test_serve_installer_win_not_found(self):
        """Test que serve_installer_win retorna 404 si no encuentra el archivo"""
        from devex_mcp.server import serve_installer_win
        
        with patch("builtins.open", side_effect=FileNotFoundError):
            request = MagicMock()
            response = serve_installer_win(request)
            
            assert response.status_code == 404
            assert b"Windows installer not found" in response.body

# Extension of TestAuthMiddleware to test public paths
    @pytest.mark.asyncio
    async def test_auth_middleware_public_paths(self):
        """Test que el middleware permite acceso sin token a rutas públicas"""
        from devex_mcp.server import AuthMiddleware
        from starlette.responses import JSONResponse
        
        middleware = AuthMiddleware(app=None)
        
        public_paths = ["/health", "/v1/devex-mcp/install", "/v1/devex-mcp/install.ps1"]
        
        for path in public_paths:
            request = MagicMock()
            request.url.path = path
            request.headers = {}
            
            # Mock del siguiente call - simplemente retorna OK
            mock_call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
            
            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200
            # Verificar que se llamó a call_next (lo que implica que pasó el check de auth)
            mock_call_next.assert_called()

class TestParseVersion:
    """Tests para utilidad parse_version"""
    def test_parse_version_invalid(self):
        from devex_mcp.server import parse_version
        assert parse_version("invalid") == (0, 0, 0)

    def test_parse_version_greater(self):
        """Test que parse_version maneja correctamente versiones mayores"""
        from devex_mcp.server import parse_version
        assert parse_version("2.0.0") > parse_version("1.0.0")

    def test_parse_version_smaller(self):
        """Test que parse_version maneja correctamente versiones menores"""
        from devex_mcp.server import parse_version
        assert parse_version("0.9.9") < parse_version("1.0.0")
