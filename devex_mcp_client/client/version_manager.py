import sys
import logging
import httpx


CLIENT_VERSION = "1.0.3"

# Configure logger
logger = logging.getLogger("devex_client")

def check_for_update(e: Exception):
    """
    Checks if the exception is a 426 Upgrade Required error.
    If so, it logs a message and exits the process to trigger an auto-update.
    """
    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 426:
        try:
            data = e.response.json()
            msg = data.get("message", "New version detected! Restarting to update...")
            logger.warning(f"♻️ {msg}")
        except Exception:
            logger.warning("♻️ New version detected! Restarting to update...")
            
        sys.exit(1)
