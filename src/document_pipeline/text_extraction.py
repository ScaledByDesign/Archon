"""
Text Extraction Module
Provides utilities for extracting text from various document formats
"""

import os
import io
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Union, BinaryIO, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

# Text extraction libraries
try:
    import PyPDF2
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import docx
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

try:
    from bs4 import BeautifulSoup
    HTML_SUPPORT = True
except ImportError:
    HTML_SUPPORT = False

try:
    import markdown
    MARKDOWN_SUPPORT = True
except ImportError:
    MARKDOWN_SUPPORT = False

try:
    import csv
    CSV_SUPPORT = True
except ImportError:
    CSV_SUPPORT = False

try:
    import json
    JSON_SUPPORT = True
except ImportError:
    JSON_SUPPORT = False

from pydantic import BaseModel, Field, validator, model_validator

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"
    CSV = "csv"
    JSON = "json"
    UNKNOWN = "unknown"


class TextExtractionResult(BaseModel):
    """Result of text extraction from a document"""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_type: DocumentType = Field(..., description="File type/extension")
    text_content: str = Field(..., description="Extracted text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")
    page_count: Optional[int] = Field(None, description="Number of pages")
    word_count: int = Field(0, description="Number of words")
    extraction_time: float = Field(..., description="Time taken for extraction in seconds")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    success: bool = Field(True, description="Whether extraction was successful")
    pages: Optional[List[str]] = Field(None, description="Text content split by pages")


