"""
MongoDB Client for Document Storage
Provides integration with MongoDB for storing document metadata and processing status
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic
from datetime import datetime
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T', bound=BaseModel)


class ProcessingStatus(str, Enum):
    """Document processing status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INDEXED = "indexed"


class DocumentMetadata(BaseModel):
    """Base document metadata model"""
    model_config = ConfigDict(populate_by_name=True)
    
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    title: Optional[str] = Field(None, description="Document title")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Document creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Document last update timestamp")
    size_bytes: int = Field(..., description="Document size in bytes")
    num_pages: Optional[int] = Field(None, description="Number of pages (for multi-page documents)")
    source: Optional[str] = Field(None, description="Document source/origin")
    author: Optional[str] = Field(None, description="Document author")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    embedding_model: Optional[str] = Field(None, description="Model used for embedding generation")
    language: Optional[str] = Field(None, description="Detected document language")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")
    
    # Additional fields for vector storage reference
    vector_ids: List[str] = Field(default_factory=list, description="IDs of vectors in Qdrant")
    chunk_count: int = Field(default=0, description="Number of chunks document was split into")


class DocumentChunk(BaseModel):
    """Document chunk model for split documents"""
    model_config = ConfigDict(populate_by_name=True)
    
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    content: str = Field(..., description="Chunk text content")
    page_number: Optional[int] = Field(None, description="Page number for multi-page documents")
    chunk_index: int = Field(..., description="Index of chunk within document")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Chunk creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")
    vector_id: Optional[str] = Field(None, description="ID of vector in Qdrant")


class MongoDBConfig(BaseModel):
    """MongoDB connection configuration"""
    model_config = ConfigDict(populate_by_name=True)
    
    uri: str = Field(..., description="MongoDB connection URI")
    database_name: str = Field(..., description="Database name")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    auth_source: Optional[str] = Field(None, description="Authentication source database")
    
    @classmethod
    def from_env(cls) -> "MongoDBConfig":
        """Create MongoDB config from environment variables"""
        # Get MongoDB URI from environment
        uri = os.getenv("MONGODB_URI", "mongodb://mongo-episodic:27017,mongo-procedural:27017")
        
        # Construct config
        return cls(
            uri=uri,
            database_name=os.getenv("MONGODB_DATABASE", "rag_system"),
            username=os.getenv("MONGODB_USERNAME"),
            password=os.getenv("MONGODB_PASSWORD"),
            auth_source=os.getenv("MONGODB_AUTH_SOURCE", "admin")
        )


