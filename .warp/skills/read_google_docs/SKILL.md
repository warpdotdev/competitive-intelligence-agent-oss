---
name: read_google_docs
description: Reads content from a specific Google Doc by URL or document ID.
---

# Read Google Docs Skill

Use this skill to read the content of a specific Google Doc when you have its URL or document ID.

## When to Use

Use this skill when you need to:
- Read a specific Google Doc by URL or document ID
- Extract document content for analysis, research, or reference
- Provide document context to other skills or workflows
- Access a document shared by the user

Do NOT use this skill when:
- You need to summarize recent docs from the last N days (use `summarize_google_docs`)
- You need to create a new document (use `write_google_docs`)
- You don't have a specific document URL or ID

## How to Use

### By URL (recommended)

```bash
python skills/read_google_docs/read_google_doc.py --url "https://docs.google.com/document/d/DOC_ID/edit"
```

The script handles various Google Docs URL formats:
- `https://docs.google.com/document/d/DOC_ID/edit`
- `https://docs.google.com/document/d/DOC_ID/edit?usp=sharing`
- `https://docs.google.com/document/d/DOC_ID`

### By Document ID

```bash
python skills/read_google_docs/read_google_doc.py --id "YOUR_GOOGLE_DOC_ID"
```

### JSON Output

For programmatic use, add the `--json` flag:

```bash
python skills/read_google_docs/read_google_doc.py --url "..." --json
```

This returns JSON with `title`, `documentId`, `webViewLink`, and `content`.

## Output

### Default (human-readable)

```
Document: Project Plan Q4 2025
ID: YOUR_GOOGLE_DOC_ID
Link: https://docs.google.com/document/d/YOUR_GOOGLE_DOC_ID/edit
---
[Plain text content of the document]
```

### JSON mode

```json
{
  "title": "Project Plan Q4 2025",
  "documentId": "YOUR_GOOGLE_DOC_ID",
  "webViewLink": "https://docs.google.com/document/d/YOUR_GOOGLE_DOC_ID/edit",
  "content": "Plain text content of the document..."
}
```

## Prerequisites

- Google OAuth credentials must be configured (same as other Google Docs skills)
- The authenticated user must have read access to the document
- If authentication fails, delete `token.json` in the project root and re-authenticate

## Error Handling

Common errors:
- **Invalid URL**: The script couldn't parse a document ID from the URL
- **Permission denied**: You don't have access to the document
- **Document not found**: The document ID doesn't exist

## Integration with Other Skills

After reading a document, you can:
1. Analyze its content and provide insights
2. Use `write_google_docs` to create a new document based on it
3. Use `post_to_slack` to share a summary
