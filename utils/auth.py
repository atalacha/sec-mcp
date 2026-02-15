import os
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

# Define scopes
SCOPES = [
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/devstorage.read_only"
]

TOKEN_PATH = os.environ.get("TOKEN_PATH", "/app/token.json")
# We don't need CREDS_PATH in Cloud Run anymore

def get_credentials() -> Credentials:
    """Load credentials optimized for Cloud Run."""
    creds = None
    
    # 1. Check if token.json exists (Mounted via Secret Manager)
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            print(f"✅ Loaded credentials from {TOKEN_PATH}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Error loading token.json: {e}", file=sys.stderr)
            
    # 2. Check if valid
    if creds and creds.valid:
        return creds
        
    # 3. Try to refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            print("🔄 Refreshing expired token...", file=sys.stderr)
            creds.refresh(GoogleAuthRequest())
            return creds
        except Exception as e:
            print(f"❌ Failed to refresh token: {e}", file=sys.stderr)

    # 4. Fallback: If we are here, we failed.
    # In Local Dev, we would run InstalledAppFlow.
    # In Cloud Run, we must fail because we can't open a browser.
    
    # Detect if running in Cloud Run (PORT env var is set)
    if os.environ.get("PORT"):
        raise RuntimeError(
            "❌ No valid token.json found! Cloud Run cannot open a browser login. "
            "Please ensure 'mcp-google-token' secret is mounted to /app/token.json"
        )
    
    # If Local, try the flow (Requires google-auth-oauthlib)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        print("🚀 Starting Local Auth Flow...", file=sys.stderr)
        # Assuming credentials.json exists locally
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=8080)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        return creds
    except ImportError:
        raise RuntimeError("❌ Local auth requires 'google-auth-oauthlib' installed.")
    except FileNotFoundError:
        raise RuntimeError("❌ credentials.json not found for local auth.")

# Keep your service builders the same
def get_people_service(creds=None):
    from googleapiclient.discovery import build
    if not creds: creds = get_credentials()
    return build("people", "v1", credentials=creds)

def get_storage_client(creds=None):
    from google.cloud import storage
    if not creds: creds = get_credentials()
    return storage.Client(credentials=creds)
