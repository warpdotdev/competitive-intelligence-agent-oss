"""Google Docs API service for reading recent documents."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# drive = full Drive access (needed to move files into existing folders)
# documents = needed for write_google_docs skill
# gmail.readonly = read emails only
# bigquery = run queries only
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/bigquery',
]


class GoogleDocsService:
    """Service for interacting with Google Docs API."""

    def __init__(self, credentials_path: str = 'credentials.json'):
        """Initialize the service with credentials.
        
        Args:
            credentials_path: Path to the OAuth2 credentials JSON file
        """
        self.credentials_path = credentials_path
        self.creds = None
        self.docs_service = None
        self.drive_service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google API using OAuth2."""
        token_path = 'token.json'
        token_env = os.environ.get('GOOGLE_OAUTH_TOKEN')
        
        # Try loading from environment variable first (for automated environments)
        if token_env:
            try:
                token_info = json.loads(token_env)
                self.creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse GOOGLE_OAUTH_TOKEN: {e}")
                self.creds = None
        # Fall back to file-based token (for local development)
        elif os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If no valid credentials, refresh or let user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            elif not token_env:
                # Only attempt interactive login if not in automated environment
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())
            else:
                raise RuntimeError(
                    "GOOGLE_OAUTH_TOKEN provided but credentials are invalid and cannot be refreshed. "
                    "Re-authenticate locally and update the token."
                )
        
        # Build service objects
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def get_recent_documents(self, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch Google Docs modified in the last N days.
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            List of document metadata dictionaries
        """
        try:
            # Calculate date threshold
            date_threshold = datetime.utcnow() - timedelta(days=days)
            date_str = date_threshold.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Query Drive API for Google Docs modified after threshold
            query = (
                f"mimeType='application/vnd.google-apps.document' "
                f"and modifiedTime > '{date_str}'"
            )
            
            documents = []
            page_token = None
            
            # Paginate through all results
            while True:
                results = self.drive_service.files().list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, modifiedTime, createdTime, webViewLink)",
                    orderBy="modifiedTime desc",
                    pageToken=page_token,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True
                ).execute()
                
                documents.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                
                if not page_token:
                    break
            
            print(f"Found {len(documents)} documents modified in the last {days} days")
            return documents
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Fetch the full content of a specific document.
        
        Args:
            document_id: The ID of the Google Doc
            
        Returns:
            Document object with content
        """
        try:
            document = self.docs_service.documents().get(
                documentId=document_id
            ).execute()
            
            return document
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {}

    def extract_text_from_document(self, document: Dict[str, Any]) -> str:
        """Extract plain text from a document object.
        
        Args:
            document: Document object from API
            
        Returns:
            Plain text content
        """
        text_content = []
        
        content = document.get('body', {}).get('content', [])
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        text_content.append(text_run['textRun']['content'])
        
        return ''.join(text_content)


def main():
    """Example usage of the Google Docs service."""
    # Initialize service
    service = GoogleDocsService()
    
    # Get documents from last week
    recent_docs = service.get_recent_documents(days=7)
    
    # Display results
    for doc in recent_docs:
        print(f"\nDocument: {doc['name']}")
        print(f"ID: {doc['id']}")
        print(f"Modified: {doc['modifiedTime']}")
        print(f"Link: {doc['webViewLink']}")
        
        # Optionally fetch and display content
        # Uncomment below to also retrieve full document content
        # document_content = service.get_document_content(doc['id'])
        # text = service.extract_text_from_document(document_content)
        # print(f"Preview: {text[:200]}...")


if __name__ == '__main__':
    main()
