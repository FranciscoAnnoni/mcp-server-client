import keyring
import httpx
import logging


SERVICE_ID = "devex-mcp-client"
AUTH_URL = "https://api.platform.rappi.com/v1/auth/authenticate"

logger = logging.getLogger("devex_auth")


class AuthenticationError(Exception):
    """Raised when authentication fails with 401/403."""
    pass


class AuthManager:
    def __init__(self):
        self.username = None
        self.password = None

    def ensure_credentials(self):
        """
        Loads credentials from keyring.
        Raises ValueError if credentials are not configured.
        
        Non-interactive - for use in background mode (Claude Desktop).
        """
        self.username = keyring.get_password(SERVICE_ID, "username")
        self.password = keyring.get_password(SERVICE_ID, "password")

        if not self.username or not self.password:
            raise ValueError(
                "No credentials configured. "
                "Please run the installer again."
            )

    async def get_token(self) -> str:
        """Gets a fresh token using saved credentials (Async)."""
        if not self.username or not self.password:
            self.ensure_credentials()
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(AUTH_URL, json={
                    "username": self.username, 
                    "password": self.password
                })
                
                if resp.status_code in (401, 403):
                    logger.warning(f"⚠️ Auth server returned {resp.status_code}. Credentials retained in keyring.")
                    raise AuthenticationError(f"Authentication failed with status {resp.status_code}")

                resp.raise_for_status()
                data = resp.json()
                
                token = data.get("AuthenticationResult", {}).get("IdToken")
                if not token:
                    raise ValueError("No IdToken received in response")
                
                return token

        except AuthenticationError:
            raise
        except httpx.HTTPError as e:
            # Network errors or other HTTP errors
            logger.error(f"HTTP error obtaining token: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error obtaining token: {e}")
            raise


