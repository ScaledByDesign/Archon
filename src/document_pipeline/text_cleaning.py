"""
Text Cleaning Module
Provides utilities for cleaning and preprocessing extracted text
"""

import re
import logging
from typing import List, Dict, Any, Optional, Callable, Union
import unicodedata
from enum import Enum
from dataclasses import dataclass

# Import spaCy if available
try:
    import spacy
    from spacy.language import Language
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)


class CleaningLevel(str, Enum):
    """Text cleaning level options"""
    MINIMAL = "minimal"     # Basic whitespace normalization and unicode handling
    STANDARD = "standard"   # Remove most non-content elements but preserve structure
    AGGRESSIVE = "aggressive"  # Strip everything except semantic content


@dataclass
class TextCleaningConfig:
    """Configuration for text cleaning"""
    level: CleaningLevel = CleaningLevel.STANDARD
    
    # Cleaning options
    normalize_whitespace: bool = True
    normalize_unicode: bool = True
    remove_urls: bool = True
    remove_emails: bool = True
    remove_phone_numbers: bool = False
    remove_html_tags: bool = True
    remove_markdown: bool = True
    remove_special_characters: bool = False
    remove_punctuation: bool = False
    remove_numbers: bool = False
    remove_stopwords: bool = False
    lowercase: bool = True
    
    # spaCy options
    use_spacy: bool = True
    spacy_model: str = "en_core_web_sm"
    remove_named_entities: bool = False
    lemmatize: bool = False
    
    # Custom patterns to remove (list of regex patterns)
    custom_patterns: List[str] = None
    
    # Token length filtering
    min_token_length: int = 2
    max_token_length: int = 100


