"""Utility functions for formatting MCP responses."""
import httpx


class ResponseApiErrors:
    """Builder class for formatting API errors into MCP response format."""
    
    @staticmethod
    def format_error(error: Exception) -> dict:
        """
        Format exceptions into user-friendly MCP response format.
        
        Classifies errors into: HTTP errors, timeouts, connection errors, and unexpected errors.
        """
        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code
            if status in (401, 403):
                msg = f"Authentication Error {status}: Invalid or expired token. Please check your MS_CATALOG_TOKEN."
            else:
                msg = f"HTTP Error {status}: {error.response.text[:100]}"
        
        elif isinstance(error, httpx.TimeoutException):
            msg = "Timeout Error: API took too long to respond"
        
        elif isinstance(error, httpx.ConnectError):
            msg = "Connection Error: Cannot reach API"
        
        else:
            msg = f"Unexpected Error: {type(error).__name__}: {str(error)}"
        
        return {"content": [{"type": "text", "text": msg}]}
