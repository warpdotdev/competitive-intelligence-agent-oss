"""Google Docs API service for writing and creating documents."""

import sys
import os
import re
from typing import Dict, Any, List, Optional, Tuple

# Add parent directory to path to import google_docs_service
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'summarize_google_docs'))

from google_docs_service import GoogleDocsService
from googleapiclient.errors import HttpError


class GoogleDocsWriter(GoogleDocsService):
    """Service for writing to Google Docs, extends GoogleDocsService."""

    def get_tabs(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all tabs in a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of tab info dicts with keys: tabId, title, index
        """
        try:
            # The bundled discovery document may not include includeTabsContent,
            # so we append it to the request URI directly.
            request = self.docs_service.documents().get(documentId=document_id)
            sep = '&' if '?' in request.uri else '?'
            request.uri += f'{sep}includeTabsContent=true'
            document = request.execute()
            
            tabs = []
            for tab in document.get('tabs', []):
                props = tab.get('tabProperties', {})
                tabs.append({
                    'tabId': props.get('tabId', ''),
                    'title': props.get('title', ''),
                    'index': props.get('index', 0)
                })
                # Include child tabs
                for child in tab.get('childTabs', []):
                    child_props = child.get('tabProperties', {})
                    tabs.append({
                        'tabId': child_props.get('tabId', ''),
                        'title': child_props.get('title', ''),
                        'index': child_props.get('index', 0),
                        'parentTabId': props.get('tabId', '')
                    })
            
            return tabs
            
        except HttpError as error:
            print(f"An error occurred getting tabs: {error}")
            raise

    def find_tab_by_title(self, document_id: str, title: str) -> Optional[Dict[str, Any]]:
        """Find a tab by its title.
        
        Args:
            document_id: The ID of the document
            title: The title of the tab to find
            
        Returns:
            Tab info dict if found, None otherwise
        """
        tabs = self.get_tabs(document_id)
        for tab in tabs:
            if tab['title'] == title:
                return tab
        return None

    def add_tab(self, document_id: str, title: str, index: Optional[int] = None) -> str:
        """Add a new tab to a document.
        
        Args:
            document_id: The ID of the document
            title: The title for the new tab
            index: Optional zero-based index for tab position
            
        Returns:
            The tab ID of the newly created tab
        """
        try:
            tab_properties = {'title': title}
            if index is not None:
                tab_properties['index'] = index
            
            requests = [{
                'addDocumentTab': {
                    'tabProperties': tab_properties
                }
            }]
            
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            # Extract the new tab ID from the reply
            replies = result.get('replies', [{}])
            reply = replies[0].get('addDocumentTab', {})
            tab_id = reply.get('tabId', '') or reply.get('tabProperties', {}).get('tabId', '')
            
            # Fallback: fetch tabs and find by title if reply didn't include the ID
            if not tab_id:
                tab = self.find_tab_by_title(document_id, title)
                if tab:
                    tab_id = tab['tabId']
            
            if not tab_id:
                raise RuntimeError(f"Created tab '{title}' but could not determine its ID")
            
            print(f"Added tab '{title}' with ID: {tab_id}")
            return tab_id
            
        except HttpError as error:
            print(f"An error occurred adding tab: {error}")
            raise

    def move_to_folder(self, file_id: str, folder_id: str) -> None:
        """Move a file into a specific Drive folder.
        
        Args:
            file_id: The ID of the file to move
            folder_id: The ID of the destination folder
        """
        try:
            # Get the file's current parents to remove them
            file_meta = self.drive_service.files().get(
                fileId=file_id, fields='parents',
                supportsAllDrives=True
            ).execute()
            previous_parents = ','.join(file_meta.get('parents', []))
            
            self.drive_service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents',
                supportsAllDrives=True
            ).execute()
            
            print(f"Moved file {file_id} to folder {folder_id}")
            
        except HttpError as error:
            print(f"An error occurred moving file to folder: {error}")
            raise

    def create_document(self, title: str) -> Dict[str, Any]:
        """Create a new blank Google Doc with the given title.
        
        Args:
            title: The title for the new document
            
        Returns:
            Dictionary containing document metadata including documentId and webViewLink
        """
        try:
            document_body = {
                'title': title
            }
            
            document = self.docs_service.documents().create(
                body=document_body
            ).execute()
            
            print(f"Created document: {document.get('title')}")
            print(f"Document ID: {document.get('documentId')}")
            
            return document
            
        except HttpError as error:
            print(f"An error occurred creating document: {error}")
            raise

    def insert_text(self, document_id: str, text: str, index: Optional[int] = None,
                    tab_id: Optional[str] = None) -> Dict[str, Any]:
        """Insert text into a document at a specific index or at the end.
        
        Args:
            document_id: The ID of the document
            text: The text to insert
            index: Optional index position. If None, appends to end of document
            tab_id: Optional tab ID to write to. If None, writes to the first tab.
            
        Returns:
            Response from the batchUpdate call
        """
        try:
            requests = []
            
            if index is None:
                # Insert at the end of the document/tab
                end_location = {'segmentId': ''}
                if tab_id:
                    end_location['tabId'] = tab_id
                requests.append({
                    'insertText': {
                        'text': text,
                        'endOfSegmentLocation': end_location
                    }
                })
            else:
                # Insert at specific index
                location = {'index': index}
                if tab_id:
                    location['tabId'] = tab_id
                requests.append({
                    'insertText': {
                        'text': text,
                        'location': location
                    }
                })
            
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return result
            
        except HttpError as error:
            print(f"An error occurred inserting text: {error}")
            raise

    def format_as_heading(self, document_id: str, start_index: int, end_index: int, 
                         heading_level: int = 1) -> Dict[str, Any]:
        """Format text as a heading.
        
        Args:
            document_id: The ID of the document
            start_index: Start index of text to format
            end_index: End index of text to format
            heading_level: Heading level (1-6, where 1 is largest)
            
        Returns:
            Response from the batchUpdate call
        """
        try:
            heading_style = f'HEADING_{heading_level}'
            
            requests = [{
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index
                    },
                    'paragraphStyle': {
                        'namedStyleType': heading_style
                    },
                    'fields': 'namedStyleType'
                }
            }]
            
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return result
            
        except HttpError as error:
            print(f"An error occurred formatting heading: {error}")
            raise

    def format_text_style(self, document_id: str, start_index: int, end_index: int,
                         bold: bool = False, italic: bool = False) -> Dict[str, Any]:
        """Apply text formatting (bold, italic).
        
        Args:
            document_id: The ID of the document
            start_index: Start index of text to format
            end_index: End index of text to format
            bold: Whether to make text bold
            italic: Whether to make text italic
            
        Returns:
            Response from the batchUpdate call
        """
        try:
            text_style = {}
            fields = []
            
            if bold:
                text_style['bold'] = True
                fields.append('bold')
            
            if italic:
                text_style['italic'] = True
                fields.append('italic')
            
            if not fields:
                return {}
            
            requests = [{
                'updateTextStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index
                    },
                    'textStyle': text_style,
                    'fields': ','.join(fields)
                }
            }]
            
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return result
            
        except HttpError as error:
            print(f"An error occurred formatting text: {error}")
            raise

    def get_document_link(self, document_id: str) -> str:
        """Get the web view link for a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            The webViewLink URL for the document
        """
        try:
            file_metadata = self.drive_service.files().get(
                fileId=document_id,
                fields='webViewLink',
                supportsAllDrives=True
            ).execute()
            
            return file_metadata.get('webViewLink', '')
            
        except HttpError as error:
            print(f"An error occurred getting document link: {error}")
            raise

    def _parse_markdown_to_plain_text_and_formatting(self, content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse markdown content and extract plain text with formatting instructions.
        
        Converts markdown to plain text while tracking where formatting should be applied.
        
        Args:
            content: Markdown-formatted text
            
        Returns:
            Tuple of (plain_text, formatting_instructions)
            formatting_instructions is a list of dicts with keys:
                - type: 'heading', 'bold', 'italic', 'bullet', 'numbered'
                - start: start index in plain text
                - end: end index in plain text
                - level: (for headings) 1-6
        """
        lines = content.split('\n')
        plain_text_parts = []
        formatting = []
        current_index = 1  # Google Docs starts at index 1
        
        for line in lines:
            original_line = line
            line_start = current_index
            
            # Check for headings (# ## ### etc.)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                # Process inline formatting in heading text
                text, inline_formats = self._process_inline_formatting(text, line_start)
                formatting.extend(inline_formats)
                plain_text_parts.append(text + '\n')
                formatting.append({
                    'type': 'heading',
                    'start': line_start,
                    'end': line_start + len(text) + 1,
                    'level': level
                })
                current_index += len(text) + 1
                continue
            
            # Check for bullet points (- or *)
            bullet_match = re.match(r'^\s*[-*]\s+(.+)$', line)
            if bullet_match:
                text = bullet_match.group(1)
                # Process inline formatting
                text, inline_formats = self._process_inline_formatting(text, line_start)
                formatting.extend(inline_formats)
                plain_text_parts.append(text + '\n')
                formatting.append({
                    'type': 'bullet',
                    'start': line_start,
                    'end': line_start + len(text) + 1
                })
                current_index += len(text) + 1
                continue
            
            # Check for numbered lists
            numbered_match = re.match(r'^\s*\d+\.\s+(.+)$', line)
            if numbered_match:
                text = numbered_match.group(1)
                # Process inline formatting
                text, inline_formats = self._process_inline_formatting(text, line_start)
                formatting.extend(inline_formats)
                plain_text_parts.append(text + '\n')
                formatting.append({
                    'type': 'numbered',
                    'start': line_start,
                    'end': line_start + len(text) + 1
                })
                current_index += len(text) + 1
                continue
            
            # Regular line - process inline formatting
            text, inline_formats = self._process_inline_formatting(line, line_start)
            formatting.extend(inline_formats)
            plain_text_parts.append(text + '\n')
            current_index += len(text) + 1
        
        plain_text = ''.join(plain_text_parts)
        # Remove trailing newline if present
        if plain_text.endswith('\n'):
            plain_text = plain_text[:-1]
        
        return plain_text, formatting
    
    def _process_inline_formatting(self, text: str, base_index: int) -> Tuple[str, List[Dict[str, Any]]]:
        """Process inline markdown formatting (bold, italic) in text.
        
        Args:
            text: Text that may contain inline markdown
            base_index: Starting index in the document for this text
            
        Returns:
            Tuple of (plain_text, formatting_instructions)
        """
        formatting = []
        result = text
        
        # Process bold (**text** or __text__)
        bold_pattern = r'\*\*(.+?)\*\*|__(.+?)__'
        offset = 0
        for match in re.finditer(bold_pattern, text):
            content = match.group(1) or match.group(2)
            start_in_result = match.start() - offset
            # Remove the markdown syntax
            result = result[:start_in_result] + content + result[start_in_result + len(match.group(0)):]
            formatting.append({
                'type': 'bold',
                'start': base_index + start_in_result,
                'end': base_index + start_in_result + len(content)
            })
            offset += 4  # ** on each side = 4 chars removed
        
        # Process italic (*text* or _text_) - must be careful not to match bold
        # Process single asterisks/underscores that aren't part of double
        italic_pattern = r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)'
        offset = 0
        temp_result = result
        for match in re.finditer(italic_pattern, result):
            content = match.group(1) or match.group(2)
            if content:  # Ensure we have a match
                start_in_result = match.start() - offset
                temp_result = temp_result[:start_in_result] + content + temp_result[start_in_result + len(match.group(0)):]
                formatting.append({
                    'type': 'italic',
                    'start': base_index + start_in_result,
                    'end': base_index + start_in_result + len(content)
                })
                offset += 2  # * on each side = 2 chars removed
        result = temp_result
        
        # Remove inline code backticks (just display as plain text)
        result = re.sub(r'`([^`]+)`', r'\1', result)
        
        # Remove link markdown [text](url) -> text
        result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)
        
        return result, formatting
    
    def _apply_formatting(self, document_id: str, formatting: List[Dict[str, Any]],
                          tab_id: Optional[str] = None) -> None:
        """Apply formatting instructions to a document.
        
        Args:
            document_id: The ID of the document
            formatting: List of formatting instructions
            tab_id: Optional tab ID to apply formatting to
        """
        if not formatting:
            return
        
        requests = []
        
        for fmt in formatting:
            fmt_range = {
                'startIndex': fmt['start'],
                'endIndex': fmt['end']
            }
            if tab_id:
                fmt_range['tabId'] = tab_id
            
            if fmt['type'] == 'heading':
                level = min(fmt['level'], 6)  # Cap at 6
                heading_style = f'HEADING_{level}'
                requests.append({
                    'updateParagraphStyle': {
                        'range': fmt_range,
                        'paragraphStyle': {
                            'namedStyleType': heading_style
                        },
                        'fields': 'namedStyleType'
                    }
                })
            elif fmt['type'] == 'bold':
                requests.append({
                    'updateTextStyle': {
                        'range': fmt_range,
                        'textStyle': {'bold': True},
                        'fields': 'bold'
                    }
                })
            elif fmt['type'] == 'italic':
                requests.append({
                    'updateTextStyle': {
                        'range': fmt_range,
                        'textStyle': {'italic': True},
                        'fields': 'italic'
                    }
                })
            elif fmt['type'] == 'bullet':
                requests.append({
                    'createParagraphBullets': {
                        'range': fmt_range,
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                })
            elif fmt['type'] == 'numbered':
                requests.append({
                    'createParagraphBullets': {
                        'range': fmt_range,
                        'bulletPreset': 'NUMBERED_DECIMAL_NESTED'
                    }
                })
        
        if requests:
            try:
                self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
            except HttpError as error:
                print(f"An error occurred applying formatting: {error}")
                raise

    def create_document_with_content(self, title: str, content: str,
                                      tab_name: Optional[str] = None,
                                      folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new document and populate it with content.
        
        This is a convenience method that creates a document and adds content in one call.
        Markdown formatting in the content is automatically converted to native Google Docs
        formatting (headings, bold, italic, bullets, numbered lists).
        
        Args:
            title: The title for the new document
            content: The text content to add to the document (can include markdown)
            tab_name: Optional name for a new tab to write content into.
                      If None, content is written to the default first tab.
            folder_id: Optional Drive folder ID to place the document in.
            
        Returns:
            Dictionary containing documentId, webViewLink, and optionally tabId
        """
        # Create the document
        document = self.create_document(title)
        document_id = document.get('documentId')
        
        tab_id = None
        if tab_name:
            tab_id = self.add_tab(document_id, tab_name)
        
        # Parse markdown and insert content with formatting
        if content:
            plain_text, formatting = self._parse_markdown_to_plain_text_and_formatting(content)
            self.insert_text(document_id, plain_text, index=1, tab_id=tab_id)
            self._apply_formatting(document_id, formatting, tab_id=tab_id)
        
        # Move to folder if specified
        if folder_id:
            self.move_to_folder(document_id, folder_id)
        
        # Get the web link
        web_link = self.get_document_link(document_id)
        
        result = {
            'documentId': document_id,
            'webViewLink': web_link,
            'title': title
        }
        if tab_id:
            result['tabId'] = tab_id
        return result

    def write_to_tab(self, document_id: str, tab_title: str, content: str,
                     create_if_missing: bool = True) -> Dict[str, Any]:
        """Write content to a specific tab in an existing document.
        
        Args:
            document_id: The ID of the document
            tab_title: The title of the tab to write to
            content: Markdown content to write
            create_if_missing: If True, creates the tab if it doesn't exist
            
        Returns:
            Dictionary containing documentId, webViewLink, tabId, and tabTitle
        """
        # Find existing tab or create new one
        tab = self.find_tab_by_title(document_id, tab_title)
        if tab:
            tab_id = tab['tabId']
            print(f"Found existing tab '{tab_title}' with ID: {tab_id}")
        elif create_if_missing:
            tab_id = self.add_tab(document_id, tab_title)
        else:
            raise ValueError(f"Tab '{tab_title}' not found in document {document_id}")
        
        # Parse and insert content
        if content:
            plain_text, formatting = self._parse_markdown_to_plain_text_and_formatting(content)
            self.insert_text(document_id, plain_text, index=1, tab_id=tab_id)
            self._apply_formatting(document_id, formatting, tab_id=tab_id)
        
        web_link = self.get_document_link(document_id)
        
        return {
            'documentId': document_id,
            'webViewLink': web_link,
            'tabId': tab_id,
            'tabTitle': tab_title
        }


def main():
    """Example usage of the Google Docs writer service."""
    # Initialize service
    writer = GoogleDocsWriter()
    
    # Create a new document with content
    result = writer.create_document_with_content(
        title="Test Document",
        content="This is a test document created via the Google Docs API.\n\nIt has multiple paragraphs."
    )
    
    print(f"\nDocument created successfully!")
    print(f"Title: {result['title']}")
    print(f"Document ID: {result['documentId']}")
    print(f"Link: {result['webViewLink']}")


if __name__ == '__main__':
    main()