class TextCleaner:
    """Text cleaner for preprocessing document content"""
    
    def __init__(self, config: Optional[TextCleaningConfig] = None):
        """Initialize text cleaner
        
        Args:
            config: Cleaning configuration
        """
        self.config = config or TextCleaningConfig()
        
        # Initialize spaCy if requested and available
        self.nlp = None
        if self.config.use_spacy and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(self.config.spacy_model)
                logger.info(f"Loaded spaCy model: {self.config.spacy_model}")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model {self.config.spacy_model}: {e}")
                logger.warning("Falling back to basic cleaning without spaCy")
        elif self.config.use_spacy and not SPACY_AVAILABLE:
            logger.warning("spaCy requested but not available, falling back to basic cleaning")
        
        # Compile regex patterns
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for cleaning
        
        Returns:
            Dictionary of compiled regex patterns
        """
        patterns = {}
        
        # URL pattern
        patterns['url'] = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Email pattern
        patterns['email'] = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )
        
        # Phone number pattern
        patterns['phone'] = re.compile(
            r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
        )
        
        # HTML tags pattern
        patterns['html'] = re.compile(
            r'<[^>]+>'
        )
        
        # Markdown pattern - headers, bold, italic, links, lists, code blocks
        patterns['markdown'] = re.compile(
            r'(#+\s|\*\*|\*|__|\[.+?\]\(.+?\)|```[\s\S]*?```|`.*?`|^\s*[\*\-\+]\s|^\s*\d+\.\s|\n\s*[-\*\=]{3,})'
        )
        
        # Special characters
        patterns['special_chars'] = re.compile(
            r'[^\w\s]'
        )
        
        # Numbers
        patterns['numbers'] = re.compile(
            r'\d+'
        )
        
        # Whitespace (multiple spaces, tabs, newlines)
        patterns['whitespace'] = re.compile(
            r'\s+'
        )
        
        # Add custom patterns if provided
        if self.config.custom_patterns:
            for i, pattern in enumerate(self.config.custom_patterns):
                patterns[f'custom_{i}'] = re.compile(pattern)
        
        return patterns
    
    def clean(self, text: str) -> str:
        """Clean and preprocess text
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Apply cleaning based on level
        if self.config.level == CleaningLevel.MINIMAL:
            return self._minimal_cleaning(text)
        elif self.config.level == CleaningLevel.AGGRESSIVE:
            return self._aggressive_cleaning(text)
        else:
            return self._standard_cleaning(text)
    
    def _minimal_cleaning(self, text: str) -> str:
        """Apply minimal text cleaning
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Basic cleaning for minimal level
        if self.config.normalize_unicode:
            text = unicodedata.normalize('NFKC', text)
        
        if self.config.normalize_whitespace:
            text = self.patterns['whitespace'].sub(' ', text)
            text = text.strip()
        
        if self.config.lowercase:
            text = text.lower()
        
        return text
    
    def _standard_cleaning(self, text: str) -> str:
        """Apply standard text cleaning
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Apply minimal cleaning first
        text = self._minimal_cleaning(text)
        
        # Apply additional standard cleaning
        if self.config.remove_urls:
            text = self.patterns['url'].sub(' ', text)
        
        if self.config.remove_emails:
            text = self.patterns['email'].sub(' ', text)
        
        if self.config.remove_phone_numbers:
            text = self.patterns['phone'].sub(' ', text)
        
        if self.config.remove_html_tags:
            text = self.patterns['html'].sub(' ', text)
        
        if self.config.remove_markdown:
            text = self.patterns['markdown'].sub(' ', text)
        
        # Apply custom patterns
        if self.config.custom_patterns:
            for i in range(len(self.config.custom_patterns)):
                pattern_key = f'custom_{i}'
                text = self.patterns[pattern_key].sub(' ', text)
        
        # Normalize whitespace again after all substitutions
        if self.config.normalize_whitespace:
            text = self.patterns['whitespace'].sub(' ', text)
            text = text.strip()
        
        return text
    
    def _aggressive_cleaning(self, text: str) -> str:
        """Apply aggressive text cleaning
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Apply standard cleaning first
        text = self._standard_cleaning(text)
        
        # Apply additional aggressive cleaning
        if self.config.remove_special_characters:
            text = self.patterns['special_chars'].sub(' ', text)
        
        if self.config.remove_numbers:
            text = self.patterns['numbers'].sub(' ', text)
        
        # Use spaCy for advanced cleaning if available
        if self.nlp is not None:
            # Process with spaCy
            doc = self.nlp(text)
            
            # Filter tokens
            tokens = []
            for token in doc:
                # Skip stopwords if configured
                if self.config.remove_stopwords and token.is_stop:
                    continue
                
                # Skip named entities if configured
                if self.config.remove_named_entities and token.ent_type_:
                    continue
                
                # Apply lemmatization if configured
                if self.config.lemmatize:
                    token_text = token.lemma_
                else:
                    token_text = token.text
                
                # Filter by token length
                if (len(token_text) >= self.config.min_token_length and 
                    len(token_text) <= self.config.max_token_length):
                    tokens.append(token_text)
            
            # Reconstruct text
            text = ' '.join(tokens)
        else:
            # Fallback if spaCy not available - simple token length filtering
            tokens = text.split()
            tokens = [
                t for t in tokens 
                if len(t) >= self.config.min_token_length and 
                len(t) <= self.config.max_token_length
            ]
            text = ' '.join(tokens)
        
        # Final whitespace normalization
        if self.config.normalize_whitespace:
            text = self.patterns['whitespace'].sub(' ', text)
            text = text.strip()
        
        return text
    
    def clean_document_chunks(self, chunks: List[str]) -> List[str]:
        """Clean a list of document chunks
        
        Args:
            chunks: List of text chunks to clean
            
        Returns:
            List of cleaned text chunks
        """
        return [self.clean(chunk) for chunk in chunks]
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current cleaning configuration
        
        Returns:
            Dictionary of configuration settings
        """
        return {
            "level": self.config.level,
            "use_spacy": self.config.use_spacy and self.nlp is not None,
            "spacy_model": self.config.spacy_model if self.nlp is not None else None,
            "remove_stopwords": self.config.remove_stopwords,
            "remove_named_entities": self.config.remove_named_entities,
            "lemmatize": self.config.lemmatize,
            "lowercase": self.config.lowercase,
            "filters": {
                "urls": self.config.remove_urls,
                "emails": self.config.remove_emails,
                "html": self.config.remove_html_tags,
                "markdown": self.config.remove_markdown,
                "special_chars": self.config.remove_special_characters,
                "numbers": self.config.remove_numbers,
                "phone_numbers": self.config.remove_phone_numbers,
            },
            "min_token_length": self.config.min_token_length,
            "max_token_length": self.config.max_token_length,
            "custom_patterns_count": len(self.config.custom_patterns) if self.config.custom_patterns else 0
        }
