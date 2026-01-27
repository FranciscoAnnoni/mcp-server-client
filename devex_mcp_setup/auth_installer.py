import keyring
import getpass
import httpx
import time

SERVICE_ID = "devex-mcp-client"
AUTH_URL = "https://api.platform.rappi.com/v1/auth/authenticate"

class AuthManager:
    """
    Authentication manager for installation.
    Only responsible for initial credential setup.
    """
    
    def _validate_credentials(self, username: str, password: str) -> tuple[bool, str]:
        """
        Validates credentials by attempting to obtain a token.
        Returns (success, error_message)
        
        Includes automatic retry logic to handle cold start connection issues.
        """
        max_retries = 2
        last_error = ""
        
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(AUTH_URL, json={
                        "username": username,
                        "password": password
                    })
                    resp.raise_for_status()
                    data = resp.json()
                    
                    token = data.get("AuthenticationResult", {}).get("IdToken")
                    if not token:
                        return False, "No authentication token received in response"
                    
                    return True, ""
                    
            except httpx.TimeoutException as e:
                last_error = "Connection timeout. Are you connected to Rappi VPN?"
            except httpx.ConnectError as e:
                last_error = "Could not connect to server. Check your internet connection and Rappi VPN."
            except httpx.HTTPStatusError as e:
                # Don't retry on authentication errors (401/403)
                if e.response.status_code in [401, 403]:
                    return False, "Invalid credentials. Verify your username and password."
                last_error = f"Server error (code {e.response.status_code})"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries - 1:
                time.sleep(1)
        
        # All retries failed
        return False, f"{last_error} (tried {max_retries} times)"
    
    def setup_credentials(self) -> bool:
        """
        Prompts user for credentials interactively, validates them, and saves to keyring.
        Returns True if saved successfully, False otherwise.
        
        ONLY for use during installation.
        """
        print("\n🔒 DevEx MCP Credentials Setup")
        print("-----------------------------------------------")
        print("Your credentials will be securely stored in your OS keyring.")
        print("(⚠️ Please ensure you are connected to the VPN for this to work.)")
        
        while True:
            username = input("\nDevEx Username (Email without @rappi.com): ").strip()
            if not username:
                print("❌ Username cannot be empty.")
                continue
                
            password = getpass.getpass("DevEx Password: ").strip()
            if not password:
                print("❌ Password cannot be empty.")
                continue

            # Validate credentials
            print("🔄 Validating credentials...")
            valid, error = self._validate_credentials(username, password)
            
            if not valid:
                print(f"\n❌ Validation error: {error}")
                
                print("\n💡 Suggestions:")
                print("   • Verify your username and password are correct")
                print("   • Make sure you're connected to Rappi VPN")
                print("   • Check your internet connection")
                
                retry = input("\nDo you want to try again? (y/n): ").strip().lower()
                if retry != 'y':
                    print("⛔ Installation cancelled by user.")
                    return False
                continue
            
            # Valid credentials, save them
            try:
                keyring.set_password(SERVICE_ID, "username", username)
                keyring.set_password(SERVICE_ID, "password", password)
                print("\n✅ Credentials validated and saved successfully!")
                print("You can now configure your IDE.")
                return True
            except Exception as e:
                print(f"\n❌ Error saving to system keyring: {e}")
                print("Make sure you have access to the keyring (Keychain/Credential Manager).")
                return False

