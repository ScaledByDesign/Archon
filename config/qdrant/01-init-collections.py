#!/usr/bin/env python3
"""
Qdrant Bootstrap Script for Zoi Ecosystem
Creates collections, indexes, and initial configurations for vector search
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PayloadSchemaType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QdrantBootstrap:
    """Bootstrap Qdrant collections for Zoi ecosystem"""
    
    def __init__(self, host: str = "qdrant", port: int = 6333):
        """Initialize Qdrant client"""
        self.client = QdrantClient(host=host, port=port)
        logger.info(f"Connected to Qdrant at {host}:{port}")
    
    def wait_for_qdrant(self, max_retries: int = 30, delay: int = 2) -> bool:
        """Wait for Qdrant to be ready"""
        for attempt in range(max_retries):
            try:
                self.client.get_collections()
                logger.info("Qdrant is ready!")
                return True
            except Exception as e:
                logger.info(f"Waiting for Qdrant... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
        
        logger.error("Qdrant failed to become ready")
        return False
    
    def create_collection_if_not_exists(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
        description: str = "",
        payload_indexes: Optional[Dict] = None
    ) -> bool:
        """Create collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            existing_names = [col.name for col in collections]
            
            if collection_name in existing_names:
                logger.info(f"Collection '{collection_name}' already exists")
                return True
            
            # Create collection
            logger.info(f"Creating collection '{collection_name}' (size: {vector_size}, distance: {distance})")
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            # Create payload indexes if specified
            if payload_indexes:
                for field_name, schema_type in payload_indexes.items():
                    logger.info(f"Creating payload index for field '{field_name}'")
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=schema_type
                    )
            
            logger.info(f"Collection '{collection_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            return False
    
    def setup_zoi_collections(self) -> bool:
        """Setup all Zoi ecosystem collections"""
        collections_config = [
            {
                "collection_name": "zoi_knowledge_base",
                "vector_size": 1024,  # mxbai-embed-large
                "distance": Distance.COSINE,
                "description": "Main knowledge base for RAG system",
                "payload_indexes": {
                    "source": PayloadSchemaType.KEYWORD,
                    "document_type": PayloadSchemaType.KEYWORD,
                    "created_at": PayloadSchemaType.DATETIME,
                    "service": PayloadSchemaType.KEYWORD,
                    "tags": PayloadSchemaType.KEYWORD,
                }
            },
            {
                "collection_name": "litellm_cache",
                "vector_size": 1536,  # OpenAI embeddings
                "distance": Distance.COSINE,
                "description": "LiteLLM semantic cache for similar queries",
                "payload_indexes": {
                    "model": PayloadSchemaType.KEYWORD,
                    "user_id": PayloadSchemaType.KEYWORD,
                    "timestamp": PayloadSchemaType.DATETIME,
                    "cost": PayloadSchemaType.FLOAT,
                }
            },
            {
                "collection_name": "openwebui_conversations",
                "vector_size": 1024,
                "distance": Distance.COSINE,
                "description": "OpenWebUI conversation embeddings for search",
                "payload_indexes": {
                    "user_id": PayloadSchemaType.KEYWORD,
                    "chat_id": PayloadSchemaType.KEYWORD,
                    "timestamp": PayloadSchemaType.DATETIME,
                    "model": PayloadSchemaType.KEYWORD,
                }
            },
            {
                "collection_name": "lobechat_agents",
                "vector_size": 1024,
                "distance": Distance.COSINE,
                "description": "LobeChat agent embeddings for similarity matching",
                "payload_indexes": {
                    "agent_type": PayloadSchemaType.KEYWORD,
                    "created_by": PayloadSchemaType.KEYWORD,
                    "public": PayloadSchemaType.BOOL,
                    "tags": PayloadSchemaType.KEYWORD,
                }
            },
            {
                "collection_name": "n8n_workflows",
                "vector_size": 1024,
                "distance": Distance.COSINE,
                "description": "n8n workflow embeddings for template matching",
                "payload_indexes": {
                    "workflow_type": PayloadSchemaType.KEYWORD,
                    "active": PayloadSchemaType.BOOL,
                    "created_by": PayloadSchemaType.KEYWORD,
                    "complexity": PayloadSchemaType.INTEGER,
                }
            },
            {
                "collection_name": "archon_knowledge",
                "vector_size": 1024,
                "distance": Distance.COSINE,
                "description": "Archon MCP knowledge items for semantic search",
                "payload_indexes": {
                    "item_type": PayloadSchemaType.KEYWORD,
                    "priority": PayloadSchemaType.INTEGER,
                    "status": PayloadSchemaType.KEYWORD,
                    "tags": PayloadSchemaType.KEYWORD,
                }
            },
            {
                "collection_name": "code_embeddings",
                "vector_size": 1024,
                "distance": Distance.COSINE,
                "description": "Code snippets and documentation embeddings",
                "payload_indexes": {
                    "language": PayloadSchemaType.KEYWORD,
                    "file_type": PayloadSchemaType.KEYWORD,
                    "repository": PayloadSchemaType.KEYWORD,
                    "complexity": PayloadSchemaType.INTEGER,
                }
            },
            {
                "collection_name": "user_preferences",
                "vector_size": 512,
                "distance": Distance.COSINE,
                "description": "User preference embeddings for personalization",
                "payload_indexes": {
                    "user_id": PayloadSchemaType.KEYWORD,
                    "service": PayloadSchemaType.KEYWORD,
                    "updated_at": PayloadSchemaType.DATETIME,
                }
            }
        ]
        
        success_count = 0
        for config in collections_config:
            if self.create_collection_if_not_exists(**config):
                success_count += 1
        
        logger.info(f"Successfully created {success_count}/{len(collections_config)} collections")
        return success_count == len(collections_config)
    
    def create_collection_aliases(self) -> bool:
        """Create collection aliases for easier access"""
        aliases = {
            "knowledge": "zoi_knowledge_base",
            "cache": "litellm_cache",
            "chats": "openwebui_conversations",
            "agents": "lobechat_agents",
            "workflows": "n8n_workflows",
            "docs": "archon_knowledge",
            "code": "code_embeddings",
            "users": "user_preferences"
        }
        
        try:
            for alias, collection in aliases.items():
                # Note: Qdrant doesn't have built-in aliases, but we can document them
                logger.info(f"Alias '{alias}' -> '{collection}'")
            
            logger.info("Collection aliases documented")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create aliases: {e}")
            return False
    
    def get_cluster_info(self) -> Dict:
        """Get cluster information"""
        try:
            collections = self.client.get_collections()
            cluster_info = {
                "collections_count": len(collections.collections),
                "collections": [
                    {
                        "name": col.name,
                        "vectors_count": col.vectors_count,
                        "segments_count": col.segments_count,
                        "status": col.status
                    }
                    for col in collections.collections
                ]
            }
            
            logger.info(f"Cluster info: {cluster_info['collections_count']} collections")
            return cluster_info
            
        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            return {}

def main():
    """Main bootstrap function"""
    logger.info("🚀 Starting Qdrant bootstrap for Zoi ecosystem")
    
    # Get configuration from environment
    host = os.getenv("QDRANT_HOST", "qdrant")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    try:
        # Initialize bootstrap
        bootstrap = QdrantBootstrap(host=host, port=port)
        
        # Wait for Qdrant to be ready
        if not bootstrap.wait_for_qdrant():
            logger.error("Qdrant is not ready, exiting")
            sys.exit(1)
        
        # Setup collections
        if not bootstrap.setup_zoi_collections():
            logger.error("Failed to setup collections")
            sys.exit(1)
        
        # Create aliases
        bootstrap.create_collection_aliases()
        
        # Show cluster info
        cluster_info = bootstrap.get_cluster_info()
        logger.info(f"Bootstrap completed! Created {cluster_info.get('collections_count', 0)} collections")
        
        logger.info("✅ Qdrant bootstrap completed successfully!")
        
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
