"""
Embedding Generator Module
Provides utilities for generating vector embeddings from document text
"""

import os
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

# Import sentence-transformers if available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Import LiteLLM for OpenAI-compatible embedding APIs
try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class EmbeddingModel(str, Enum):
    """Supported embedding models"""
    # Sentence Transformers models
    MINILM_L6_V2 = "all-MiniLM-L6-v2"  # 384-dim, fast, good quality
    MPNET_BASE_V2 = "all-mpnet-base-v2"  # 768-dim, higher quality
    MULTILINGUAL_MINILM = "paraphrase-multilingual-MiniLM-L12-v2"  # 384-dim multilingual
    
    # OpenAI models via LiteLLM
    OPENAI_ADA_002 = "text-embedding-ada-002"  # 1536-dim
    OPENAI_3_SMALL = "text-embedding-3-small"  # 1536-dim
    OPENAI_3_LARGE = "text-embedding-3-large"  # 3072-dim
    
    # Custom model path (for loading from disk)
    CUSTOM = "custom"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model_name: EmbeddingModel = EmbeddingModel.MINILM_L6_V2
    custom_model_path: Optional[str] = None
    batch_size: int = 32
    show_progress: bool = False
    use_gpu: bool = False
    device: Optional[str] = None  # 'cpu', 'cuda', or 'cuda:0', 'cuda:1', etc.
    cache_folder: Optional[str] = None  # Path to cache folder for models
    
    # LiteLLM settings
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    litellm_proxy_url: Optional[str] = None
    
    # Dimension settings
    normalize_embeddings: bool = True
    
    # Additional settings
    timeout: int = 60
    retry_count: int = 3
    
    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create config from environment variables"""
        # Get model name from environment, defaulting to MINILM_L6_V2
        model_name_str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Try to convert to enum, default to CUSTOM if not a standard model
        try:
            model_name = EmbeddingModel(model_name_str)
        except ValueError:
            model_name = EmbeddingModel.CUSTOM
            
        # Create config
        return cls(
            model_name=model_name,
            custom_model_path=model_name_str if model_name == EmbeddingModel.CUSTOM else None,
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
            show_progress=os.getenv("EMBEDDING_SHOW_PROGRESS", "false").lower() == "true",
            use_gpu=os.getenv("EMBEDDING_USE_GPU", "false").lower() == "true",
            device=os.getenv("EMBEDDING_DEVICE", None),
            cache_folder=os.getenv("EMBEDDING_CACHE_FOLDER", None),
            api_key=os.getenv("OPENAI_API_KEY", None),
            api_base=os.getenv("OPENAI_API_BASE", None),
            litellm_proxy_url=os.getenv("LITELLM_PROXY_URL", None),
            normalize_embeddings=os.getenv("EMBEDDING_NORMALIZE", "true").lower() == "true",
            timeout=int(os.getenv("EMBEDDING_TIMEOUT", "60")),
            retry_count=int(os.getenv("EMBEDDING_RETRY_COUNT", "3"))
        )


class EmbeddingGenerator:
    """Generator for text embeddings"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embedding generator
        
        Args:
            config: Embedding configuration
        """
        self.config = config or EmbeddingConfig.from_env()
        self.model = None
        self.embedding_dimension = None
        
        # Load embedding model
        self._load_model()
    
    def _load_model(self):
        """Load embedding model based on configuration"""
        model_name = self.config.model_name
        
        try:
            # Check if using OpenAI models via LiteLLM
            if model_name in [EmbeddingModel.OPENAI_ADA_002, 
                              EmbeddingModel.OPENAI_3_SMALL, 
                              EmbeddingModel.OPENAI_3_LARGE]:
                if not LITELLM_AVAILABLE:
                    raise ImportError("LiteLLM not installed. Please install with 'pip install litellm'")
                
                # For OpenAI models, we don't actually load a model
                # just set up the configuration for later API calls
                self.model = model_name.value
                
                # Set dimensions based on model
                if model_name == EmbeddingModel.OPENAI_3_LARGE:
                    self.embedding_dimension = 3072
                else:
                    self.embedding_dimension = 1536
                
                # Configure LiteLLM if not using a proxy
                if not self.config.litellm_proxy_url:
                    if self.config.api_key:
                        litellm.api_key = self.config.api_key
                    if self.config.api_base:
                        litellm.api_base = self.config.api_base
                
                logger.info(f"Configured for {model_name.value} via LiteLLM")
                
            # Sentence Transformers models
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                # Load model configuration
                model_kwargs = {}
                
                if self.config.cache_folder:
                    model_kwargs['cache_folder'] = self.config.cache_folder
                
                if self.config.device:
                    model_kwargs['device'] = self.config.device
                
                # Load the appropriate model
                if model_name == EmbeddingModel.CUSTOM:
                    # Load custom model from path
                    if not self.config.custom_model_path:
                        raise ValueError("Custom model path must be provided for CUSTOM model type")
                    
                    self.model = SentenceTransformer(self.config.custom_model_path, **model_kwargs)
                else:
                    # Load standard model
                    self.model = SentenceTransformer(model_name.value, **model_kwargs)
                
                # Get embedding dimension
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
                
                logger.info(f"Loaded {model_name.value} with dimension {self.embedding_dimension}")
            else:
                raise ImportError("sentence-transformers not installed. Please install with 'pip install sentence-transformers'")
                
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise
    
    def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (as lists of floats)
        """
        if not texts:
            return []
        
        # Check if using OpenAI models via LiteLLM
        if isinstance(self.model, str) and self.model in [m.value for m in [
            EmbeddingModel.OPENAI_ADA_002,
            EmbeddingModel.OPENAI_3_SMALL, 
            EmbeddingModel.OPENAI_3_LARGE
        ]]:
            return self._generate_with_litellm(texts)
        
        # Otherwise use Sentence Transformers
        return self._generate_with_sentence_transformers(texts)
    
    def _generate_with_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (as lists of floats)
        """
        try:
            # Track timing
            start_time = time.time()
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=self.config.batch_size,
                show_progress_bar=self.config.show_progress,
                normalize_embeddings=self.config.normalize_embeddings
            )
            
            # Convert numpy arrays to lists
            embeddings_list = embeddings.tolist()
            
            # Log timing info
            elapsed = time.time() - start_time
            logger.info(f"Generated {len(texts)} embeddings with {self.config.model_name.value} in {elapsed:.2f}s")
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def _generate_with_litellm(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using LiteLLM (OpenAI API)
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (as lists of floats)
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM not installed. Please install with 'pip install litellm'")
        
        # Track timing and results
        start_time = time.time()
        all_embeddings = []
        
        try:
            # Process in batches
            for i in range(0, len(texts), self.config.batch_size):
                batch = texts[i:i + self.config.batch_size]
                
                # Prepare for retries
                retry_count = 0
                success = False
                
                while not success and retry_count < self.config.retry_count:
                    try:
                        # Use litellm for embedding
                        if self.config.litellm_proxy_url:
                            # Use LiteLLM proxy
                            response = litellm.embedding(
                                model=self.model,
                                input=batch,
                                api_base=self.config.litellm_proxy_url,
                                timeout=self.config.timeout
                            )
                        else:
                            # Use direct API
                            response = litellm.embedding(
                                model=self.model,
                                input=batch,
                                timeout=self.config.timeout
                            )
                        
                        # Extract embeddings from response
                        batch_embeddings = [item.embedding for item in response.data]
                        all_embeddings.extend(batch_embeddings)
                        
                        success = True
                        
                    except Exception as e:
                        # Retry on failure
                        retry_count += 1
                        logger.warning(f"Embedding batch failed (attempt {retry_count}): {str(e)}")
                        
                        if retry_count >= self.config.retry_count:
                            logger.error(f"Failed to generate embeddings after {self.config.retry_count} retries")
                            raise
                        
                        # Wait before retrying
                        time.sleep(1 * retry_count)  # Exponential backoff
            
            # Log timing info
            elapsed = time.time() - start_time
            logger.info(f"Generated {len(texts)} embeddings with {self.model} in {elapsed:.2f}s")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings with LiteLLM: {e}")
            raise
    
    def generate_single(self, text: str) -> List[float]:
        """Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector as list of floats
        """
        if not text:
            # For empty text, return zero vector of correct dimension
            return [0.0] * self.embedding_dimension
        
        result = self.generate([text])
        return result[0] if result else [0.0] * self.embedding_dimension
    
    def generate_document_chunks(
        self, 
        chunks: List[str],
        metadata: List[Dict[str, Any]] = None
    ) -> Tuple[List[List[float]], List[Dict[str, Any]]]:
        """Generate embeddings for document chunks
        
        Args:
            chunks: List of text chunks
            metadata: Optional list of metadata dicts for each chunk
            
        Returns:
            Tuple of (embeddings, updated_metadata)
        """
        if not chunks:
            return [], []
        
        # Generate embeddings
        embeddings = self.generate(chunks)
        
        # Add embedding metadata if provided
        if metadata:
            for i, embedding in enumerate(embeddings):
                if i < len(metadata):
                    metadata[i]['embedding_model'] = self.config.model_name.value
                    metadata[i]['embedding_dimension'] = self.embedding_dimension
                    metadata[i]['embedding_timestamp'] = time.time()
        
        return embeddings, metadata
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.config.model_name.value,
            "custom_model_path": self.config.custom_model_path,
            "embedding_dimension": self.embedding_dimension,
            "normalize_embeddings": self.config.normalize_embeddings,
            "use_gpu": self.config.use_gpu,
            "device": self.config.device or "default",
            "batch_size": self.config.batch_size,
            "provider": "sentence-transformers" if not isinstance(self.model, str) else "litellm",
        }
