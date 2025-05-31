"""
Document Processing API Routes
Provides endpoints for document upload, processing, and retrieval
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Union
import uuid
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.document_pipeline.document_processor import DocumentProcessor, ProcessingStatus
from src.document_pipeline.queue_consumer import DocumentQueueConsumer
from src.db.mongodb_client import MongoDBClient
from src.core.service_manager import get_document_processor, get_mongodb_client, get_queue_consumer

logger = logging.getLogger(__name__)

# Models
class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    processing_stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "example.pdf",
                "status": "completed",
                "processing_stats": {
                    "extraction_time_ms": 152,
                    "cleaning_time_ms": 45,
                    "chunking_time_ms": 78,
                    "embedding_time_ms": 523,
                    "indexing_time_ms": 89,
                    "total_time_ms": 887,
                    "char_count": 15278,
                    "chunk_count": 12
                },
                "created_at": "2023-05-29T08:59:37.123Z"
            }
        }

class DocumentSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)
    filter: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query": "How to implement vector search?",
                "limit": 5,
                "filter": {
                    "document_filename": {"$regex": ".*\\.pdf$"}
                }
            }
        }

class DocumentSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int
    query: str
    
    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "chunk_id": "123e4567-e89b-12d3-a456-426614174000_1",
                        "document_id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "Vector search is a technique...",
                        "score": 0.92,
                        "document_filename": "vector_search.pdf"
                    }
                ],
                "count": 1,
                "query": "How to implement vector search?"
            }
        }

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Vector Search Implementation Guide",
                "author": "John Doe",
                "description": "A comprehensive guide to vector search",
                "tags": ["vector", "search", "guide"],
                "source": "knowledge_base",
                "custom_fields": {
                    "department": "Engineering",
                    "confidentiality": "Public"
                }
            }
        }

# Router
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

# Dependencies
async def get_document_processor_dep():
    """Get document processor from service manager"""
    return await get_document_processor()

async def get_queue_consumer_dep():
    """Get queue consumer from service manager"""
    return await get_queue_consumer()

async def get_mongodb_client_dep():
    """Get MongoDB client from service manager"""
    return await get_mongodb_client()

# Routes
@router.post(
    "/upload",
    response_model=DocumentResponse,
    summary="Upload and process a document",
    description="Upload a document for processing. The document will be processed asynchronously."
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    process_async: bool = Form(True),
    processor: DocumentProcessor = Depends(get_document_processor_dep),
    queue_consumer: DocumentQueueConsumer = Depends(get_queue_consumer_dep)
):
    try:
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Parse metadata if provided
        document_metadata = {}
        if metadata:
            try:
                document_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata format. Must be valid JSON.")
        
        # Add upload metadata
        document_metadata.update({
            "filename": file.filename,
            "content_type": file.content_type,
            "uploaded_at": datetime.now().isoformat(),
            "size_bytes": 0  # Will be updated after reading the file
        })
        
        # Read file content
        file_content = await file.read()
        document_metadata["size_bytes"] = len(file_content)
        
        # Create initial response
        response = {
            "document_id": document_id,
            "filename": file.filename,
            "status": ProcessingStatus.PENDING,
            "created_at": document_metadata["uploaded_at"]
        }
        
        if process_async:
            # Enqueue for async processing
            await queue_consumer.enqueue_document(
                file_content=file_content,
                filename=file.filename,
                metadata=document_metadata,
                document_id=document_id
            )
        else:
            # Process synchronously in background task
            # This allows the API to return immediately but still process the document
            background_tasks.add_task(
                processor.process_document,
                file_content=file_content,
                filename=file.filename,
                metadata=document_metadata,
                document_id=document_id
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document status",
    description="Get the processing status and metadata for a document."
)
async def get_document(
    document_id: str,
    processor: DocumentProcessor = Depends(get_document_processor_dep)
):
    try:
        document = await processor.get_document_status(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        # Convert to response format
        response = {
            "document_id": document["document_id"],
            "filename": document.get("filename", "unknown"),
            "status": document.get("status", "unknown"),
            "created_at": document.get("uploaded_at", document.get("processing_started"))
        }
        
        # Add processing stats if available
        if "processing_stats" in document:
            response["processing_stats"] = document["processing_stats"]
        
        # Add error if failed
        if document.get("status") == ProcessingStatus.FAILED and "error" in document:
            response["error"] = document["error"]
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")

@router.post(
    "/search",
    response_model=DocumentSearchResponse,
    summary="Search for similar documents",
    description="Search for document chunks similar to the provided query."
)
async def search_documents(
    request: DocumentSearchRequest,
    processor: DocumentProcessor = Depends(get_document_processor_dep)
):
    try:
        # Search for similar chunks
        results = await processor.search_similar_chunks(
            query_text=request.query,
            limit=request.limit,
            filter_condition=request.filter
        )
        
        # Format response
        response = {
            "results": results,
            "count": len(results),
            "query": request.query
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@router.get(
    "/",
    summary="List documents",
    description="List all documents with optional filtering and pagination."
)
async def list_documents(
    status: Optional[str] = Query(None, description="Filter by processing status"),
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of documents to return"),
    mongodb_client: MongoDBClient = Depends(get_mongodb_client_dep),
    processor: DocumentProcessor = Depends(get_document_processor_dep)
):
    try:
        # Build filter
        filter_condition = {}
        if status:
            filter_condition["status"] = status
        
        # Query MongoDB
        documents = await mongodb_client.find_documents(
            processor.config.documents_collection,
            filter_condition,
            skip=skip,
            limit=limit,
            sort=[("processing_started", -1)]  # Sort by processing time, newest first
        )
        
        # Count total
        total = await mongodb_client.count_documents(
            processor.config.documents_collection,
            filter_condition
        )
        
        # Format response
        response = {
            "documents": documents,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.delete(
    "/{document_id}",
    summary="Delete a document",
    description="Delete a document and all its chunks and vector embeddings."
)
async def delete_document(
    document_id: str,
    mongodb_client: MongoDBClient = Depends(get_mongodb_client_dep),
    processor: DocumentProcessor = Depends(get_document_processor_dep),
):
    try:
        # Check if document exists
        document = await processor.get_document_status(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        # Delete document from MongoDB
        await mongodb_client.delete_document(
            processor.config.documents_collection,
            {"document_id": document_id}
        )
        
        # Delete chunks from MongoDB
        await mongodb_client.delete_documents(
            processor.config.chunks_collection,
            {"document_id": document_id}
        )
        
        # Delete vectors from vector store
        # Get chunk IDs
        chunk_ids = [
            chunk["chunk_id"] 
            for chunk in await mongodb_client.find_documents(
                processor.config.chunks_collection,
                {"document_id": document_id}
            )
        ]
        
        # Delete points from vector store
        if chunk_ids:
            await processor.vector_store.delete_points(
                processor.config.vector_collection,
                points=chunk_ids
            )
        
        return {"status": "success", "message": f"Document {document_id} deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
