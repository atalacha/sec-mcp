from typing import Any, Dict
from .base import BaseTool

class GetFileFromGCS(BaseTool):
    name = "get_file_from_gcs"
    description = "Reads the content of a file from Google Cloud Storage."
    
    input_schema = {
        "type": "object",
        "properties": {
            "bucket_name": {"type": "string", "description": "Name of the GCS bucket"},
            "blob_name": {"type": "string", "description": "Path/Name of the file"}
        },
        "required": ["bucket_name", "blob_name"]
    }

    def __init__(self, storage_client):
        self.client = storage_client  # Store the authenticated client

    async def run(self, arguments: Dict[str, Any]) -> str:
        try:
            bucket = self.client.bucket(arguments["bucket_name"])
            blob = bucket.blob(arguments["blob_name"])
            
            # Download as text
            content = blob.download_as_text()
            return content
        except Exception as e:
            return f"Error reading GCS file: {str(e)}"
