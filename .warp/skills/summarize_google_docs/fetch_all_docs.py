"""Fetch all recent Google Docs and print their contents."""

from google_docs_service import GoogleDocsService


def main():
    service = GoogleDocsService()
    recent_docs = service.get_recent_documents(days=7)
    
    for doc in recent_docs:
        print(f"\n{'='*80}")
        print(f"DOCUMENT: {doc['name']}")
        print(f"Modified: {doc['modifiedTime']}")
        print(f"Link: {doc['webViewLink']}")
        print(f"{'='*80}")
        
        content = service.get_document_content(doc['id'])
        text = service.extract_text_from_document(content)
        print(text[:5000] if text else "(empty)")


if __name__ == '__main__':
    main()
