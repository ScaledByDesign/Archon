"""
Vector search routes for the RAG System API
Handles document search, embedding, and retrieval operations
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field

from src.api.dependencies import get_vector_store, get_authenticated_user
from src.vector_store.vector_store import QdrantVectorStore

router = APIRouter(prefix="/search", tags=["vector_search"])


class SearchRequest(BaseModel):
    """Vector search request model"""
    query: str = Field(..., description="Search query text", min_length=1, max_length=1000)
    collection: str = Field(default="documents", description="Collection to search in")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum similarity score")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    include_vectors: bool = Field(default=False, description="Include vectors in response")


class EmbeddingRequest(BaseModel):
    """Text embedding request model"""
    text: str = Field(..., description="Text to embed", min_length=1, max_length=10000)
    model: str = Field(default="text-embedding-ada-002", description="Embedding model to use")


class DocumentUpload(BaseModel):
    """Document upload model"""
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    collection: str = Field(default="documents", description="Target collection")
    document_id: Optional[str] = Field(default=None, description="Optional document ID")


class SearchResult(BaseModel):
    """Individual search result"""
    id: str = Field(..., description="Document ID")
    score: float = Field(..., description="Similarity score")
    payload: Dict[str, Any] = Field(..., description="Document metadata")
    content: Optional[str] = Field(default=None, description="Document content")
    vector: Optional[List[float]] = Field(default=None, description="Document vector")


class SearchResponse(BaseModel):
    """Vector search response model"""
    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total results count")
    execution_time: float = Field(..., description="Query execution time in seconds")
    collection: str = Field(..., description="Searched collection")
    timestamp: str = Field(..., description="Search timestamp")


class EmbeddingResponse(BaseModel):
    """Text embedding response"""
    embedding: List[float] = Field(..., description="Text embedding vector")
    model: str = Field(..., description="Model used for embedding")
    text_length: int = Field(..., description="Length of input text")
    dimensions: int = Field(..., description="Embedding dimensions")


class UploadResponse(BaseModel):
    """Document upload response"""
    document_id: str = Field(..., description="Uploaded document ID")
    collection: str = Field(..., description="Target collection")
    status: str = Field(..., description="Upload status")
    vector_count: int = Field(..., description="Number of vectors created")


def create_mock_embedding(text: str, dimensions: int = 1536) -> List[float]:
    """Create a mock embedding vector for development purposes"""
    import hashlib
    import struct
    
    # Create deterministic hash-based embedding
    hash_bytes = hashlib.sha256(text.encode()).digest()
    embedding = []
    
    for i in range(0, min(len(hash_bytes), dimensions * 4), 4):
        if i + 4 <= len(hash_bytes):
            value = struct.unpack('f', hash_bytes[i:i+4])[0]
        else:
            value = 0.0
        embedding.append(value)
    
    # Pad with zeros if needed
    while len(embedding) < dimensions:
        embedding.append(0.0)
    
    # Normalize vector
    magnitude = sum(x*x for x in embedding) ** 0.5
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]
    
    return embedding[:dimensions]


@router.post("/embed", response_model=EmbeddingResponse)
async def create_embedding(
    request: EmbeddingRequest,
    user: dict = Depends(get_authenticated_user)
):
    """Create text embedding using specified model"""
    try:
        # For development, use mock embedding
        # In production, this would call actual embedding service (OpenAI, etc.)
        embedding = create_mock_embedding(request.text)
        
        return EmbeddingResponse(
            embedding=embedding,
            model=request.model,
            text_length=len(request.text),
            dimensions=len(embedding)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )


@router.post("/", response_model=SearchResponse)
async def vector_search(
    request: SearchRequest,
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    user: dict = Depends(get_authenticated_user)
):
    """Perform vector similarity search"""
    start_time = time.time()
    
    try:
        # Create query embedding
        query_vector = create_mock_embedding(request.query)
        
        # Perform search
        results = await vector_store.search_similar_vectors(
            collection_name=request.collection,
            query_vector=query_vector,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filter_conditions=request.filter
        )
        
        # Format results
        search_results = []
        for result in results:
            search_result = SearchResult(
                id=str(result.id),
                score=result.score,
                payload=result.payload or {},
                content=result.payload.get('content') if result.payload else None
            )
            
            if request.include_vectors and hasattr(result, 'vector'):
                search_result.vector = result.vector
                
            search_results.append(search_result)
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
            execution_time=execution_time,
            collection=request.collection,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: DocumentUpload,
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    user: dict = Depends(get_authenticated_user)
):
    """Upload and index a document"""
    try:
        # Generate embedding for document content
        content_vector = create_mock_embedding(request.content)
        
        # Prepare document payload
        payload = {
            'content': request.content,
            'uploaded_by': user.get('username', 'unknown'),
            'upload_timestamp': datetime.utcnow().isoformat() + "Z",
            **request.metadata
        }
        
        # Generate document ID if not provided
        document_id = request.document_id or f"doc_{int(time.time() * 1000)}"
        
        # Upsert document vector
        await vector_store.upsert_vectors(
            collection_name=request.collection,
            vectors=[{
                'id': document_id,
                'vector': content_vector,
                'payload': payload
            }]
        )
        
        return UploadResponse(
            document_id=document_id,
            collection=request.collection,
            status="uploaded",
            vector_count=1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.get("/collections", response_model=List[str])
async def list_collections(
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    user: dict = Depends(get_authenticated_user)
):
    """List available vector collections"""
    try:
        collections = await vector_store.list_collections()
        return [collection.name for collection in collections]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/collections/{collection_name}/stats")
async def get_collection_stats(
    collection_name: str,
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    user: dict = Depends(get_authenticated_user)
):
    """Get statistics for a specific collection"""
    try:
        stats = await vector_store.get_collection_info(collection_name)
        
        return {
            "name": collection_name,
            "vectors_count": getattr(stats, 'vectors_count', 0),
            "points_count": getattr(stats, 'points_count', 0),
            "status": str(getattr(stats, 'status', 'unknown')),
            "config": {
                "distance": getattr(stats.config, 'params', {}).get('distance', 'unknown') if hasattr(stats, 'config') else 'unknown'
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_name}' not found: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    collection: str = Query(default="documents", description="Collection name"),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    user: dict = Depends(get_authenticated_user)
):
    """Delete a document from the vector store"""
    try:
        await vector_store.delete_vectors(
            collection_name=collection,
            vector_ids=[document_id]
        )
        
        return {
            "status": "deleted",
            "document_id": document_id,
            "collection": collection,
            "deleted_by": user.get('username', 'unknown'),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/health")
async def search_health(
    vector_store: QdrantVectorStore = Depends(get_vector_store)
):
    """Search service health check"""
    try:
        health_status = await vector_store.health_check()
        
        return {
            "status": "healthy" if health_status else "unhealthy",
            "service": "vector_search",
            "vector_store": "healthy" if health_status else "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "vector_search",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