class MongoDBClient:
    """MongoDB client for document storage"""
    
    # Collection names
    DOCUMENTS_COLLECTION = "documents"
    CHUNKS_COLLECTION = "document_chunks"
    PROCESSING_QUEUE_COLLECTION = "processing_queue"
    
    def __init__(self, config: Optional[MongoDBConfig] = None):
        """Initialize MongoDB client
        
        Args:
            config: MongoDB configuration, uses environment defaults if None
        """
        self.config = config or MongoDBConfig.from_env()
        self.client = None
        self.db = None
        
        # Initialize collections
        self.documents_collection = None
        self.chunks_collection = None
        self.processing_queue_collection = None
        
    async def connect(self) -> bool:
        """Connect to MongoDB
        
        Returns:
            True if connection successful
        """
        try:
            # Create connection URI with auth if provided
            if self.config.username and self.config.password:
                # Check if URI already contains auth
                if '@' not in self.config.uri:
                    # Split URI into protocol and address
                    protocol, address = self.config.uri.split('://', 1)
                    auth_uri = f"{protocol}://{self.config.username}:{self.config.password}@{address}"
                    self.client = AsyncIOMotorClient(auth_uri)
                else:
                    self.client = AsyncIOMotorClient(self.config.uri)
            else:
                self.client = AsyncIOMotorClient(self.config.uri)
            
            # Get database
            self.db = self.client[self.config.database_name]
            
            # Initialize collections
            self.documents_collection = self.db[self.DOCUMENTS_COLLECTION]
            self.chunks_collection = self.db[self.CHUNKS_COLLECTION]
            self.processing_queue_collection = self.db[self.PROCESSING_QUEUE_COLLECTION]
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"Connected to MongoDB at {self.config.uri}, database: {self.config.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def _create_indexes(self):
        """Create indexes for collections"""
        # Document collection indexes
        await self.documents_collection.create_index("document_id", unique=True)
        await self.documents_collection.create_index("status")
        await self.documents_collection.create_index("created_at")
        await self.documents_collection.create_index("tags")
        
        # Chunks collection indexes
        await self.chunks_collection.create_index("chunk_id", unique=True)
        await self.chunks_collection.create_index("document_id")
        await self.chunks_collection.create_index("vector_id")
        await self.chunks_collection.create_index([("content", "text")])
        
        # Processing queue indexes
        await self.processing_queue_collection.create_index("document_id", unique=True)
        await self.processing_queue_collection.create_index("status")
        await self.processing_queue_collection.create_index("created_at")
    
    async def health_check(self) -> bool:
        """Check MongoDB connection health
        
        Returns:
            True if MongoDB is accessible
        """
        try:
            # Simple command to check connection
            await self.db.command("ping")
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    async def create_document(self, document: DocumentMetadata) -> str:
        """Create a new document metadata entry
        
        Args:
            document: Document metadata model
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Convert to dict and insert
            doc_dict = document.model_dump(by_alias=True)
            
            # Handle datetime conversion for MongoDB
            doc_dict["created_at"] = document.created_at
            doc_dict["updated_at"] = document.updated_at
            
            result = await self.documents_collection.insert_one(doc_dict)
            logger.info(f"Created document metadata: {document.document_id}")
            return document.document_id
            
        except Exception as e:
            logger.error(f"Failed to create document metadata: {e}")
            return None
    
    async def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document metadata if found, None otherwise
        """
        try:
            doc = await self.documents_collection.find_one({"document_id": document_id})
            if doc:
                return DocumentMetadata.model_validate(doc)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document metadata: {e}")
            return None
    
    async def update_document(self, document_id: str, update_data: Dict[str, Any]) -> bool:
        """Update document metadata
        
        Args:
            document_id: Document ID
            update_data: Fields to update
            
        Returns:
            True if update successful
        """
        try:
            # Always update the updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.documents_collection.update_one(
                {"document_id": document_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Document not found for update: {document_id}")
                return False
                
            logger.info(f"Updated document metadata: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document metadata and all chunks
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deletion successful
        """
        try:
            # Delete document metadata
            doc_result = await self.documents_collection.delete_one({"document_id": document_id})
            
            # Delete all chunks for this document
            chunks_result = await self.chunks_collection.delete_many({"document_id": document_id})
            
            # Also remove from processing queue if present
            queue_result = await self.processing_queue_collection.delete_one({"document_id": document_id})
            
            logger.info(f"Deleted document {document_id} with {chunks_result.deleted_count} chunks")
            return doc_result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def create_chunk(self, chunk: DocumentChunk) -> str:
        """Create a document chunk
        
        Args:
            chunk: Document chunk model
            
        Returns:
            Chunk ID if successful, None otherwise
        """
        try:
            # Convert to dict and insert
            chunk_dict = chunk.model_dump(by_alias=True)
            
            # Handle datetime conversion for MongoDB
            chunk_dict["created_at"] = chunk.created_at
            
            result = await self.chunks_collection.insert_one(chunk_dict)
            logger.debug(f"Created document chunk: {chunk.chunk_id} for document {chunk.document_id}")
            return chunk.chunk_id
            
        except Exception as e:
            logger.error(f"Failed to create document chunk: {e}")
            return None
    
    async def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            List of document chunks
        """
        try:
            chunks = await self.chunks_collection.find({"document_id": document_id}).to_list(length=None)
            return [DocumentChunk.model_validate(chunk) for chunk in chunks]
            
        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []
    
    async def update_chunk(self, chunk_id: str, update_data: Dict[str, Any]) -> bool:
        """Update document chunk
        
        Args:
            chunk_id: Chunk ID
            update_data: Fields to update
            
        Returns:
            True if update successful
        """
        try:
            result = await self.chunks_collection.update_one(
                {"chunk_id": chunk_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Chunk not found for update: {chunk_id}")
                return False
                
            logger.debug(f"Updated document chunk: {chunk_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document chunk: {e}")
            return False
    
    async def add_to_processing_queue(self, document_id: str, priority: int = 1) -> bool:
        """Add document to processing queue
        
        Args:
            document_id: Document ID
            priority: Processing priority (higher = more important)
            
        Returns:
            True if added successfully
        """
        try:
            # Check if already in queue
            existing = await self.processing_queue_collection.find_one({"document_id": document_id})
            if existing:
                # Update priority if document already in queue
                await self.processing_queue_collection.update_one(
                    {"document_id": document_id},
                    {"$set": {
                        "priority": priority,
                        "updated_at": datetime.utcnow()
                    }}
                )
                logger.info(f"Updated document in processing queue: {document_id}")
                return True
            
            # Add to queue
            await self.processing_queue_collection.insert_one({
                "document_id": document_id,
                "status": ProcessingStatus.PENDING.value,
                "priority": priority,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "attempts": 0,
                "last_error": None
            })
            
            logger.info(f"Added document to processing queue: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to processing queue: {e}")
            return False
    
    async def get_next_from_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get next documents from processing queue
        
        Args:
            limit: Maximum number of documents to retrieve
            
        Returns:
            List of document IDs with queue information
        """
        try:
            # Get documents with PENDING status, ordered by priority and creation time
            cursor = self.processing_queue_collection.find(
                {"status": ProcessingStatus.PENDING.value}
            ).sort([
                ("priority", -1),  # Higher priority first
                ("created_at", 1)   # Older documents first
            ]).limit(limit)
            
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Failed to get next documents from processing queue: {e}")
            return []
    
    async def update_queue_status(
        self, 
        document_id: str, 
        status: ProcessingStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update document status in processing queue
        
        Args:
            document_id: Document ID
            status: New status
            error_message: Error message if failed
            
        Returns:
            True if update successful
        """
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
            
            if status == ProcessingStatus.FAILED:
                # Increment attempts count and set error message
                update_data["$inc"] = {"attempts": 1}
                update_data["last_error"] = error_message
            
            result = await self.processing_queue_collection.update_one(
                {"document_id": document_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Document not found in queue: {document_id}")
                return False
                
            logger.info(f"Updated document status in queue to {status.value}: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document status in queue: {e}")
            return False
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        status: Optional[ProcessingStatus] = None,
        tag: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[DocumentMetadata]:
        """Search for documents based on criteria
        
        Args:
            query: Text search query
            limit: Maximum number of results
            status: Filter by processing status
            tag: Filter by tag
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of matching documents
        """
        try:
            filter_criteria = {}
            
            # Add filters if provided
            if query:
                filter_criteria["$text"] = {"$search": query}
            
            if status:
                filter_criteria["status"] = status.value
                
            if tag:
                filter_criteria["tags"] = tag
                
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                
                if date_filter:
                    filter_criteria["created_at"] = date_filter
            
            # Execute search
            cursor = self.documents_collection.find(filter_criteria).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            return [DocumentMetadata.model_validate(doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    async def find_document(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document in a collection
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter criteria
            
        Returns:
            Document if found, None otherwise
        """
        try:
            collection = self.db[collection_name]
            return await collection.find_one(filter_dict)
        except Exception as e:
            logger.error(f"Failed to find document in {collection_name}: {e}")
            return None

    async def find_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                           limit: int = None, skip: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find multiple documents in a collection
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter criteria
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            sort: List of (field, direction) tuples for sorting
            
        Returns:
            List of documents
        """
        try:
            collection = self.db[collection_name]
            cursor = collection.find(filter_dict or {})
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
                
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            return []
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in a collection
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter criteria
            
        Returns:
            Number of documents matching the filter
        """
        try:
            collection = self.db[collection_name]
            return await collection.count_documents(filter_dict or {})
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            return 0
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")


# Global instance for dependency injection
mongodb_client = None


async def get_mongodb_client() -> MongoDBClient:
    """Get or create MongoDB client instance
    
    Returns:
        MongoDB client instance
    """
    global mongodb_client
    
    if mongodb_client is None:
        mongodb_client = MongoDBClient()
        await mongodb_client.connect()
        
    return mongodb_client
