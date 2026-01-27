"""Tests para ResponseApiError"""
import pytest
import httpx
from unittest.mock import AsyncMock
from devex_mcp.libs.ResponseApiError import ResponseApiErrors


class TestResponseApiErrors:
    """Test suite para el formateador de errores"""
    
    def test_format_http_status_error(self):
        """Test que format_error maneja HTTPStatusError correctamente"""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Service not found in registry"
        
        error = httpx.HTTPStatusError(
            "Not Found",
            request=AsyncMock(),
            response=mock_response
        )
        
        result = ResponseApiErrors.format_error(error)
        
        assert "content" in result
        assert isinstance(result["content"], list)
        assert result["content"][0]["type"] == "text"
        assert "HTTP Error 404" in result["content"][0]["text"]
        assert "Service not found" in result["content"][0]["text"]
    
    def test_format_http_status_error_truncates_long_response(self):
        """Test que format_error trunca respuestas HTTP muy largas"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Error: " + "X" * 200  # Texto muy largo
        
        error = httpx.HTTPStatusError(
            "Internal Server Error",
            request=AsyncMock(),
            response=mock_response
        )
        
        result = ResponseApiErrors.format_error(error)
        
        # Debe truncar a 100 caracteres
        assert len(result["content"][0]["text"]) < len(mock_response.text)
        assert "HTTP Error 500" in result["content"][0]["text"]
    
    def test_format_timeout_error(self):
        """Test que format_error maneja TimeoutException correctamente"""
        error = httpx.TimeoutException("Request timed out")
        
        result = ResponseApiErrors.format_error(error)
        
        assert "content" in result
        assert result["content"][0]["type"] == "text"
        assert "Timeout Error" in result["content"][0]["text"]
        assert "API took too long" in result["content"][0]["text"]
    
    def test_format_connection_error(self):
        """Test que format_error maneja ConnectError correctamente"""
        error = httpx.ConnectError("Cannot connect to host")
        
        result = ResponseApiErrors.format_error(error)
        
        assert "content" in result
        assert result["content"][0]["type"] == "text"
        assert "Connection Error" in result["content"][0]["text"]
        assert "Cannot reach API" in result["content"][0]["text"]
    
    def test_format_generic_exception(self):
        """Test que format_error maneja excepciones genéricas correctamente"""
        error = ValueError("Invalid microservice name format")
        
        result = ResponseApiErrors.format_error(error)
        
        assert "content" in result
        assert result["content"][0]["type"] == "text"
        assert "Unexpected Error" in result["content"][0]["text"]
        assert "ValueError" in result["content"][0]["text"]
        assert "Invalid microservice name" in result["content"][0]["text"]
    
    def test_format_error_returns_correct_structure(self):
        """Test que format_error siempre retorna la estructura MCP correcta"""
        errors = [
            httpx.TimeoutException("timeout"),
            httpx.ConnectError("connect"),
            ValueError("value"),
            RuntimeError("runtime")
        ]
        
        for error in errors:
            result = ResponseApiErrors.format_error(error)
            
            # Verificar estructura MCP
            assert isinstance(result, dict)
            assert "content" in result
            assert isinstance(result["content"], list)
            assert len(result["content"]) > 0
            assert "type" in result["content"][0]
            assert "text" in result["content"][0]
            assert result["content"][0]["type"] == "text"
            assert isinstance(result["content"][0]["text"], str)
    
    def test_format_error_with_different_http_codes(self):
        """Test que format_error maneja diferentes códigos HTTP"""
        status_codes = [400, 401, 403, 404, 500, 502, 503]
        
        for code in status_codes:
            mock_response = AsyncMock()
            mock_response.status_code = code
            mock_response.text = f"Error {code}"
            
            error = httpx.HTTPStatusError(
                f"HTTP {code}",
                request=AsyncMock(),
                response=mock_response
            )
            
            result = ResponseApiErrors.format_error(error)
            
            if code in (401, 403):
                assert f"Authentication Error {code}" in result["content"][0]["text"]
            else:
                assert f"HTTP Error {code}" in result["content"][0]["text"]
