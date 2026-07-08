#!/usr/bin/env python3
"""
Generate a read-only OAuth token for the Product Bot.

This token can only READ data from:
- Google Drive (drive.readonly)
- Google Docs (documents.readonly)
- Gmail (gmail.readonly)
- BigQuery (bigquery - queries only, no data modification)

Usage:
    python generate_readonly_token.py

The token will be saved to token.json and can be copied to GOOGLE_OAUTH_TOKEN env var.
"""

import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes for product bot - read-only except for creating docs
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',          # Create/edit files created by this app only
    'https://www.googleapis.com/auth/documents',           # Create/edit docs (needed for write_google_docs)
    'https://www.googleapis.com/auth/gmail.readonly',      # Read emails only
    'https://www.googleapis.com/auth/bigquery',            # Run queries (read-only operations)
]

CREDENTIALS_PATH = 'credentials.json'
TOKEN_PATH = 'token.json'


def main():
    print("Generating OAuth token for Product Bot...")
    print()
    print("This token will have access to:")
    print("  ✓ Google Drive (create files, edit own files only)")
    print("  ✓ Google Docs (create and edit)")
    print("  ✓ Gmail (read-only)")
    print("  ✓ BigQuery (query only)")
    print()
    print("This token CANNOT:")
    print("  ✗ Delete or modify files it didn't create")
    print("  ✗ Send or modify emails")
    print("  ✗ Modify BigQuery tables or datasets")
    print()
    
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Error: {CREDENTIALS_PATH} not found")
        print("Please download OAuth credentials from Google Cloud Console")
        return
    
    # Remove existing token to force re-auth
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)
        print(f"Removed existing {TOKEN_PATH}")
    
    # Run OAuth flow
    print("Opening browser for authentication...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save token
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())
    
    print()
    print(f"✓ Token saved to {TOKEN_PATH}")
    print()
    print("To use in a remote environment, set GOOGLE_OAUTH_TOKEN:")
    print()
    print(f"  The token is saved at: {TOKEN_PATH}")
    print("  ⚠️  WARNING: The token JSON contains live credentials (refresh_token, client_secret).")
    print("      Do NOT share it, log it, or commit it. To export for a remote environment:")
    print(f"      cat {TOKEN_PATH}")
    print("      Then set GOOGLE_OAUTH_TOKEN to that JSON value in your remote environment's secrets.")
    print()
    
    # Verify scopes
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    
    print("Token scopes:")
    for scope in token_data.get('scopes', []):
        readonly = 'readonly' in scope or scope.endswith('bigquery')
        icon = '✓' if readonly else '⚠'
        print(f"  {icon} {scope}")


if __name__ == '__main__':
    main()
