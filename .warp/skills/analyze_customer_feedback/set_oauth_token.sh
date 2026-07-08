#!/usr/bin/env bash
# Sets GOOGLE_OAUTH_TOKEN from gcloud Application Default Credentials.
#
# Usage:
#   source set_oauth_token.sh
#
# Prerequisites:
#   gcloud auth application-default login --project=your-gcp-project-id

ADC_PATH="${HOME}/.config/gcloud/application_default_credentials.json"

if [ ! -f "$ADC_PATH" ]; then
  echo "Error: No ADC credentials found at $ADC_PATH" >&2
  echo "Run: gcloud auth application-default login --project=your-gcp-project-id" >&2
  return 1 2>/dev/null || exit 1
fi

export GOOGLE_OAUTH_TOKEN
GOOGLE_OAUTH_TOKEN=$(cat "$ADC_PATH")
echo "GOOGLE_OAUTH_TOKEN set from $ADC_PATH"