class TextExtractor:
    """Text extractor for various document formats"""
    
    def __init__(self):
        """Initialize text extractor with supported formats"""
        self.supported_formats = {
            DocumentType.PDF: PDF_SUPPORT,
            DocumentType.DOCX: DOCX_SUPPORT,
            DocumentType.TXT: True,  # Built-in support
            DocumentType.HTML: HTML_SUPPORT,
            DocumentType.MARKDOWN: MARKDOWN_SUPPORT,
            DocumentType.CSV: CSV_SUPPORT,
            DocumentType.JSON: JSON_SUPPORT,
        }
        
        logger.info(f"Initialized TextExtractor with support for: {[fmt.value for fmt, supported in self.supported_formats.items() if supported]}")
    
    def get_document_type(self, filename: str) -> DocumentType:
        """Determine document type from filename
        
        Args:
            filename: Filename with extension
            
        Returns:
            DocumentType enum value
        """
        if not filename:
            return DocumentType.UNKNOWN
            
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Map extension to document type
        extension_map = {
            'pdf': DocumentType.PDF,
            'docx': DocumentType.DOCX,
            'doc': DocumentType.DOCX,  # Treat as DOCX, though extraction may differ
            'txt': DocumentType.TXT,
            'text': DocumentType.TXT,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'md': DocumentType.MARKDOWN,
            'markdown': DocumentType.MARKDOWN,
            'csv': DocumentType.CSV,
            'json': DocumentType.JSON,
        }
        
        return extension_map.get(extension, DocumentType.UNKNOWN)
    
    def extract_text(
        self, 
        file_content: Union[bytes, BinaryIO],
        filename: str,
        document_id: Optional[str] = None,
        extract_metadata: bool = True,
        split_pages: bool = True
    ) -> TextExtractionResult:
        """Extract text from document
        
        Args:
            file_content: File content as bytes or file-like object
            filename: Original filename with extension
            document_id: Optional document ID, generated if not provided
            extract_metadata: Whether to extract metadata
            split_pages: Whether to split content by pages (if applicable)
            
        Returns:
            TextExtractionResult with extracted text and metadata
        """
        import time
        start_time = time.time()
        
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Determine document type
        doc_type = self.get_document_type(filename)
        
        # Check if format is supported
        if doc_type == DocumentType.UNKNOWN:
            return TextExtractionResult(
                document_id=document_id,
                filename=filename,
                file_type=DocumentType.UNKNOWN,
                text_content="",
                extraction_time=time.time() - start_time,
                success=False,
                error="Unsupported file format"
            )
        
        if not self.supported_formats.get(doc_type, False):
            return TextExtractionResult(
                document_id=document_id,
                filename=filename,
                file_type=doc_type,
                text_content="",
                extraction_time=time.time() - start_time,
                success=False,
                error=f"Required library for {doc_type.value} extraction not installed"
            )
        
        # Extract text based on document type
        try:
            if isinstance(file_content, bytes):
                file_obj = io.BytesIO(file_content)
            else:
                file_obj = file_content
                
            if doc_type == DocumentType.PDF:
                result = self._extract_from_pdf(file_obj, extract_metadata, split_pages)
            elif doc_type == DocumentType.DOCX:
                result = self._extract_from_docx(file_obj, extract_metadata, split_pages)
            elif doc_type == DocumentType.TXT:
                result = self._extract_from_txt(file_obj, extract_metadata)
            elif doc_type == DocumentType.HTML:
                result = self._extract_from_html(file_obj, extract_metadata)
            elif doc_type == DocumentType.MARKDOWN:
                result = self._extract_from_markdown(file_obj, extract_metadata)
            elif doc_type == DocumentType.CSV:
                result = self._extract_from_csv(file_obj, extract_metadata)
            elif doc_type == DocumentType.JSON:
                result = self._extract_from_json(file_obj, extract_metadata)
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
                
            text_content, metadata, pages = result
            
            # Count words
            word_count = len(text_content.split())
            
            return TextExtractionResult(
                document_id=document_id,
                filename=filename,
                file_type=doc_type,
                text_content=text_content,
                metadata=metadata,
                page_count=len(pages) if pages else None,
                word_count=word_count,
                extraction_time=time.time() - start_time,
                success=True,
                pages=pages if split_pages else None
            )
            
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return TextExtractionResult(
                document_id=document_id,
                filename=filename,
                file_type=doc_type,
                text_content="",
                extraction_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    def _extract_from_pdf(
        self, 
        file_obj: BinaryIO, 
        extract_metadata: bool = True,
        split_pages: bool = True
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract text from PDF file
        
        Args:
            file_obj: File-like object
            extract_metadata: Whether to extract metadata
            split_pages: Whether to split content by pages
            
        Returns:
            Tuple of (text_content, metadata, pages)
        """
        if not PDF_SUPPORT:
            raise ImportError("PyPDF2 library not installed")
            
        reader = PdfReader(file_obj)
        
        # Extract text
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text())
        
        # Combine all pages
        text_content = "\n\n".join(pages)
        
        # Extract metadata
        metadata = {}
        if extract_metadata and reader.metadata:
            for key, value in reader.metadata.items():
                if key.startswith('/'):
                    clean_key = key[1:]  # Remove leading slash
                    metadata[clean_key] = value
        
        return text_content, metadata, pages
    
    def _extract_from_docx(
        self, 
        file_obj: BinaryIO, 
        extract_metadata: bool = True,
        split_pages: bool = True
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract text from DOCX file
        
        Args:
            file_obj: File-like object
            extract_metadata: Whether to extract metadata
            split_pages: Whether to split content by pages
            
        Returns:
            Tuple of (text_content, metadata, pages)
        """
        if not DOCX_SUPPORT:
            raise ImportError("python-docx library not installed")
            
        doc = Document(file_obj)
        
        # Extract text - note that DOCX doesn't have a concept of pages like PDFs
        paragraphs = [p.text for p in doc.paragraphs]
        text_content = "\n".join(paragraphs)
        
        # Extract metadata
        metadata = {}
        if extract_metadata and hasattr(doc, 'core_properties'):
            props = doc.core_properties
            if hasattr(props, 'title') and props.title:
                metadata['title'] = props.title
            if hasattr(props, 'author') and props.author:
                metadata['author'] = props.author
            if hasattr(props, 'created') and props.created:
                metadata['created'] = props.created
            if hasattr(props, 'modified') and props.modified:
                metadata['modified'] = props.modified
            if hasattr(props, 'subject') and props.subject:
                metadata['subject'] = props.subject
            if hasattr(props, 'keywords') and props.keywords:
                metadata['keywords'] = props.keywords
            if hasattr(props, 'category') and props.category:
                metadata['category'] = props.category
            if hasattr(props, 'comments') and props.comments:
                metadata['comments'] = props.comments
        
        # For DOCX, we don't have a clear concept of pages, but we can simulate
        # page breaks based on paragraph spacing or sections if needed
        pages = [text_content]  # Single "page" for now
        
        return text_content, metadata, pages
    
    def _extract_from_txt(
        self, 
        file_obj: BinaryIO, 
        extract_metadata: bool = True
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract text from TXT file
        
        Args:
            file_obj: File-like object
            extract_metadata: Whether to extract metadata
            
        Returns:
            Tuple of (text_content, metadata, pages)
        """
        # Reset file position to start
        file_obj.seek(0)
        
        # Read text content
        try:
            text_content = file_obj.read().decode('utf-8')
        except UnicodeDecodeError:
            # Try with another encoding if UTF-8 fails
            file_obj.seek(0)
            text_content = file_obj.read().decode('latin-1')
        
        # For text files, metadata is limited
        metadata = {
            'format': 'text/plain'
        }
        
        # Text files don't have pages
        pages = [text_content]
        
        return text_content, metadata, pages
    
    def _extract_from_html(
        self, 
        file_obj: BinaryIO, 
        extract_metadata: bool = True
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract text from HTML file
        
        Args:
            file_obj: File-like object
            extract_metadata: Whether to extract metadata
            
        Returns:
            Tuple of (text_content, metadata, pages)
        """
        if not HTML_SUPPORT:
            raise ImportError("BeautifulSoup library not installed")
            
        # Reset file position to start
        file_obj.seek(0)
        
        # Read HTML content
        try:
            html_content = file_obj.read().decode('utf-8')
        except UnicodeDecodeError:
            # Try with another encoding if UTF-8 fails
            file_obj.seek(0)
            html_content = file_obj.read().decode('latin-1')
        
        # Parse HTML and extract text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text_content = soup.get_text(separator='\n')
        
        # Clean up whitespace
        lines = (line.strip() for line in text_content.splitlines())
        text_content = '\n'.join(line for line in lines if line)
        
        # Extract metadata
        metadata = {}
        if extract_metadata:
            # Get title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.text
            
            # Get meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name')
                content = meta.get('content')
                if name and content:
                    metadata[name] = content
        
        # HTML doesn't have pages
        pages = [text_content]
        
        return text_content, metadata, pages
    
    def _extract_from_markdown(
        self, 
        file_obj: BinaryIO, 
        extract_metadata: bool = True
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract text from Markdown file
        
        Args:
            file_obj: File-like object
            extract_metadata: Whether to extract metadata
            
        Returns:
            Tuple of (text_content, metadata, pages)
        """
        # Reset file position to start
        file_obj.seek(0)
        
        # Read markdown content
        try:
            md_content = file_obj.read().decode('utf-8')
        except UnicodeDecodeError:
            # Try with another encoding if UTF-8 fails
            file_obj.seek(0)
            md_content = file_obj.read().decode('latin-1')
        
        # Extract front matter if present (YAML between --- markers)
        metadata = {}
        text_content = md_content
        
        if extract_metadata and md_content.startswith('---'):
            try:
                # Find end of front matter
                second_marker = md_content.find('---', 3)
                if second_marker > 0:
                    front_matter = md_content[3:second_marker].strip()
                    text_content = md_content[second_marker + 3:].strip()
                    
                    # Parse YAML front matter
                    try:
                        import yaml
                        metadata = yaml.safe_load(front_matter)
                    except (ImportError, yaml.YAMLError):
                        # Fall back to basic parsing if YAML module not available
                        for line in front_matter.splitlines():
                            if ':' in line:
                                key, value = line.split(':', 1)
                                metadata[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"Error parsing markdown front matter: {e}")
        
        # Convert markdown to plain text if the library is available
        if MARKDOWN_SUPPORT:
            from markdown import markdown
            from bs4 import BeautifulSoup
            
            html = markdown(text_content)
            text_content = BeautifulSoup(html, 'html.parser').get_text()
        
        # Markdown doesn't have pages
        pages = [text_content]
        
        return text_content, metadata, pages
    
    def _extract_from_csv(
        self, 
        file_obj: BinaryIO, 
        extract_metadata: bool = True
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract text from CSV file
        
        Args:
            file_obj: File-like object
            extract_metadata: Whether to extract metadata
            
        Returns:
            Tuple of (text_content, metadata, pages)
        """
        if not CSV_SUPPORT:
            raise ImportError("CSV library not installed")
            
        # Reset file position to start
        file_obj.seek(0)
        
        # Read CSV content
        try:
            # Try different encodings
            try:
                content = file_obj.read().decode('utf-8')
                file_obj.seek(0)
            except UnicodeDecodeError:
                content = file_obj.read().decode('latin-1')
                file_obj.seek(0)
            
            # Parse CSV
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            
            # Extract headers if present
            headers = rows[0] if rows else []
            
            # Convert to text
            text_lines = []
            for row in rows:
                text_lines.append('\t'.join(row))
            
            text_content = '\n'.join(text_lines)
            
            # Extract metadata
            metadata = {
                'format': 'text/csv',
                'rows': len(rows),
                'columns': len(headers) if headers else 0,
                'headers': headers if headers else []
            }
            
            # CSV doesn't have pages
            pages = [text_content]
            
            return text_content, metadata, pages
            
        except Exception as e:
            logger.error(f"Error extracting text from CSV: {e}")
            raise
    
    def _extract_from_json(
        self, 
        file_obj: BinaryIO, 
        extract_metadata: bool = True
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract text from JSON file
        
        Args:
            file_obj: File-like object
            extract_metadata: Whether to extract metadata
            
        Returns:
            Tuple of (text_content, metadata, pages)
        """
        if not JSON_SUPPORT:
            raise ImportError("JSON library not installed")
            
        # Reset file position to start
        file_obj.seek(0)
        
        # Read JSON content
        try:
            content = file_obj.read().decode('utf-8')
            
            # Parse JSON
            json_data = json.loads(content)
            
            # Convert to text
            if isinstance(json_data, dict):
                # Extract text from values
                text_parts = []
                for key, value in json_data.items():
                    if isinstance(value, (str, int, float, bool)):
                        text_parts.append(f"{key}: {value}")
                    elif value is None:
                        text_parts.append(f"{key}: null")
                    else:
                        # For nested structures, use JSON string
                        text_parts.append(f"{key}: {json.dumps(value)}")
                
                text_content = '\n'.join(text_parts)
            elif isinstance(json_data, list):
                # For lists, convert each item to text
                text_parts = []
                for item in json_data:
                    if isinstance(item, (str, int, float, bool)):
                        text_parts.append(str(item))
                    elif item is None:
                        text_parts.append("null")
                    else:
                        # For nested structures, use JSON string
                        text_parts.append(json.dumps(item))
                
                text_content = '\n'.join(text_parts)
            else:
                # For scalar values, convert to string
                text_content = str(json_data)
            
            # Extract metadata
            metadata = {
                'format': 'application/json',
                'structure': type(json_data).__name__,
            }
            
            if isinstance(json_data, dict):
                metadata['keys'] = list(json_data.keys())
                metadata['top_level_keys'] = len(json_data)
            elif isinstance(json_data, list):
                metadata['items'] = len(json_data)
            
            # JSON doesn't have pages
            pages = [text_content]
            
            return text_content, metadata, pages
            
        except Exception as e:
            logger.error(f"Error extracting text from JSON: {e}")
            raise
