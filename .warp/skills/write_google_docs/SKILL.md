---
name: write_google_docs
description: Skill for writing arbitrary Google Docs
---

# Write Google Docs Skill

Use this skill to create new Google Docs documents, populate them with content, and write to specific tabs.

## When to Use

Use this skill when you need to:
- Create product briefs, reports, or analysis documents
- Write competitive analysis summaries
- Generate deliverables that need to be shared via Google Docs
- Create structured documents for team review
- Write content to a specific tab in a new or existing document

Do NOT use this skill when:
- The user just wants text output in the conversation
- The content is short and doesn't need to be a document

## How to Use

### Basic Usage

Run the script from the `skills/write_google_docs/` directory:

```bash
python skills/write_google_docs/write_google_doc.py --title "Document Title" --content "Your content here"
```

### Writing to Tabs

1. **Create a new document with a named tab**:
```bash
python skills/write_google_docs/write_google_doc.py --title "Weekly Report" --tab "Week 9" --content "Week 9 analysis..."
```

2. **Write to a tab in an existing document** (creates the tab if it doesn't exist):
```bash
python skills/write_google_docs/write_google_doc.py --document-id DOCUMENT_ID --tab "Week 10" --content "Week 10 analysis..."
```

3. **Write to an existing tab** (if tab title matches, writes to it; otherwise creates a new tab):
```bash
python skills/write_google_docs/write_google_doc.py --document-id DOCUMENT_ID --tab "Summary" --content-file summary.txt
```

When using `--document-id`, the `--tab` flag is required. When creating a new document with `--title`, `--tab` is optional — if omitted, content goes to the default first tab.

### Placing Documents in a Drive Folder

Use `--folder-id` to create the document inside a specific Google Drive folder:
```bash
python skills/write_google_docs/write_google_doc.py --title "Report" --folder-id FOLDER_ID --content "Content..."
```

The folder ID is the last segment of a Drive folder URL (e.g. `YOUR_GOOGLE_DRIVE_FOLDER_ID` from `https://drive.google.com/drive/folders/YOUR_GOOGLE_DRIVE_FOLDER_ID`). This option can be combined with `--tab`.

### Content Options

1. **Inline content** (for shorter text):
```bash
python skills/write_google_docs/write_google_doc.py --title "Brief Title" --content "Brief content goes here"
```

2. **From a file** (for longer content):
```bash
python skills/write_google_docs/write_google_doc.py --title "Report Title" --content-file /path/to/content.txt
```

3. **From stdin** (for piping content):
```bash
echo "Content here" | python skills/write_google_docs/write_google_doc.py --title "Document Title" --stdin
```

### JSON Output

For programmatic use, add the `--json` flag:
```bash
python skills/write_google_docs/write_google_doc.py --title "Title" --content "Content" --json
```

This returns JSON with `documentId`, `webViewLink`, `title`, and optionally `tabId`.

## Output

The script outputs:
- Document title
- Document ID
- Tab ID (when using `--tab`)
- Web link to the document (shareable)

## Content Formatting

Markdown in the content is automatically converted to native Google Docs formatting:
- `# Heading` through `###### Heading` → Google Docs headings (H1-H6)
- `**bold**` or `__bold__` → bold text
- `*italic*` or `_italic_` → italic text
- `- item` or `* item` → bullet lists
- `1. item` → numbered lists
- `[text](url)` → plain text (link removed)
- `` `code` `` → plain text (backticks removed)

For best results:
- Use newlines to separate paragraphs
- Structure content with markdown headings
- The document title becomes the Google Doc title

## After Creating a Document

After creating a document, you can:
1. Share the link with the user
2. Use the `post_to_slack` skill to share the link to Slack
3. Return the link for the user to access

## Example Workflows

### Single document

```bash
python skills/write_google_docs/write_google_doc.py --title "Competitive Analysis - January 2026" --content "Your analysis content..."
```

### Multi-tab weekly report

Create the document with the first week's tab:
```bash
python skills/write_google_docs/write_google_doc.py --title "Weekly Reports - Q1 2026" --tab "Week 1" --content "Week 1 content..." --json
```

Then add subsequent weeks to the same document using the returned document ID:
```bash
python skills/write_google_docs/write_google_doc.py --document-id DOC_ID --tab "Week 2" --content "Week 2 content..."
python skills/write_google_docs/write_google_doc.py --document-id DOC_ID --tab "Week 3" --content "Week 3 content..."
```

## Prerequisites

- Google OAuth credentials must be configured (same as summarize_google_docs)
- Credentials with write permissions to Google Docs and Drive
- If authentication fails, delete `token.json` in the project root and re-authenticate

## Error Handling

If you encounter authentication errors:
1. The OAuth scopes may need to be updated
2. Delete `token.json` and run again to re-authenticate with new scopes
3. The user will need to authorize the app in their browser
