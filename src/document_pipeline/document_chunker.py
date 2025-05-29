"""
Document Chunking Module
Provides utilities for splitting documents into manageable chunks for embedding
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass
import uuid
import math

logger = logging.getLogger(__name__)

# Try to import spaCy if available
try:
    import spacy
    from spacy.language import Language
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Try to import nltk if available
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
    # Download required NLTK data if not present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
except ImportError:
    NLTK_AVAILABLE = False


class ChunkingStrategy:
    """Enumeration of document chunking strategies"""
    FIXED_SIZE = "fixed_size"      # Split into chunks of roughly equal size
    PARAGRAPH = "paragraph"        # Split by paragraphs
    SENTENCE = "sentence"          # Split by sentences
    HYBRID = "hybrid"              # Combine paragraphs until a size limit is reached
    SEMANTIC = "semantic"          # Split by semantic boundaries using NLP
    OVERLAP = "overlap"            # Fixed size with overlapping content


@dataclass
class ChunkingConfig:
    """Configuration for document chunking"""
    strategy: str = ChunkingStrategy.HYBRID
    chunk_size: int = 512           # Target number of characters per chunk
    chunk_overlap: int = 50         # Number of characters to overlap between chunks
    min_chunk_size: int = 100       # Minimum chunk size to keep
    max_chunk_size: int = 1024      # Maximum chunk size
    paragraph_separator: str = "\n\n"  # Pattern to identify paragraphs
    split_by_headings: bool = True    # Whether to split by headings (e.g. # Title)
    respect_sections: bool = True     # Try to keep sections together when possible
    use_spacy: bool = False           # Whether to use spaCy for better sentence splitting
    spacy_model: str = "en_core_web_sm"  # spaCy model to use for sentence splitting


class DocumentChunker:
    """Utility for splitting documents into chunks for embedding"""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """Initialize document chunker
        
        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkingConfig()
        
        # Initialize spaCy if requested and available
        self.nlp = None
        if self.config.use_spacy and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(self.config.spacy_model)
                logger.info(f"Loaded spaCy model: {self.config.spacy_model}")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model {self.config.spacy_model}: {e}")
                logger.warning("Falling back to basic sentence tokenization")
    
    def chunk_document(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Split document into chunks
        
        Args:
            text: Document text content
            metadata: Optional document metadata to include with each chunk
            document_id: Document ID (generated if not provided)
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text:
            return []
        
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Create base metadata dict if none provided
        if metadata is None:
            metadata = {}
        
        # Apply chunking strategy
        if self.config.strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(text)
        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(text)
        elif self.config.strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(text)
        elif self.config.strategy == ChunkingStrategy.OVERLAP:
            chunks = self._chunk_with_overlap(text)
        elif self.config.strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._chunk_semantic(text)
        else:  # Default to HYBRID
            chunks = self._chunk_hybrid(text)
        
        # Create result objects with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            # Skip empty chunks
            if not chunk_text.strip():
                continue
                
            # Create chunk ID
            chunk_id = f"{document_id}_{i+1}"
            
            # Create chunk object
            chunk = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "chunk_index": i,
                "content": chunk_text,
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
            }
            
            # Add document metadata
            for key, value in metadata.items():
                # Don't override existing chunk properties
                if key not in chunk:
                    chunk[f"document_{key}"] = value
            
            result.append(chunk)
        
        logger.info(f"Split document into {len(result)} chunks using {self.config.strategy} strategy")
        return result
    
    def _chunk_fixed_size(self, text: str) -> List[str]:
        """Split text into fixed-size chunks
        
        Args:
            text: Document text
            
        Returns:
            List of text chunks
        """
        # Split text into words
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            # Add word length plus a space
            word_size = len(word) + 1
            
            # If adding this word would exceed the chunk size, finalize current chunk
            if current_size + word_size > self.config.chunk_size and current_size > self.config.min_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Add word to current chunk
            current_chunk.append(word)
            current_size += word_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _chunk_by_paragraph(self, text: str) -> List[str]:
        """Split text by paragraphs
        
        Args:
            text: Document text
            
        Returns:
            List of text chunks
        """
        # Split by paragraph separator
        paragraphs = text.split(self.config.paragraph_separator)
        
        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs]
        paragraphs = [p for p in paragraphs if p]
        
        # Handle paragraphs that exceed max_chunk_size
        result = []
        for para in paragraphs:
            if len(para) <= self.config.max_chunk_size:
                result.append(para)
            else:
                # Split large paragraphs using fixed size chunking
                result.extend(self._chunk_fixed_size(para))
        
        return result
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        """Split text by sentences
        
        Args:
            text: Document text
            
        Returns:
            List of text chunks
        """
        # Use spaCy for better sentence tokenization if available
        if self.nlp is not None:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
        elif NLTK_AVAILABLE:
            # Use NLTK sentence tokenizer
            sentences = sent_tokenize(text)
        else:
            # Fallback to simple regex-based sentence splitting
            sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Combine sentences until we reach target chunk size
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence) + 1  # +1 for space
            
            # If adding this sentence would exceed the chunk size, finalize current chunk
            if current_size + sentence_size > self.config.chunk_size and current_size > self.config.min_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _chunk_with_overlap(self, text: str) -> List[str]:
        """Split text into chunks with overlap
        
        Args:
            text: Document text
            
        Returns:
            List of text chunks
        """
        # Calculate how much text to include in each chunk
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        # Ensure text is long enough to chunk
        if len(text) <= chunk_size:
            return [text]
        
        # Calculate offsets
        stride = chunk_size - overlap
        
        # Split text with overlap
        chunks = []
        for i in range(0, len(text), stride):
            # Get chunk
            chunk = text[i:i + chunk_size]
            
            # Only add if it meets minimum size
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
            
            # Stop if we've reached the end of the text
            if i + chunk_size >= len(text):
                break
        
        return chunks
    
    def _chunk_semantic(self, text: str) -> List[str]:
        """Split text based on semantic boundaries
        
        Args:
            text: Document text
            
        Returns:
            List of text chunks
        """
        # This requires spaCy
        if not SPACY_AVAILABLE or self.nlp is None:
            logger.warning("spaCy not available, falling back to hybrid chunking")
            return self._chunk_hybrid(text)
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Find semantic boundaries (sentences, section headers, etc.)
        boundaries = []
        
        # Split by sentences
        for sent in doc.sents:
            boundaries.append((sent.start_char, sent.end_char))
        
        # Sort boundaries by start position
        boundaries.sort(key=lambda x: x[0])
        
        # Combine chunks until we reach target size
        chunks = []
        current_chunk = []
        current_size = 0
        
        for start, end in boundaries:
            # Get sentence
            sentence = text[start:end].strip()
            sentence_size = len(sentence) + 1  # +1 for space
            
            # If adding this sentence would exceed the chunk size, finalize current chunk
            if current_size + sentence_size > self.config.chunk_size and current_size > self.config.min_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _chunk_hybrid(self, text: str) -> List[str]:
        """Split text using a hybrid approach combining paragraphs until size limit
        
        Args:
            text: Document text
            
        Returns:
            List of text chunks
        """
        # Split by paragraph first
        paragraphs = text.split(self.config.paragraph_separator)
        paragraphs = [p.strip() for p in paragraphs]
        paragraphs = [p for p in paragraphs if p]
        
        # Check for headings if configured
        if self.config.split_by_headings:
            # Define patterns for Markdown headings
            heading_pattern = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)
            
            # Refine paragraph splits to break at headings
            refined_paragraphs = []
            for para in paragraphs:
                # Check for headings within paragraph
                heading_matches = heading_pattern.finditer(para)
                last_end = 0
                
                for match in heading_matches:
                    if match.start() > last_end:
                        # Add text before heading
                        refined_paragraphs.append(para[last_end:match.start()].strip())
                    
                    # Add heading as separate paragraph
                    refined_paragraphs.append(para[match.start():match.end()].strip())
                    last_end = match.end()
                
                # Add remaining text after last heading
                if last_end < len(para):
                    refined_paragraphs.append(para[last_end:].strip())
            
            paragraphs = [p for p in refined_paragraphs if p]
        
        # Combine paragraphs until we reach target size
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para) + 2  # +2 for newline characters
            
            # Special handling for large paragraphs
            if para_size > self.config.max_chunk_size:
                # If we have content in the current chunk, add it first
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph
                para_chunks = self._chunk_fixed_size(para)
                chunks.extend(para_chunks)
                continue
            
            # If adding this paragraph would exceed the chunk size, finalize current chunk
            if current_size + para_size > self.config.chunk_size and current_size > self.config.min_chunk_size:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Add paragraph to current chunk
            current_chunk.append(para)
            current_size += para_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def split_by_tokens(
        self, 
        text: str, 
        max_tokens: int = 512,
        tokenizer: Optional[Callable[[str], List[str]]] = None
    ) -> List[str]:
        """Split text to ensure chunks don't exceed max token count
        
        Args:
            text: Document text
            max_tokens: Maximum tokens per chunk
            tokenizer: Optional custom tokenizer function
            
        Returns:
            List of text chunks
        """
        # Default tokenization (approximated)
        if tokenizer is None:
            # Simple whitespace tokenization with some cleanup
            def default_tokenizer(text: str) -> List[str]:
                # Remove extra whitespace
                text = re.sub(r'\s+', ' ', text)
                # Split on whitespace
                return text.split()
            
            tokenizer = default_tokenizer
        
        # Tokenize the text
        tokens = tokenizer(text)
        
        # Simple chunking based on token count
        chunks = []
        current_chunk = []
        
        for token in tokens:
            if len(current_chunk) >= max_tokens:
                # Join tokens back to text
                chunks.append(' '.join(current_chunk))
                current_chunk = []
            
            current_chunk.append(token)
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def create_metadata_for_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        document_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create metadata for each chunk based on document metadata
        
        Args:
            chunks: List of chunk objects
            document_metadata: Original document metadata
            
        Returns:
            Updated list of chunk objects with metadata
        """
        for chunk in chunks:
            # Add document metadata to chunk
            for key, value in document_metadata.items():
                # Don't override existing chunk properties
                if key not in chunk:
                    chunk[f"document_{key}"] = value
        
        return chunks
