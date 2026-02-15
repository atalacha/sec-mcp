# Troubleshooting Cloud Run Deployment & Secret Mounting

If you encounter a "Container failed to start" error or "No such file or directory" for your main script (e.g., `server.py`), follow these steps to diagnose and fix the issue.

## 1. Verify Secret Permissions
The Cloud Run service account must have permission to access the secret in Secret Manager.

**Step:** Run the following command (replace placeholders):
```bash
gcloud secrets add-iam-policy-binding [SECRET_NAME] 
  --member="serviceAccount:[PROJECT_NUMBER]-compute@developer.gserviceaccount.com" 
  --role="roles/secretmanager.secretAccessor" 
  --project [PROJECT_ID]
```
*Note: Cloud Run uses the default Compute Engine service account unless specified otherwise.*

## 2. Avoid Mounting Secrets Directly into `/app`
Mounting a single file into your application's working directory (`/app`) can "mask" or hide your code files, leading to `Errno 2: No such file or directory` errors.

**The Fix:**
1.  **Mount to a dedicated directory:** Mount secrets to `/secrets/` instead of `/app/`.
2.  **Use Environment Variables:** Tell your app where to find the file.

**Example `gcloud` command:**
```bash
--set-secrets="/secrets/token.json=mcp-google-token:latest" 
--set-env-vars="TOKEN_PATH=/secrets/token.json"
```

## 3. Update Your Application Code
Ensure your code is flexible enough to look for the token in the location defined by the environment variable.

**Example (Python):**
```python
import os
TOKEN_PATH = os.environ.get("TOKEN_PATH", "/app/token.json")

def get_credentials():
    if os.path.exists(TOKEN_PATH):
        # Load from TOKEN_PATH...
```

## 4. Debugging with Logs
If it still fails, check the logs for specific errors:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=[SERVICE_NAME]" 
  --project [PROJECT_ID] --limit 20
```

## 5. Check the Docker Build Context
If the logs say `server.py` is missing even without mounting issues:
1.  Check `.dockerignore` to ensure `server.py` isn't accidentally excluded.
2.  Check `.gcloudignore` (if using `gcloud builds submit`).
3.  Add `ls -la /app` to your `Dockerfile` temporarily to see what is actually inside the container:
    ```dockerfile
    CMD ["sh", "-c", "ls -la /app && python server.py"]
    ```
