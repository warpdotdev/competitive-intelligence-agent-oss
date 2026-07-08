#!/usr/bin/env python3
"""Fetch feedback emails from Gmail (address configured via FEEDBACK_EMAIL)."""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# OAuth scopes - need gmail.readonly to read emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly'
]

# Feedback inbox address to filter on. Set FEEDBACK_EMAIL in your environment
# (see .env.example); no address is hardcoded.
FEEDBACK_EMAIL = os.environ.get('FEEDBACK_EMAIL', '').strip()

# Path configuration - credentials are in project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_PATH = os.path.join(SCRIPT_DIR, 'gmail_token.json')  # Separate token for Gmail


class GmailFeedbackService:
    """Service for fetching feedback emails from Gmail."""

    def __init__(self):
        """Initialize the Gmail service with OAuth2 credentials."""
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        # Use same env var as google_docs_service for consistency
        token_env = os.environ.get('GOOGLE_OAUTH_TOKEN')
        
        # Try loading from environment variable first (for automated environments)
        if token_env:
            try:
                token_info = json.loads(token_env)
                self.creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse GOOGLE_OAUTH_TOKEN: {e}", file=sys.stderr)
                self.creds = None
        # Fall back to file-based token
        elif os.path.exists(TOKEN_PATH):
            self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
        # If no valid credentials, refresh or let user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            elif not token_env:
                if not os.path.exists(CREDENTIALS_PATH):
                    print(f"Error: credentials.json not found at {CREDENTIALS_PATH}", file=sys.stderr)
                    print("Please set up OAuth credentials in Google Cloud Console.", file=sys.stderr)
                    sys.exit(1)
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES)
                self.creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(TOKEN_PATH, 'w') as token:
                    token.write(self.creds.to_json())
            else:
                raise RuntimeError(
                    "GOOGLE_OAUTH_TOKEN provided but credentials are invalid and cannot be refreshed. "
                    "Re-authenticate locally and update the token."
                )
        
        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _decode_message_body(self, payload: Dict) -> str:
        """
        Decode the message body from base64.
        
        Gmail uses URL-safe base64 encoding which needs conversion.
        """
        body = ""
        
        if 'body' in payload and payload['body'].get('data'):
            # Single part message
            data = payload['body']['data']
            # Convert URL-safe base64 to standard base64
            data = data.replace('-', '+').replace('_', '/')
            try:
                body = base64.b64decode(data).decode('utf-8')
            except Exception:
                body = "(Could not decode message body)"
        
        elif 'parts' in payload:
            # Multipart message - look for text/plain first, then text/html
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                    data = part['body']['data']
                    data = data.replace('-', '+').replace('_', '/')
                    try:
                        body = base64.b64decode(data).decode('utf-8')
                        break
                    except Exception:
                        continue
                elif 'parts' in part:
                    # Nested multipart
                    body = self._decode_message_body(part)
                    if body:
                        break
        
        return body

    def _get_header(self, headers: List[Dict], name: str) -> Optional[str]:
        """Get a header value by name."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None

    def _parse_digest_email(self, body: str, digest_date: str) -> List[Dict[str, Any]]:
        """
        Parse a Google Groups digest email to extract individual feedback messages.
        
        Digest format:
        =============================================================================
        Topic: <topic title>
        Url: <url>
        =============================================================================
        
        ---------- 1 of N ----------
        From: <sender>
        Date: <date>
        Url: <url>
        
        <message body>
        
        Args:
            body: The digest email body text
            digest_date: The date of the digest email
            
        Returns:
            List of parsed individual messages
        """
        messages = []
        
        # Split by topic sections
        topic_pattern = r'={10,}\nTopic: ([^\n]+)\nUrl: ([^\n]+)\n={10,}'
        topics = re.split(topic_pattern, body)
        
        # topics[0] is the header, then we have (topic_title, url, content) triplets
        i = 1
        while i + 2 < len(topics):
            topic_title = topics[i].strip()
            topic_url = topics[i + 1].strip()
            topic_content = topics[i + 2]
            
            # Parse individual messages within the topic
            # Format: "---------- N of M ----------\nFrom: ...\nDate: ...\nUrl: ...\n\n<body>"
            msg_pattern = r'-{10,} \d+ of \d+ -{10,}\nFrom: ([^\n]+)\nDate: ([^\n]+)\nUrl: ([^\n]+)\n\n'
            msg_parts = re.split(msg_pattern, topic_content)
            
            # msg_parts[0] is empty or whitespace, then (from, date, url, body) quadruplets
            j = 1
            while j + 3 < len(msg_parts):
                sender = msg_parts[j].strip()
                msg_date = msg_parts[j + 1].strip()
                msg_url = msg_parts[j + 2].strip()
                msg_body = msg_parts[j + 3].strip()
                
                # Clean up the body - remove quoted replies and signatures
                # Stop at "On ... wrote:" patterns (quoted text)
                on_wrote_match = re.search(r'\nOn .+wrote:\s*$', msg_body, re.MULTILINE)
                if on_wrote_match:
                    msg_body = msg_body[:on_wrote_match.start()].strip()
                
                # Skip automated messages or very short messages
                if msg_body and len(msg_body) > 10:
                    # Skip messages that are clearly automated
                    skip_patterns = [
                        r'^This is an automated',
                        r'^Thank you for contacting',
                        r'^Your subscription',
                    ]
                    is_automated = any(re.match(p, msg_body, re.IGNORECASE) for p in skip_patterns)
                    
                    if not is_automated:
                        messages.append({
                            'id': f"digest-{hash(msg_url) % 10000000}",
                            'thread_id': topic_url,
                            'from': sender,
                            'to': FEEDBACK_EMAIL,
                            'subject': topic_title,
                            'date': msg_date or digest_date,
                            'snippet': msg_body[:200],
                            'body': msg_body,
                            'labels': ['DIGEST'],
                            'source': 'digest'
                        })
                
                j += 4
            
            i += 3
        
        return messages

    def fetch_feedback_emails(self, days: int = 7, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch emails from the last N days.
        
        Parses Google Groups digest emails to extract individual feedback messages.
        
        Args:
            days: Number of days to look back (default: 7)
            max_results: Maximum number of emails to fetch (default: 100)
            
        Returns:
            List of email dictionaries (including parsed digest messages)
        """
        if not FEEDBACK_EMAIL:
            print("Error: FEEDBACK_EMAIL is not set; cannot query the feedback inbox.",
                  file=sys.stderr)
            return []

        try:
            # Calculate date for query
            after_date = datetime.now(timezone.utc) - timedelta(days=days)
            after_timestamp = int(after_date.timestamp())
            
            # Build query - filter for the configured feedback address
            # Finds emails TO, FROM, or via the list for FEEDBACK_EMAIL
            query = (
                f"after:{after_timestamp} "
                f"(to:{FEEDBACK_EMAIL} OR from:{FEEDBACK_EMAIL} OR list:{FEEDBACK_EMAIL})"
            )
            
            # List messages matching query
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            # Fetch full message details
            emails = []
            for msg_info in messages:
                try:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=msg_info['id'],
                        format='full'
                    ).execute()
                    
                    headers = msg.get('payload', {}).get('headers', [])
                    subject = self._get_header(headers, 'Subject') or ''
                    date = self._get_header(headers, 'Date') or ''
                    body = self._decode_message_body(msg.get('payload', {}))
                    
                    # Check if this is a Google Groups digest email
                    if f'Digest for {FEEDBACK_EMAIL}' in subject:
                        # Parse the digest to extract individual messages
                        parsed_messages = self._parse_digest_email(body, date)
                        emails.extend(parsed_messages)
                    else:
                        # Regular email - add as-is
                        email_data = {
                            'id': msg['id'],
                            'thread_id': msg['threadId'],
                            'from': self._get_header(headers, 'From'),
                            'to': self._get_header(headers, 'To'),
                            'subject': subject,
                            'date': date,
                            'snippet': msg.get('snippet', ''),
                            'body': body[:3000],  # Truncate long bodies
                            'labels': msg.get('labelIds', []),
                            'source': 'direct'
                        }
                        emails.append(email_data)
                    
                except HttpError as e:
                    print(f"Error fetching message {msg_info['id']}: {e}", file=sys.stderr)
                    continue
            
            return emails
            
        except HttpError as e:
            print(f"Gmail API error: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Error fetching emails: {e}", file=sys.stderr)
            return []


def fetch_gmail_feedback(days: int = 7) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch feedback emails.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of email dictionaries
    """
    service = GmailFeedbackService()
    return service.fetch_feedback_emails(days=days)


def main():
    parser = argparse.ArgumentParser(description="Fetch feedback emails from Gmail")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of emails to fetch (default: 100)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    
    args = parser.parse_args()
    
    try:
        service = GmailFeedbackService()
        emails = service.fetch_feedback_emails(days=args.days, max_results=args.max_results)
        
        if args.json:
            print(json.dumps(emails, indent=2))
        else:
            print(f"Found {len(emails)} emails from the last {args.days} days:\n")
            for email in emails:
                print(f"From: {email['from']}")
                print(f"Subject: {email['subject']}")
                print(f"Date: {email['date']}")
                print(f"Snippet: {email['snippet'][:100]}...")
                print("-" * 60)
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nTo set up Gmail API access:", file=sys.stderr)
        print("1. Enable Gmail API in Google Cloud Console", file=sys.stderr)
        print("2. Add gmail.readonly scope to your OAuth consent screen", file=sys.stderr)
        print("3. Delete any existing token file and re-authenticate", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
