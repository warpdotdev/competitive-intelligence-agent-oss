---
name: summarize_google_docs
description: Reads internal documents and creates a summary.
---

Use the provided python script to read recent google docs from the last 7 days and summarize the output. the required credentials are stored as an environment variable.

Don't mention upcoming milestones or DRI's.

Make note of important themes across the documents. if there are potential conflicts, also make note of that. 

## After Completing Summary

1. **Save the report** to `reports/google_doc_summaries/google_doc_summary_YYYY-MM-DD.md`, then create a PR.
Here are instructions for using the google docs python scripts:

# Google Docs Service

A Python service that connects to the Google Docs API and retrieves documents modified in the last week.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the service:**
   ```bash
   python google_docs_service.py
   ```

The credential to run the service can be found in the environment variable GOOGLE_OAUTH_TOKEN

## Usage

### Basic Usage

```python
from google_docs_service import GoogleDocsService

# Initialize service
service = GoogleDocsService()

# Get documents from last 7 days
recent_docs = service.get_recent_documents(days=7)

for doc in recent_docs:
    print(f"Document: {doc['name']}")
    print(f"Link: {doc['webViewLink']}")
```

### Reading Document Content

```python
# Get full document content
document_content = service.get_document_content(document_id)

# Extract plain text
text = service.extract_text_from_document(document_content)
print(text)
```

### Custom Time Range

```python
# Get documents from last 30 days
recent_docs = service.get_recent_documents(days=30)
```

## Features

- OAuth2 authentication with token caching
- Query documents modified within a specified time range
- Fetch document metadata (name, ID, modified time, link)
- Retrieve full document content
- Extract plain text from documents

## Files

- `google_docs_service.py` - Main service implementation
- `requirements.txt` - Python dependencies
## API Scopes

The service requests the following scopes:
- `drive.readonly` - Read-only access to Drive files
- `documents.readonly` - Read-only access to Google Docs

## Notes

- The service uses UTC time for date calculations
- Maximum 100 documents are returned per query (can be adjusted)
- Documents are ordered by modification time (most recent first)
