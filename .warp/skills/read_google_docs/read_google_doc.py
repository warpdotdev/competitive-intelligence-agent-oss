#!/usr/bin/env python3
"""
Read a Google Doc by URL or document ID.

Usage:
    python read_google_doc.py --url "https://docs.google.com/document/d/DOC_ID/edit"
    python read_google_doc.py --id "DOC_ID"
    python read_google_doc.py --url "..." --json  # JSON output with metadata
"""
import argparse
import json
import re
import sys

from google_docs_service import GoogleDocsService


def extract_document_id(url: str) -> str | None:
    """Extract the document ID from a Google Docs URL.
    
    Handles various URL formats:
    - https://docs.google.com/document/d/DOC_ID/edit
    - https://docs.google.com/document/d/DOC_ID/edit?usp=sharing
    - https://docs.google.com/document/d/DOC_ID
    - docs.google.com/document/d/DOC_ID/...
    
    Args:
        url: A Google Docs URL
        
    Returns:
        The document ID, or None if not found
    """
    # Pattern matches /d/DOCUMENT_ID with optional trailing path
    pattern = r'/d/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Read a Google Doc by URL or document ID"
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--url",
        help="The Google Docs URL (e.g., https://docs.google.com/document/d/DOC_ID/edit)"
    )
    input_group.add_argument(
        "--id",
        dest="doc_id",
        help="The document ID directly"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    
    args = parser.parse_args()
    
    # Determine document ID
    if args.url:
        doc_id = extract_document_id(args.url)
        if not doc_id:
            print(f"Error: Could not extract document ID from URL: {args.url}", file=sys.stderr)
            print("Expected format: https://docs.google.com/document/d/DOCUMENT_ID/...", file=sys.stderr)
            sys.exit(1)
    else:
        doc_id = args.doc_id
    
    # Fetch the document
    try:
        service = GoogleDocsService()
        document = service.get_document_content(doc_id)
        
        if not document:
            print(f"Error: Could not retrieve document with ID: {doc_id}", file=sys.stderr)
            print("Check that the document exists and you have permission to access it.", file=sys.stderr)
            sys.exit(1)
        
        # Extract content
        title = document.get('title', 'Untitled')
        content = service.extract_text_from_document(document)
        web_link = f"https://docs.google.com/document/d/{doc_id}/edit"
        
        if args.json:
            result = {
                "title": title,
                "documentId": doc_id,
                "webViewLink": web_link,
                "content": content
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"Document: {title}")
            print(f"ID: {doc_id}")
            print(f"Link: {web_link}")
            print("---")
            print(content)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error reading document: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
