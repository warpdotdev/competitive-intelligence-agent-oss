---
name: write_notion
description: Skill for interacting with Notion workspaces through the Notion REST API.
---

# Notion API Skill

This skill enables interaction with Notion workspaces through the Notion REST API. Use `curl` and `jq` for direct REST calls, or write ad-hoc scripts as appropriate for the task.

## When to Use

Use this skill when you need to:
- Create, update, or archive pages in Notion
- Query or create databases in Notion
- Append or modify block content on Notion pages
- Search across Notion workspaces

Do NOT use this skill when:
- The user just wants text output in the conversation
- The Notion MCP server can handle the request (prefer MCP for reads)

## Authentication

### API Key Handling

1. **Environment Variable**: Check if `NOTION_API_KEY` is available in the environment
2. **User-Provided Key**: If the user provides an API key in context, use that instead
3. **No Key Available**: Ask the user to provide the API key

IMPORTANT: Never display, log, or send `NOTION_API_KEY` anywhere except in the `Authorization` header. Confirm its existence, ask if missing, use it in requests—but never echo or expose it.

### Request Headers

All requests require these headers:

```bash
-H "Authorization: Bearer $NOTION_API_KEY" \
-H "Notion-Version: 2025-09-03" \
-H "Content-Type: application/json"
```

### Verifying Authentication

Test the API key by retrieving the bot user:

```bash
curl -s "https://api.notion.com/v1/users/me" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

## Base URL and Conventions

- Base URL: `https://api.notion.com`
- API Version: `2025-09-03` (required header)
- Data Format: JSON for all request/response bodies
- Property Names: `snake_case`
- Timestamps: ISO 8601 format (`2020-08-12T02:12:33.231Z`)
- IDs: UUIDv4 format (dashes optional in requests)
- Empty Values: Use `null` instead of empty strings

## Rate Limits

- Average: 3 requests per second per integration
- Bursts: Brief bursts above this limit are allowed
- Rate Limited Response: HTTP 429 with `Retry-After` header
- Strategy: Implement exponential backoff when receiving 429 responses

## Request Size Limits

- Maximum block elements per payload: 1000
- Maximum payload size: 500KB
- Rich text content: 2000 characters
- URLs: 2000 characters
- Equations: 1000 characters
- Email addresses: 200 characters
- Phone numbers: 200 characters
- Multi-select options: 100 items
- Relations: 100 related pages
- People mentions: 100 users
- Block arrays per request: 100 elements

## Confirmation for Destructive Operations

IMPORTANT: Before executing any operation that modifies or deletes data, ask the user for confirmation. This includes:

- Any bulk operations
- Creating pages (if multiple or in batch)
- Modifying database schemas
- Deleting/archiving pages or blocks
- Updating pages or blocks

For a logical group of related operations, a single confirmation is sufficient.

## Core API Endpoints

### Search

Search across all accessible pages and databases:

```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search term",
    "filter": {"property": "object", "value": "page"},
    "sort": {"direction": "descending", "timestamp": "last_edited_time"},
    "page_size": 100
  }' | jq
```

Filter values: `"page"` or `"data_source"` (or omit for both)

### Pages

#### Retrieve a Page

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

Note: This returns page properties, not content. For content, use "Retrieve block children" with the page ID.

#### Create a Page

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "parent-page-id"},
    "properties": {
      "title": {
        "title": [{"text": {"content": "Page Title"}}]
      }
    },
    "children": [
      {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
          "rich_text": [{"type": "text", "text": {"content": "Paragraph content"}}]
        }
      }
    ]
  }' | jq
```

Parent options:
- `{"data_source_id": "..."}` - Create in a data source (API v2025-09-03+)
- `{"database_id": "..."}` - Create in a database (legacy)
- `{"page_id": "..."}` - Create under a page

#### Update a Page

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "title": {"title": [{"text": {"content": "Updated Title"}}]}
    },
    "icon": {"type": "emoji", "emoji": "📝"},
    "archived": false
  }' | jq
```

Additional update options: `cover`, `is_locked`, `in_trash`

#### Archive (Delete) a Page

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"archived": true}' | jq
```

#### Retrieve a Page Property Item

For properties with more than 25 references:

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}/properties/{property_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

### Blocks (Page Content)

#### Retrieve Block Children

```bash
curl -s "https://api.notion.com/v1/blocks/{block_id}/children?page_size=100" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

