"""
Qdrant Vector Database Client
Provides integration with Qdrant for vector storage and similarity search.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
)

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Result from vector similarity search"""
    id: Union[str, int]
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None


@dataclass
class QdrantConfig:
    """Qdrant client configuration"""
    host: str = "localhost"
    port: int = 6333
    api_key: Optional[str] = None
    https: bool = False
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> "QdrantConfig":
        """Create config from environment variables"""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        
        # Parse URL
        if qdrant_url.startswith("https://"):
            https = True
            host_port = qdrant_url[8:]
        elif qdrant_url.startswith("http://"):
            https = False
            host_port = qdrant_url[7:]
        else:
            https = False
            host_port = qdrant_url
            
        if ":" in host_port:
            host, port_str = host_port.split(":", 1)
            port = int(port_str)
        else:
            host = host_port
            port = 6333
            
        return cls(
            host=host,
            port=port,
            api_key=os.getenv("QDRANT_API_KEY"),
            https=https,
            timeout=int(os.getenv("QDRANT_TIMEOUT", "30"))
        )


class QdrantVectorStore:
    """Qdrant vector database client for RAG system"""
    
    def __init__(self, config: Optional[QdrantConfig] = None):
        """Initialize Qdrant client
        
        Args:
            config: Qdrant configuration, uses environment defaults if None
        """
        self.config = config or QdrantConfig.from_env()
        self.client = self._create_client()
        
    def _create_client(self) -> QdrantClient:
        """Create Qdrant client instance"""
        try:
            if self.config.api_key:
                client = QdrantClient(
                    url=f"{'https' if self.config.https else 'http'}://{self.config.host}:{self.config.port}",
                    api_key=self.config.api_key,
                    timeout=self.config.timeout
                )
            else:
                client = QdrantClient(
                    host=self.config.host,
                    port=self.config.port,
                    https=self.config.https,
                    timeout=self.config.timeout
                )
            
            # Test connection
            client.get_collections()
            logger.info(f"Connected to Qdrant at {self.config.host}:{self.config.port}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists
        
        Args:
            collection_name: Name of the collection to check
            
        Returns:
            True if collection exists
        """
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Failed to check if collection {collection_name} exists: {e}")
            return False

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
        on_disk_payload: bool = True,
        recreate: bool = False
    ) -> bool:
        """Create a new vector collection
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (COSINE, EUCLID, DOT)
            on_disk_payload: Store payload on disk to save RAM
            recreate: Delete existing collection if it exists
            
        Returns:
            True if collection was created successfully
        """
        try:
            # Check if collection exists
            collection_exists = await self.collection_exists(collection_name)
            
            if collection_exists:
                if recreate:
                    logger.info(f"Deleting existing collection: {collection_name}")
                    self.client.delete_collection(collection_name)
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    return True
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                    on_disk=True  # Store vectors on disk for large datasets
                ),
                on_disk_payload=on_disk_payload
            )
            
            logger.info(f"Created collection: {collection_name} (size: {vector_size}, distance: {distance})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if collection was deleted successfully
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection information dict or None if error
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "status": info.status,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance,
                }
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return None
    
    def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[Union[str, int]]] = None
    ) -> bool:
        """Insert or update vectors in a collection
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector embeddings
            payloads: List of metadata for each vector
            ids: Optional list of IDs, auto-generated if None
            
        Returns:
            True if upsert was successful
        """
        try:
            if len(vectors) != len(payloads):
                raise ValueError("Number of vectors must match number of payloads")
            
            if ids and len(ids) != len(vectors):
                raise ValueError("Number of IDs must match number of vectors")
            
            # Generate IDs if not provided
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in vectors]
            
            # Create points
            points = [
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
                for point_id, vector, payload in zip(ids, vectors, payloads)
            ]
            
            # Upsert points
            result = self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Upserted {len(points)} vectors to {collection_name}")
            return result.status == models.UpdateStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors to {collection_name}: {e}")
            return False
    
    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        with_vectors: bool = False
    ) -> List[VectorSearchResult]:
        """Search for similar vectors
        
        Args:
            collection_name: Name of the collection to search
            query_vector: Vector to find similar vectors for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Optional payload filter conditions
            with_vectors: Include vectors in results
            
        Returns:
            List of search results
        """
        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)
            
            # Perform search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_vectors=with_vectors
            )
            
            # Convert results
            search_results = []
            for result in results:
                search_results.append(VectorSearchResult(
                    id=result.id,
                    score=result.score,
                    payload=result.payload or {},
                    vector=result.vector if with_vectors else None
                ))
            
            logger.info(f"Found {len(search_results)} similar vectors in {collection_name}")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            return []
    
    def delete_vectors(
        self,
        collection_name: str,
        ids: List[Union[str, int]]
    ) -> bool:
        """Delete vectors by IDs
        
        Args:
            collection_name: Name of the collection
            ids: List of vector IDs to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            result = self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=ids
                )
            )
            
            logger.info(f"Deleted {len(ids)} vectors from {collection_name}")
            return result.status == models.UpdateStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Failed to delete vectors from {collection_name}: {e}")
            return False
    
    def count_vectors(self, collection_name: str) -> int:
        """Count vectors in a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of vectors in the collection
        """
        try:
            info = self.client.get_collection(collection_name)
            return info.points_count or 0
        except Exception as e:
            logger.error(f"Failed to count vectors in {collection_name}: {e}")
            return 0
    
    def close(self):
        """Close the client connection"""
        if hasattr(self.client, 'close'):
            self.client.close()
            logger.info("Closed Qdrant client connection")


# Collection name constants for the RAG system
class Collections:
    """Standard collection names for the RAG system"""
    DOCUMENTS = "documents"           # Document embeddings
    QUERIES = "queries"              # Query embeddings  
    CHUNKS = "chunks"                # Document chunk embeddings
    EPISODIC = "episodic"            # Episodic memory embeddings
    PROCEDURAL = "procedural"        # Procedural memory embeddings
    TOOLS = "tools"                  # Tool/function embeddings


# Convenience function for quick setup
def create_rag_collections(
    client: QdrantVectorStore,
    vector_size: int = 1536,  # OpenAI ada-002 embedding size
    recreate: bool = False
) -> Dict[str, bool]:
    """Create all standard RAG collections
    
    Args:
        client: Qdrant client instance
        vector_size: Embedding vector dimension
        recreate: Whether to recreate existing collections
        
    Returns:
        Dict mapping collection names to creation success status
    """
    collections_to_create = [
        Collections.DOCUMENTS,
        Collections.QUERIES,
        Collections.CHUNKS,
        Collections.EPISODIC,
        Collections.PROCEDURAL,
        Collections.TOOLS
    ]
    
    results = {}
    for collection_name in collections_to_create:
        results[collection_name] = client.create_collection(
            collection_name=collection_name,
            vector_size=vector_size,
            distance=Distance.COSINE,
            recreate=recreate
        )
    
    return results
