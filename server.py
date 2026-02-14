# server.py
from utils.auth import get_credentials, get_people_service, get_storage_client

def main():
    print("--- STARTING OAUTH TEST ---")
    
    # 1. Test Credentials
    print("1. Attempting to get credentials...")
    try:
        creds = get_credentials()
        print("✅ SUCCESS: Credentials obtained.")
        print(f"   Scopes: {creds.scopes}")
    except Exception as e:
        print(f"❌ FAILED to get credentials: {e}")
        return

    # 2. Test People API Connection
    print("\n2. Building People Service...")
    try:
        people_service = get_people_service(creds)
        print("✅ SUCCESS: People Service built successfully.")
    except Exception as e:
        print(f"❌ FAILED to build People Service: {e}")

    # 3. Test GCS Connection
    print("\n3. Building Storage Client...")
    try:
        storage_client = get_storage_client(creds)
        print("✅ SUCCESS: Storage Client built successfully.")
    except ImportError:
        print("⚠️ SKIPPED: 'google-cloud-storage' library not found. Run: uv pip install google-cloud-storage")
    except Exception as e:
        print(f"❌ FAILED to build Storage Client: {e}")

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    main()