Use the page ID as `block_id` to get page content. Check `has_children` on each block for nested content.

#### Append Block Children

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{block_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
          "rich_text": [{"type": "text", "text": {"content": "New Section"}}]
        }
      },
      {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
          "rich_text": [{"type": "text", "text": {"content": "Content here"}}]
        }
      }
    ]
  }' | jq
```

Maximum 100 blocks per request, up to 2 levels of nesting.

Position options in request body:
- `"position": {"type": "after_block", "after_block": {"id": "block-id"}}` - Insert after specific block
- `"position": {"type": "start"}` - Insert at beginning
- Default: appends to end

#### Retrieve a Block

```bash
curl -s "https://api.notion.com/v1/blocks/{block_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

#### Update a Block

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{block_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "paragraph": {
      "rich_text": [{"type": "text", "text": {"content": "Updated content"}}]
    }
  }' | jq
```

The update replaces the entire value for the specified field.

#### Delete a Block

```bash
curl -s -X DELETE "https://api.notion.com/v1/blocks/{block_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

Moves block to trash (can be restored).

### Databases

#### Retrieve a Database

```bash
curl -s "https://api.notion.com/v1/databases/{database_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

Returns database structure including data sources and properties.

#### Query a Database

```bash
curl -s -X POST "https://api.notion.com/v1/databases/{database_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "property": "Status",
      "select": {"equals": "Done"}
    },
    "sorts": [
      {"property": "Created", "direction": "descending"}
    ],
    "page_size": 100
  }' | jq
```

#### Create a Database

```bash
curl -s -X POST "https://api.notion.com/v1/databases" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "parent-page-id"},
    "title": [{"type": "text", "text": {"content": "My Database"}}],
    "is_inline": true,
    "initial_data_source": {
      "properties": {
        "Name": {"title": {}},
        "Status": {
          "select": {
            "options": [
              {"name": "To Do", "color": "red"},
              {"name": "In Progress", "color": "yellow"},
              {"name": "Done", "color": "green"}
            ]
          }
        },
        "Due Date": {"date": {}}
      }
    }
  }' | jq
```

#### Update a Database

```bash
curl -s -X PATCH "https://api.notion.com/v1/databases/{database_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "title": [{"text": {"content": "Updated Title"}}],
    "description": [{"text": {"content": "Database description"}}]
  }' | jq
```

### Users

#### List All Users

```bash
curl -s "https://api.notion.com/v1/users?page_size=100" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

#### Retrieve a User

```bash
curl -s "https://api.notion.com/v1/users/{user_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

### Comments

#### Retrieve Comments

```bash
curl -s "https://api.notion.com/v1/comments?block_id={block_id}&page_size=100" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq
```

#### Add a Comment

```bash
curl -s -X POST "https://api.notion.com/v1/comments" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "page-id"},
    "rich_text": [{"type": "text", "text": {"content": "Comment text"}}]
  }' | jq
```

## Pagination

Paginated endpoints return a `next_cursor` field. To get subsequent pages:

```bash
curl -s -X POST "https://api.notion.com/v1/databases/{database_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "start_cursor": "next-cursor-value",
    "page_size": 100
  }' | jq
```

Check `has_more` in the response to determine if more pages exist.

## Block Types Reference

Common block types for use in `children` arrays:

- `paragraph` - Standard text
- `heading_1`, `heading_2`, `heading_3` - Headings
- `bulleted_list_item` - Bullet list item
- `numbered_list_item` - Numbered list item
- `to_do` - Checkbox item (has `checked` boolean)
- `toggle` - Collapsible toggle
- `code` - Code block (has `language` field)
- `quote` - Block quote
- `callout` - Callout box (has `icon` field)
- `divider` - Horizontal divider (`{}` as value)
- `table_of_contents` - Auto-generated TOC
- `image`, `video`, `file`, `pdf` - Media embeds
- `bookmark` - URL bookmark
- `equation` - Math equation (KaTeX)

## Guidelines

- Always verify `NOTION_API_KEY` exists before making requests
- Use `jq` to parse and format JSON responses
- Handle pagination for large result sets
- Implement retry logic with exponential backoff for 429 errors
- Always ask for user confirmation before destructive or bulk operations
