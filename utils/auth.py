import os.path
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 1. Update Scopes to include EVERYTHING you need (Contacts + Storage)
SCOPES = [
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/devstorage.read_only" # Added for GCS
]

TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")
CREDS_PATH = os.environ.get("CREDS_PATH", "credentials.json")

def get_credentials() -> Credentials:
    """Load or refresh Google OAuth2 credentials."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
            
    return creds

def get_people_service(creds=None):
    """Return an authenticated People API service."""
    if not creds:
        creds = get_credentials()
    return build("people", "v1", credentials=creds)

# You can add this for your GCS tool later
def get_storage_client(creds=None):
    from google.cloud import storage
    if not creds:
        creds = get_credentials()
    return storage.Client(credentials=creds)
