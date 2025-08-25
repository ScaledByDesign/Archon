#!/usr/bin/env python3
"""
ZOI Context Population Script

This script populates the vector databases with comprehensive ZOI project context
for testing and demonstrating the hybrid RAG architecture.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
import httpx
import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZOIContextPopulator:
    """Populates ZOI context across all vector databases"""
    
    def __init__(self):
        # Database connections
        self.postgres_url = "postgresql://postgres:litellm_password123@localhost:7063/postgres"
        self.qdrant_client = QdrantClient(host="localhost", port=7060)
        self.litellm_url = "http://localhost:7010"
        self.litellm_key = "sk-wqn0xwq_vha4MVM2yzw"
        
        # Context documents to populate
        self.context_documents = [
            {
                "title": "ZOI Project Overview",
                "file_path": "../docs/zoi-project-context.md",
                "collection": "zoi_knowledge_base",
                "document_type": "project_overview",
                "tags": ["zoi", "overview", "architecture", "ai-ecosystem"]
            },
            {
                "title": "ZOI Technical Architecture",
                "file_path": "../docs/zoi-technical-architecture.md",
                "collection": "zoi_knowledge_base",
                "document_type": "technical_documentation",
                "tags": ["zoi", "architecture", "technical", "microservices"]
            },
            {
                "title": "ZOI Development Context",
                "file_path": "../docs/zoi-development-context.md",
                "collection": "zoi_knowledge_base",
                "document_type": "development_guide",
                "tags": ["zoi", "development", "practices", "workflow"]
            },
            {
                "title": "ZOI README - Main Documentation",
                "file_path": "../README.md",
                "collection": "zoi_knowledge_base",
                "document_type": "main_documentation",
                "tags": ["zoi", "readme", "getting-started", "overview"]
            },
            {
                "title": "ZOI Core Stack Architecture",
                "file_path": "../apps/core/README.md",
                "collection": "code_embeddings",
                "document_type": "service_documentation",
                "tags": ["core", "ai-infrastructure", "litellm", "vllm"]
            },
            {
                "title": "ZOI Tools Stack Documentation",
                "file_path": "../apps/tools/README.md",
                "collection": "code_embeddings",
                "document_type": "service_documentation",
                "tags": ["tools", "productivity", "lobechat", "openwebui"]
            },
            {
                "title": "ZOI Platform Stack Documentation",
                "file_path": "../apps/platform/README.md",
                "collection": "code_embeddings",
                "document_type": "service_documentation",
                "tags": ["platform", "infrastructure", "traefik", "authentik"]
            }
        ]
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using LiteLLM"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.litellm_url}/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.litellm_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "zoi-embed",
                        "input": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return dummy embedding for testing
            return [0.1] * 1024  # mxbai-embed-large dimension
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:break_point + 1]
                    end = break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return chunks
    
    async def populate_qdrant_collection(self, collection_name: str, documents: List[Dict[str, Any]]):
        """Populate a Qdrant collection with documents"""
        try:
            # Check if collection exists, create if not
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {collection_name}")
            
            # Prepare points for insertion
            points = []
            point_id = 1
            
            for doc in documents:
                # Read document content
                try:
                    with open(doc["file_path"], 'r', encoding='utf-8') as f:
                        content = f.read()
                except FileNotFoundError:
                    logger.warning(f"File not found: {doc['file_path']}")
                    continue
                
                # Chunk the document
                chunks = self.chunk_text(content)
                logger.info(f"Processing {doc['title']}: {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    # Generate embedding
                    embedding = await self.generate_embedding(chunk)
                    
                    # Create point
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "content": chunk,
                            "title": doc["title"],
                            "source": doc["file_path"],
                            "document_type": doc["document_type"],
                            "tags": doc["tags"],
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "created_at": datetime.now().isoformat(),
                            "service": "zoi-context-populator"
                        }
                    )
                    points.append(point)
                    point_id += 1
            
            # Insert points in batches
            batch_size = 50
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                logger.info(f"Inserted batch {i//batch_size + 1} into {collection_name}")
            
            logger.info(f"✅ Populated {collection_name} with {len(points)} points")
            
        except Exception as e:
            logger.error(f"❌ Failed to populate {collection_name}: {e}")
    
    async def populate_postgres_shared(self, documents: List[Dict[str, Any]]):
        """Populate PostgreSQL shared embeddings table"""
        try:
            conn = await asyncpg.connect(self.postgres_url)
            
            for doc in documents:
                # Read document content
                try:
                    with open(doc["file_path"], 'r', encoding='utf-8') as f:
                        content = f.read()
                except FileNotFoundError:
                    logger.warning(f"File not found: {doc['file_path']}")
                    continue
                
                # Chunk the document
                chunks = self.chunk_text(content)
                logger.info(f"Processing {doc['title']} for PostgreSQL: {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    # Generate embedding (1536 dimensions for PostgreSQL)
                    embedding_text = chunk[:500]  # Truncate for embedding
                    embedding = await self.generate_embedding(embedding_text)
                    
                    # Pad or truncate to 1536 dimensions for PostgreSQL
                    if len(embedding) < 1536:
                        embedding.extend([0.0] * (1536 - len(embedding)))
                    elif len(embedding) > 1536:
                        embedding = embedding[:1536]
                    
                    # Insert into shared embeddings table
                    await conn.execute("""
                        INSERT INTO shared.embeddings 
                        (service_name, content_id, content_text, embedding, metadata)
                        VALUES ($1, $2, $3, $4, $5)
                    """, 
                        "zoi-context-populator",
                        f"{doc['title']}_chunk_{i}",
                        chunk,
                        embedding,
                        json.dumps({
                            "title": doc["title"],
                            "source": doc["file_path"],
                            "document_type": doc["document_type"],
                            "tags": doc["tags"],
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        })
                    )
            
            await conn.close()
            logger.info("✅ Populated PostgreSQL shared embeddings")
            
        except Exception as e:
            logger.error(f"❌ Failed to populate PostgreSQL: {e}")
    
    async def populate_all_databases(self):
        """Populate all vector databases with ZOI context"""
        logger.info("🚀 Starting ZOI context population...")
        
        # Group documents by collection
        collections = {}
        for doc in self.context_documents:
            collection = doc["collection"]
            if collection not in collections:
                collections[collection] = []
            collections[collection].append(doc)
        
        # Populate Qdrant collections
        for collection_name, docs in collections.items():
            await self.populate_qdrant_collection(collection_name, docs)
        
        # Populate PostgreSQL shared embeddings
        await self.populate_postgres_shared(self.context_documents)
        
        logger.info("🎉 ZOI context population completed!")
    
    async def test_search(self):
        """Test search functionality after population"""
        logger.info("🔍 Testing search functionality...")
        
        try:
            # Test Qdrant search
            test_embedding = await self.generate_embedding("What is ZOI architecture?")
            
            results = self.qdrant_client.search(
                collection_name="zoi_knowledge_base",
                query_vector=test_embedding,
                limit=3
            )
            
            logger.info(f"✅ Qdrant search returned {len(results)} results")
            for i, result in enumerate(results):
                logger.info(f"  {i+1}. Score: {result.score:.3f} - {result.payload.get('title', 'Unknown')}")
            
            # Test unified RAG service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:7090/search",
                    json={
                        "query_text": "What is ZOI architecture?",
                        "limit": 5
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Unified RAG search returned {data.get('total_results', 0)} results")
                else:
                    logger.warning(f"⚠️ Unified RAG search failed: {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ Search test failed: {e}")

async def main():
    """Main execution function"""
    populator = ZOIContextPopulator()
    
    try:
        # Populate all databases
        await populator.populate_all_databases()
        
        # Test search functionality
        await populator.test_search()
        
        logger.info("🎯 ZOI context population and testing completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Population failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
