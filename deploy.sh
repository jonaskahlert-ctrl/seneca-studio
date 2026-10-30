#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-your-gcp-project-id}"
PROJECT_NUMBER="${PROJECT_NUMBER:-123456789012}"
REGION="${REGION:-europe-west1}"
SKILL_LOCATION="${SKILL_LOCATION:-europe-west4}"
VERTEX_LOCATION="${VERTEX_LOCATION:-europe-west4}"
SERVICE_NAME="${SERVICE_NAME:-seneca-studio}"
AGENT_ID="${AGENT_ID:-seneca-studio-agent}"

echo "Deploying ${SERVICE_NAME} to Cloud Run (${REGION}) in project ${PROJECT_ID}..."

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --platform managed \
  --ingress all \
  --no-allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},PROJECT_NUMBER=${PROJECT_NUMBER},SKILL_LOCATION=${SKILL_LOCATION},VERTEX_LOCATION=${VERTEX_LOCATION},AGENT_ID=${AGENT_ID}" \
  --quiet
