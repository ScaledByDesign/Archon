#!/usr/bin/env python3
"""
Unified RAG Service for 100% Cross-Collection Context

This service enables LobeChat and other services to access ALL knowledge
from every vector database collection and graph database.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import asyncpg
import httpx
from qdrant_client import QdrantClient
from neo4j import AsyncGraphDatabase
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Unified search result from any source"""
    content: str
    source: str
    collection: str
    score: float
    metadata: Dict[str, Any]
    timestamp: Optional[datetime] = None

@dataclass
class UnifiedRAGConfig:
    """Configuration for unified RAG service"""
    # Database connections
    postgres_url: str = "postgresql://postgres:litellm_password123@postgres:5432/postgres"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password123"
    
    # Search configuration
    max_results_per_collection: int = 10
    global_similarity_threshold: float = 0.6
    max_total_results: int = 50
    
    # Collection weights
    collection_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.collection_weights is None:
            self.collection_weights = {
                "zoi_knowledge_base": 1.0,
                "code_embeddings": 0.9,
                "archon_knowledge": 0.8,
                "openwebui_conversations": 0.7,
                "n8n_workflows": 0.6,
                "lobechat_agents": 0.8,
                "user_preferences": 0.5,
                "litellm_cache": 0.4
            }

class UnifiedRAGService:
    """Unified RAG service for cross-collection knowledge access"""
    
    def __init__(self, config: UnifiedRAGConfig):
        self.config = config
        self.qdrant_client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port
        )
        self.neo4j_driver = AsyncGraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_username, config.neo4j_password)
        )
        self.postgres_pool = None
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Initialize PostgreSQL connection pool
            self.postgres_pool = await asyncpg.create_pool(
                self.config.postgres_url,
                min_size=2,
                max_size=10
            )
            logger.info("✅ PostgreSQL connection pool initialized")
            
            # Test Qdrant connection
            collections = self.qdrant_client.get_collections()
            logger.info(f"✅ Qdrant connected - {len(collections.collections)} collections available")
            
            # Test Neo4j connection
            async with self.neo4j_driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.single()
            logger.info("✅ Neo4j connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise
    
    async def search_all_collections(
        self, 
        query_embedding: List[float], 
        query_text: str,
        limit: int = None
    ) -> List[SearchResult]:
        """Search across all vector collections and databases"""
        
        if limit is None:
            limit = self.config.max_total_results
            
        all_results = []
        
        # 1. Search Qdrant collections in parallel
        qdrant_tasks = []
        for collection_name, weight in self.config.collection_weights.items():
            task = self._search_qdrant_collection(
                collection_name, query_embedding, weight
            )
            qdrant_tasks.append(task)
        
        qdrant_results = await asyncio.gather(*qdrant_tasks, return_exceptions=True)
        
        for results in qdrant_results:
            if isinstance(results, Exception):
                logger.warning(f"Qdrant search error: {results}")
                continue
            all_results.extend(results)
        
        # 2. Search PostgreSQL shared embeddings
        try:
            postgres_results = await self._search_postgres_embeddings(
                query_embedding, query_text
            )
            all_results.extend(postgres_results)
        except Exception as e:
            logger.warning(f"PostgreSQL search error: {e}")
        
        # 3. Search Neo4j for related concepts
        try:
            graph_results = await self._search_neo4j_relationships(query_text)
            all_results.extend(graph_results)
        except Exception as e:
            logger.warning(f"Neo4j search error: {e}")
        
        # 4. Rerank and deduplicate results
        final_results = self._rerank_and_deduplicate(all_results, limit)
        
        logger.info(f"🔍 Unified search returned {len(final_results)} results from {len(all_results)} total")
        return final_results
    
    async def _search_qdrant_collection(
        self, 
        collection_name: str, 
        query_embedding: List[float],
        weight: float
    ) -> List[SearchResult]:
        """Search a specific Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                logger.debug(f"Collection {collection_name} not found")
                return []
            
            # Get collection info
            collection_info = self.qdrant_client.get_collection(collection_name)
            if collection_info.points_count == 0:
                logger.debug(f"Collection {collection_name} is empty")
                return []
            
            # Perform search
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=self.config.max_results_per_collection,
                score_threshold=self.config.global_similarity_threshold
            )
            
            results = []
            for result in search_results:
                # Apply collection weight to score
                weighted_score = result.score * weight
                
                search_result = SearchResult(
                    content=result.payload.get("content", ""),
                    source=result.payload.get("source", collection_name),
                    collection=collection_name,
                    score=weighted_score,
                    metadata=result.payload
                )
                results.append(search_result)
            
            logger.debug(f"Found {len(results)} results in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching {collection_name}: {e}")
            return []
    
    async def _search_postgres_embeddings(
        self, 
        query_embedding: List[float], 
        query_text: str
    ) -> List[SearchResult]:
        """Search PostgreSQL shared embeddings table"""
        if not self.postgres_pool:
            return []
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Convert embedding to PostgreSQL vector format
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
                
                query = """
                SELECT
                    content_text,
                    service_name,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity,
                    created_at
                FROM shared.embeddings
                WHERE 1 - (embedding <=> $1::vector) > $2
                ORDER BY similarity DESC
                LIMIT $3
                """

                rows = await conn.fetch(
                    query,
                    embedding_str,
                    self.config.global_similarity_threshold,
                    self.config.max_results_per_collection
                )
                
                results = []
                for row in rows:
                    search_result = SearchResult(
                        content=row["content_text"] or "",
                        source=row["service_name"] or "postgres",
                        collection="shared_embeddings",
                        score=float(row["similarity"]),
                        metadata=row["metadata"] or {},
                        timestamp=row["created_at"]
                    )
                    results.append(search_result)
                
                logger.debug(f"Found {len(results)} results in PostgreSQL")
                return results
                
        except Exception as e:
            logger.error(f"PostgreSQL search error: {e}")
            return []
    
    async def _search_neo4j_relationships(self, query_text: str) -> List[SearchResult]:
        """Search Neo4j for related concepts and relationships"""
        try:
            async with self.neo4j_driver.session() as session:
                # Search for nodes with similar content or relationships
                cypher_query = """
                MATCH (n)
                WHERE n.content CONTAINS $query_text 
                   OR n.title CONTAINS $query_text
                   OR n.description CONTAINS $query_text
                OPTIONAL MATCH (n)-[r]-(related)
                RETURN n, collect(related) as related_nodes
                LIMIT $limit
                """
                
                result = await session.run(
                    cypher_query,
                    query_text=query_text,
                    limit=self.config.max_results_per_collection
                )
                
                results = []
                async for record in result:
                    node = record["n"]
                    related_nodes = record["related_nodes"]
                    
                    # Create content from node and relationships
                    content_parts = []
                    if hasattr(node, "content") and node.content:
                        content_parts.append(node.content)
                    if hasattr(node, "title") and node.title:
                        content_parts.append(f"Title: {node.title}")
                    
                    # Add related context
                    if related_nodes:
                        related_content = [str(n) for n in related_nodes[:3]]  # Limit related
                        content_parts.append(f"Related: {', '.join(related_content)}")
                    
                    if content_parts:
                        search_result = SearchResult(
                            content=" | ".join(content_parts),
                            source="neo4j",
                            collection="graph_relationships",
                            score=0.7,  # Fixed score for graph results
                            metadata={
                                "node_labels": list(node.labels) if hasattr(node, "labels") else [],
                                "related_count": len(related_nodes)
                            }
                        )
                        results.append(search_result)
                
                logger.debug(f"Found {len(results)} results in Neo4j")
                return results
                
        except Exception as e:
            logger.error(f"Neo4j search error: {e}")
            return []
    
    def _rerank_and_deduplicate(
        self, 
        results: List[SearchResult], 
        limit: int
    ) -> List[SearchResult]:
        """Rerank results by score and remove duplicates"""
        
        # Sort by score (descending)
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        
        # Deduplicate by content similarity
        deduplicated = []
        seen_content = set()
        
        for result in sorted_results:
            # Simple deduplication by content hash
            content_hash = hash(result.content[:200])  # First 200 chars
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(result)
                
                if len(deduplicated) >= limit:
                    break
        
        return deduplicated
    
    async def close(self):
        """Close all database connections"""
        if self.postgres_pool:
            await self.postgres_pool.close()
        await self.neo4j_driver.close()

# FastAPI endpoint for unified search
async def unified_search_endpoint(
    query_embedding: List[float],
    query_text: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Unified search endpoint for external services"""
    
    config = UnifiedRAGConfig()
    service = UnifiedRAGService(config)
    
    try:
        await service.initialize()
        results = await service.search_all_collections(
            query_embedding, query_text, limit
        )
        
        return {
            "success": True,
            "results": [
                {
                    "content": r.content,
                    "source": r.source,
                    "collection": r.collection,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ],
            "total_results": len(results),
            "query": query_text
        }
        
    except Exception as e:
        logger.error(f"Unified search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }
    finally:
        await service.close()

# FastAPI Application
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Unified RAG Service",
    description="Cross-collection knowledge access for 100% context",
    version="1.0.0"
)

# Global service instance
_rag_service = None

class SearchRequest(BaseModel):
    query_text: str
    query_embedding: Optional[List[float]] = None
    limit: int = 20

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG service on startup"""
    global _rag_service
    config = UnifiedRAGConfig()
    _rag_service = UnifiedRAGService(config)
    await _rag_service.initialize()
    logger.info("🚀 Unified RAG Service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global _rag_service
    if _rag_service:
        await _rag_service.close()
    logger.info("🛑 Unified RAG Service stopped")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "unified-rag"}

@app.post("/search")
async def search_knowledge(request: SearchRequest):
    """Search across all knowledge collections"""
    global _rag_service

    if not _rag_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # If no embedding provided, generate one using LiteLLM
        if not request.query_embedding:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "http://litellm:4000/v1/embeddings",
                        headers={
                            "Authorization": "Bearer sk-wqn0xwq_vha4MVM2yzw",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "zoi-embed",
                            "input": request.query_text
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    request.query_embedding = data["data"][0]["embedding"]
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                # Fallback to dummy embedding with correct dimensions (1024 for mxbai-embed-large)
                request.query_embedding = [0.1] * 1024

        results = await _rag_service.search_all_collections(
            request.query_embedding,
            request.query_text,
            request.limit
        )

        return {
            "success": True,
            "results": [
                {
                    "content": r.content,
                    "source": r.source,
                    "collection": r.collection,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ],
            "total_results": len(results),
            "query": request.query_text
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections")
async def list_collections():
    """List all available collections"""
    global _rag_service

    if not _rag_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Get Qdrant collections
        collections = _rag_service.qdrant_client.get_collections()
        qdrant_collections = [
            {
                "name": c.name,
                "type": "qdrant",
                "points_count": _rag_service.qdrant_client.get_collection(c.name).points_count
            }
            for c in collections.collections
        ]

        # Add PostgreSQL and Neo4j
        other_collections = [
            {"name": "shared_embeddings", "type": "postgresql", "points_count": "unknown"},
            {"name": "graph_relationships", "type": "neo4j", "points_count": "unknown"}
        ]

        return {
            "collections": qdrant_collections + other_collections,
            "total_collections": len(qdrant_collections) + len(other_collections)
        }

    except Exception as e:
        logger.error(f"Collections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
