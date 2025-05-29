"""
Document Processor Module
Manages the end-to-end document processing pipeline
"""

import os
import logging
import json
import time
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, BinaryIO
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback

# Import pipeline components
from .text_extraction import TextExtractor
from .text_cleaning import TextCleaner
from .document_chunker import DocumentChunker, ChunkingConfig
from .embedding_generator import EmbeddingGenerator, EmbeddingConfig

# Import vector store client
from src.vector_store.vector_store import QdrantVectorStore
from src.db.mongodb_client import MongoDBClient

# Import observability
try:
    from src.observability.langfuse_tracer import LangfuseTracer
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Status of document processing"""
    PENDING = "pending"
    EXTRACTING = "extracting"
    CLEANING = "cleaning"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingStats:
    """Statistics for document processing"""
    extraction_time_ms: Optional[int] = None
    cleaning_time_ms: Optional[int] = None
    chunking_time_ms: Optional[int] = None
    embedding_time_ms: Optional[int] = None
    indexing_time_ms: Optional[int] = None
    total_time_ms: Optional[int] = None
    char_count: Optional[int] = None
    chunk_count: Optional[int] = None
    total_tokens: Optional[int] = None
    error_count: int = 0


@dataclass
class DocumentProcessorConfig:
    """Configuration for document processor"""
    # Collection names
    documents_collection: str = "documents"
    chunks_collection: str = "document_chunks"
    vector_collection: str = "document_embeddings"
    
    # Vector dimensions
    vector_size: int = 384  # Default for all-MiniLM-L6-v2
    
    # Processing options
    clean_text: bool = True
    chunk_documents: bool = True
    generate_embeddings: bool = True
    store_in_vector_db: bool = True
    
    # Chunking configuration
    chunking_config: ChunkingConfig = field(default_factory=ChunkingConfig)
    
    # Embedding configuration
    embedding_config: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # Tracing configuration
    enable_tracing: bool = True
    
    @classmethod
    def from_env(cls) -> "DocumentProcessorConfig":
        """Create configuration from environment variables"""
        # Create chunking config
        chunking_config = ChunkingConfig(
            strategy=os.getenv("DOCUMENT_CHUNKING_STRATEGY", "hybrid"),
            chunk_size=int(os.getenv("DOCUMENT_CHUNK_SIZE", "512")),
            chunk_overlap=int(os.getenv("DOCUMENT_CHUNK_OVERLAP", "50")),
            min_chunk_size=int(os.getenv("DOCUMENT_MIN_CHUNK_SIZE", "100")),
            max_chunk_size=int(os.getenv("DOCUMENT_MAX_CHUNK_SIZE", "1024")),
            use_spacy=os.getenv("DOCUMENT_USE_SPACY", "false").lower() == "true"
        )
        
        # Create embedding config
        embedding_config = EmbeddingConfig.from_env()
        
        # Create processor config
        return cls(
            documents_collection=os.getenv("MONGODB_DOCUMENTS_COLLECTION", "documents"),
            chunks_collection=os.getenv("MONGODB_CHUNKS_COLLECTION", "document_chunks"),
            vector_collection=os.getenv("VECTOR_COLLECTION", "document_embeddings"),
            vector_size=int(os.getenv("VECTOR_SIZE", "384")),
            clean_text=os.getenv("DOCUMENT_CLEAN_TEXT", "true").lower() == "true",
            chunk_documents=os.getenv("DOCUMENT_CHUNK_DOCUMENTS", "true").lower() == "true",
            generate_embeddings=os.getenv("DOCUMENT_GENERATE_EMBEDDINGS", "true").lower() == "true",
            store_in_vector_db=os.getenv("DOCUMENT_STORE_IN_VECTOR_DB", "true").lower() == "true",
            chunking_config=chunking_config,
            embedding_config=embedding_config,
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true"
        )


class DocumentProcessor:
    """Processor for end-to-end document processing"""
    
    def __init__(
        self,
        config: Optional[DocumentProcessorConfig] = None,
        mongodb_client: Optional[MongoDBClient] = None,
        vector_store: Optional[QdrantVectorStore] = None
    ):
        """Initialize document processor
        
        Args:
            config: Processor configuration
            mongodb_client: MongoDB client
            vector_store: Vector store client
        """
        self.config = config or DocumentProcessorConfig.from_env()
        
        # Initialize MongoDB client if not provided
        if mongodb_client:
            self.mongodb_client = mongodb_client
        else:
            self.mongodb_client = MongoDBClient()
        
        # Initialize vector store if not provided
        if vector_store:
            self.vector_store = vector_store
        else:
            self.vector_store = QdrantVectorStore()
        
        # Create pipeline components
        self.extractor = TextExtractor()
        self.cleaner = TextCleaner()
        self.chunker = DocumentChunker(config=self.config.chunking_config)
        self.embedding_generator = EmbeddingGenerator(config=self.config.embedding_config)
        
        # Initialize tracer if Langfuse is available
        self.tracer = None
        if self.config.enable_tracing and LANGFUSE_AVAILABLE:
            self.tracer = LangfuseTracer()
            logger.info("Langfuse tracing enabled for document processing")
    
    async def setup(self):
        """Set up necessary infrastructure for document processing"""
        # Ensure vector collection exists with correct configuration
        vector_size = self.config.vector_size
        
        # If we're using the embedding generator, get its actual dimension
        if self.config.generate_embeddings:
            vector_size = self.embedding_generator.embedding_dimension
        
        # Create vector collection if it doesn't exist
        if not await self.vector_store.collection_exists(self.config.vector_collection):
            logger.info(f"Creating vector collection: {self.config.vector_collection}")
            await self.vector_store.create_collection(
                self.config.vector_collection,
                vector_size
            )
        else:
            logger.info(f"Vector collection already exists: {self.config.vector_collection}")
    
    async def process_document(
        self,
        file_content: Union[bytes, BinaryIO],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a document from start to finish
        
        Args:
            file_content: Binary file content
            filename: Original filename
            metadata: Additional document metadata
            document_id: Document ID (generated if not provided)
            trace_id: Trace ID for observability
            
        Returns:
            Document metadata with processing results
        """
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add basic metadata
        document_metadata = {
            "document_id": document_id,
            "filename": filename,
            "processing_started": datetime.now().isoformat(),
            "status": ProcessingStatus.PENDING,
            **metadata
        }
        
        # Initialize processing stats
        stats = ProcessingStats()
        
        # Create trace if enabled
        trace = None
        if self.tracer:
            trace = self.tracer.start_trace(
                name="document_processing",
                id=trace_id or document_id,
                metadata={
                    "document_id": document_id,
                    "filename": filename
                }
            )
        
        try:
            # Store document record in MongoDB
            await self.mongodb_client.insert_document(
                self.config.documents_collection,
                document_metadata
            )
            
            # Extract text
            start_time = time.time()
            document_metadata["status"] = ProcessingStatus.EXTRACTING
            await self._update_document(document_metadata)
            
            # Use the extractor to get text content
            with trace.span("text_extraction") if trace else nullcontext():
                extraction_result = self.extractor.extract_text(
                    file_content=file_content,
                    filename=filename,
                    document_id=document_id
                )
            
            # Update stats
            stats.extraction_time_ms = int((time.time() - start_time) * 1000)
            stats.char_count = len(extraction_result.text)
            
            # Update document metadata with extraction results
            document_metadata.update({
                "content_type": extraction_result.content_type,
                "page_count": extraction_result.page_count,
                "char_count": stats.char_count,
                "extraction_time_ms": stats.extraction_time_ms
            })
            
            # Clean text if enabled
            if self.config.clean_text:
                start_time = time.time()
                document_metadata["status"] = ProcessingStatus.CLEANING
                await self._update_document(document_metadata)
                
                with trace.span("text_cleaning") if trace else nullcontext():
                    cleaned_text = self.cleaner.clean_text(extraction_result.text)
                
                # Update stats
                stats.cleaning_time_ms = int((time.time() - start_time) * 1000)
            else:
                cleaned_text = extraction_result.text
            
            # Chunk document if enabled
            if self.config.chunk_documents:
                start_time = time.time()
                document_metadata["status"] = ProcessingStatus.CHUNKING
                await self._update_document(document_metadata)
                
                with trace.span("document_chunking") if trace else nullcontext():
                    chunks = self.chunker.chunk_document(
                        text=cleaned_text,
                        metadata=document_metadata,
                        document_id=document_id
                    )
                
                # Update stats
                stats.chunking_time_ms = int((time.time() - start_time) * 1000)
                stats.chunk_count = len(chunks)
                
                # Store chunks in MongoDB
                for chunk in chunks:
                    await self.mongodb_client.insert_document(
                        self.config.chunks_collection,
                        chunk
                    )
                
                # Update document metadata
                document_metadata.update({
                    "chunk_count": stats.chunk_count,
                    "chunking_time_ms": stats.chunking_time_ms
                })
            else:
                # Create a single chunk for the entire document
                chunks = [{
                    "chunk_id": f"{document_id}_1",
                    "document_id": document_id,
                    "chunk_index": 0,
                    "content": cleaned_text,
                    "char_count": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                }]
                stats.chunk_count = 1
            
            # Generate embeddings if enabled
            if self.config.generate_embeddings:
                start_time = time.time()
                document_metadata["status"] = ProcessingStatus.EMBEDDING
                await self._update_document(document_metadata)
                
                # Extract text content from chunks
                chunk_texts = [chunk["content"] for chunk in chunks]
                
                with trace.span("embedding_generation") if trace else nullcontext():
                    embeddings, _ = self.embedding_generator.generate_document_chunks(
                        chunks=chunk_texts,
                        metadata=None
                    )
                
                # Update stats
                stats.embedding_time_ms = int((time.time() - start_time) * 1000)
                
                # Add embeddings to chunks
                for i, embedding in enumerate(embeddings):
                    if i < len(chunks):
                        chunks[i]["embedding"] = embedding
                        
                        # Add model info to chunk
                        chunks[i]["embedding_model"] = self.embedding_generator.config.model_name.value
                        chunks[i]["embedding_dimension"] = self.embedding_generator.embedding_dimension
                
                # Update document metadata
                document_metadata.update({
                    "embedding_model": self.embedding_generator.config.model_name.value,
                    "embedding_dimension": self.embedding_generator.embedding_dimension,
                    "embedding_time_ms": stats.embedding_time_ms
                })
            
            # Store in vector database if enabled
            if self.config.store_in_vector_db and self.config.generate_embeddings:
                start_time = time.time()
                document_metadata["status"] = ProcessingStatus.INDEXING
                await self._update_document(document_metadata)
                
                # Prepare points for vector store
                points = []
                for chunk in chunks:
                    if "embedding" in chunk:
                        # Create payload without the embedding
                        payload = {k: v for k, v in chunk.items() if k != "embedding"}
                        
                        # Add to points
                        points.append({
                            "id": chunk["chunk_id"],
                            "vector": chunk["embedding"],
                            "payload": payload
                        })
                
                # Insert points into vector store
                with trace.span("vector_indexing") if trace else nullcontext():
                    await self.vector_store.upsert_points(
                        collection_name=self.config.vector_collection,
                        points=points
                    )
                
                # Update stats
                stats.indexing_time_ms = int((time.time() - start_time) * 1000)
                
                # Update document metadata
                document_metadata.update({
                    "vector_count": len(points),
                    "indexing_time_ms": stats.indexing_time_ms
                })
            
            # Update final status
            stats.total_time_ms = (
                (stats.extraction_time_ms or 0) +
                (stats.cleaning_time_ms or 0) +
                (stats.chunking_time_ms or 0) +
                (stats.embedding_time_ms or 0) +
                (stats.indexing_time_ms or 0)
            )
            
            document_metadata.update({
                "status": ProcessingStatus.COMPLETED,
                "processing_completed": datetime.now().isoformat(),
                "processing_stats": asdict(stats),
                "total_processing_time_ms": stats.total_time_ms
            })
            
            # Store final document metadata
            await self._update_document(document_metadata)
            
            # Log success
            logger.info(f"Document processed successfully: {document_id}")
            
            # Complete trace
            if trace:
                trace.end(
                    output={
                        "document_id": document_id,
                        "status": "completed",
                        "stats": asdict(stats)
                    }
                )
            
            return document_metadata
            
        except Exception as e:
            # Handle error
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            # Update error status
            document_metadata.update({
                "status": ProcessingStatus.FAILED,
                "error": error_message,
                "error_traceback": error_traceback,
                "processing_completed": datetime.now().isoformat()
            })
            
            # Store error in MongoDB
            await self._update_document(document_metadata)
            
            # Log error
            logger.error(f"Document processing failed: {error_message}")
            logger.debug(error_traceback)
            
            # Complete trace with error
            if trace:
                trace.end(
                    output={
                        "document_id": document_id,
                        "status": "failed",
                        "error": error_message
                    },
                    error={
                        "message": error_message,
                        "traceback": error_traceback
                    }
                )
            
            return document_metadata
    
    async def _update_document(self, document_metadata: Dict[str, Any]):
        """Update document metadata in MongoDB
        
        Args:
            document_metadata: Document metadata to update
        """
        document_id = document_metadata["document_id"]
        await self.mongodb_client.update_document(
            self.config.documents_collection,
            {"document_id": document_id},
            document_metadata
        )
    
    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get document processing status
        
        Args:
            document_id: Document ID
            
        Returns:
            Document metadata with status
        """
        document = await self.mongodb_client.find_document(
            self.config.documents_collection,
            {"document_id": document_id}
        )
        
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        return document
    
    async def search_similar_chunks(
        self, 
        query_text: str,
        limit: int = 5,
        filter_condition: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for chunks similar to query text
        
        Args:
            query_text: Query text
            limit: Maximum number of results
            filter_condition: Optional filter for search
            
        Returns:
            List of similar document chunks
        """
        # Generate embedding for query
        query_embedding = self.embedding_generator.generate_single(query_text)
        
        # Search vector store
        search_result = await self.vector_store.search(
            collection_name=self.config.vector_collection,
            query_vector=query_embedding,
            limit=limit,
            filter=filter_condition
        )
        
        return search_result
    
    async def process_document_batch(
        self,
        documents: List[Tuple[Union[bytes, BinaryIO], str, Optional[Dict[str, Any]]]],
        trace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Process a batch of documents
        
        Args:
            documents: List of (file_content, filename, metadata) tuples
            trace_id: Trace ID for observability
            
        Returns:
            List of document metadata with processing results
        """
        # Create trace if enabled
        trace = None
        if self.tracer:
            trace = self.tracer.start_trace(
                name="document_batch_processing",
                id=trace_id or str(uuid.uuid4()),
                metadata={
                    "batch_size": len(documents)
                }
            )
        
        # Process documents in parallel
        tasks = []
        for file_content, filename, metadata in documents:
            task = asyncio.create_task(
                self.process_document(
                    file_content=file_content,
                    filename=filename,
                    metadata=metadata,
                    trace_id=trace_id
                )
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                # Handle exception
                processed_results.append({
                    "status": ProcessingStatus.FAILED,
                    "error": str(result),
                    "error_traceback": traceback.format_exc()
                })
            else:
                processed_results.append(result)
        
        # Complete trace
        if trace:
            trace.end(
                output={
                    "batch_size": len(documents),
                    "successful": sum(1 for r in processed_results if r["status"] == ProcessingStatus.COMPLETED),
                    "failed": sum(1 for r in processed_results if r["status"] == ProcessingStatus.FAILED)
                }
            )
        
        return processed_results


# Context manager for use when trace might be None
class nullcontext:
    def __init__(self, enter_result=None):
        self.enter_result = enter_result

    def __enter__(self):
        return self.enter_result

    def __exit__(self, *excinfo):
        pass
