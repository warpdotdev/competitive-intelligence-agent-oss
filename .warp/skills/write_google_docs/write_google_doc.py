#!/usr/bin/env python3
"""
Create a Google Doc with the specified title and content, with optional tab support.

Usage:
    python write_google_doc.py --title "Document Title" --content "Document content"
    python write_google_doc.py --title "Document Title" --content-file input.txt
    echo "Content from stdin" | python write_google_doc.py --title "Document Title" --stdin

    # Write to a specific tab in a new document
    python write_google_doc.py --title "Document Title" --tab "Analysis" --content "Tab content"

    # Write to a tab in an existing document
    python write_google_doc.py --document-id DOC_ID --tab "Week 3" --content "Content here"
"""
import argparse
import sys
import json

from google_docs_writer import GoogleDocsWriter


def main():
    parser = argparse.ArgumentParser(
        description="Create a Google Doc with the specified title and content"
    )
    parser.add_argument(
        "--title", 
        help="The title for the Google Doc (required when creating a new document)"
    )
    parser.add_argument(
        "--document-id",
        help="ID of an existing document to write to (use with --tab)"
    )
    parser.add_argument(
        "--tab",
        help="Tab title to write content to. Creates the tab if it doesn't exist."
    )
    parser.add_argument(
        "--folder-id",
        help="Google Drive folder ID to place the new document in."
    )
    
    content_group = parser.add_mutually_exclusive_group()
    content_group.add_argument(
        "--content",
        help="The text content to add to the document"
    )
    content_group.add_argument(
        "--content-file",
        help="Path to a file containing the content to add"
    )
    content_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read content from stdin"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.document_id and not args.title:
        parser.error("--title is required when creating a new document")
    
    if args.document_id and not args.tab:
        parser.error("--tab is required when using --document-id")
    
    # Determine content source
    content = ""
    if args.content:
        content = args.content
    elif args.content_file:
        try:
            with open(args.content_file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.content_file}", file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.stdin:
        content = sys.stdin.read()
    
    try:
        writer = GoogleDocsWriter()
        
        if args.document_id:
            # Write to a tab in an existing document
            result = writer.write_to_tab(
                document_id=args.document_id,
                tab_title=args.tab,
                content=content
            )
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"\nContent written to tab '{args.tab}' successfully!")
                print(f"Document ID: {result['documentId']}")
                print(f"Tab ID: {result['tabId']}")
                print(f"Link: {result['webViewLink']}")
        else:
            # Create a new document (optionally with a named tab and/or in a folder)
            result = writer.create_document_with_content(
                title=args.title,
                content=content,
                tab_name=args.tab,
                folder_id=args.folder_id
            )
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"\nDocument created successfully!")
                print(f"Title: {result['title']}")
                print(f"Document ID: {result['documentId']}")
                if result.get('tabId'):
                    print(f"Tab ID: {result['tabId']}")
                print(f"Link: {result['webViewLink']}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
