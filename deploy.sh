#!/bin/bash

# --- Configuration ---
PROJECT_ID="careful-hangar-483408-m3"  # CHANGE THIS!
SERVICE_NAME="sec-mcp"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# --- 1. Build & Submit Docker Image ---
echo "🔨 Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME .

# --- 2. Deploy to Cloud Run ---
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --max-instances 5 \
  --min-instances 0 \
  --memory 512Mi \
  --cpu 1 \
  --set-secrets="/secrets/token.json=mcp-google-token:latest" \
  --set-env-vars="TOKEN_PATH=/secrets/token.json" \
  --project $PROJECT_ID

echo "✅ Done! Your URL is:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
