#!/usr/bin/env python3
"""
LiteLLM Custom Vector Store Provider for Unified RAG

This integrates our unified RAG service with LiteLLM's native vector store system,
allowing seamless cross-collection search through LiteLLM's standard API.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import httpx

logger = logging.getLogger(__name__)

class UnifiedRAGVectorStoreProvider:
    """
    Custom LiteLLM vector store provider that connects to our unified RAG service.
    This allows LiteLLM to use our cross-collection search as a native vector store.
    """
    
    def __init__(self, api_base: str = "http://unified-rag:8000"):
        self.api_base = api_base.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def search(
        self,
        query: str,
        vector_store_id: str,
        limit: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search the unified RAG service and return results in LiteLLM format.
        
        Args:
            query: The search query text
            vector_store_id: The vector store ID (should be "unified_all_collections")
            limit: Maximum number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            List of search results in LiteLLM format
        """
        try:
            # Prepare search request
            search_request = {
                "query_text": query,
                "limit": limit
            }
            
            # Make request to unified RAG service
            response = await self.client.post(
                f"{self.api_base}/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if not data.get("success", False):
                logger.error(f"Unified RAG search failed: {data.get('error', 'Unknown error')}")
                return []
            
            # Convert to LiteLLM format
            litellm_results = []
            for result in data.get("results", []):
                litellm_result = {
                    "id": f"{result['collection']}_{hash(result['content'][:100])}",
                    "content": result["content"],
                    "metadata": {
                        "source": result["source"],
                        "collection": result["collection"],
                        "score": result["score"],
                        **result.get("metadata", {})
                    },
                    "score": result["score"]
                }
                litellm_results.append(litellm_result)
            
            logger.info(f"✅ Unified RAG search returned {len(litellm_results)} results")
            return litellm_results
            
        except Exception as e:
            logger.error(f"❌ Unified RAG search error: {e}")
            return []
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """Get available collections from the unified RAG service."""
        try:
            response = await self.client.get(f"{self.api_base}/collections")
            response.raise_for_status()
            
            data = response.json()
            return data.get("collections", [])
            
        except Exception as e:
            logger.error(f"❌ Failed to get collections: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if the unified RAG service is healthy."""
        try:
            response = await self.client.get(f"{self.api_base}/health")
            response.raise_for_status()
            
            data = response.json()
            return data.get("status") == "healthy"
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Integration function for LiteLLM
async def unified_rag_vector_search(
    query: str,
    vector_store_id: str,
    limit: int = 10,
    **kwargs
) -> str:
    """
    Function that LiteLLM can call to perform unified RAG search.
    Returns formatted context string for injection into messages.
    
    Args:
        query: Search query
        vector_store_id: Vector store identifier
        limit: Maximum results
        **kwargs: Additional parameters
        
    Returns:
        Formatted context string
    """
    provider = UnifiedRAGVectorStoreProvider()
    
    try:
        # Perform search
        results = await provider.search(query, vector_store_id, limit, **kwargs)
        
        if not results:
            return "No relevant context found."
        
        # Format results for context injection
        context_parts = []
        context_parts.append("## Relevant Context from Knowledge Base:")
        context_parts.append("")
        
        for i, result in enumerate(results[:limit], 1):
            source_info = f"[{result['metadata']['collection']}]"
            if result['metadata'].get('source'):
                source_info += f" ({result['metadata']['source']})"
            
            context_parts.append(f"### {i}. {source_info}")
            context_parts.append(f"**Relevance Score:** {result['score']:.3f}")
            context_parts.append("")
            context_parts.append(result['content'])
            context_parts.append("")
            context_parts.append("---")
            context_parts.append("")
        
        # Add summary
        collections_used = set(r['metadata']['collection'] for r in results)
        context_parts.append(f"*Context retrieved from {len(collections_used)} collections: {', '.join(sorted(collections_used))}*")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"❌ Unified RAG context generation failed: {e}")
        return f"Error retrieving context: {str(e)}"
    
    finally:
        await provider.close()

# Test function
async def test_unified_rag_provider():
    """Test the unified RAG provider."""
    provider = UnifiedRAGVectorStoreProvider()
    
    try:
        # Test health check
        is_healthy = await provider.health_check()
        print(f"Health check: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
        
        if not is_healthy:
            return
        
        # Test collections
        collections = await provider.get_collections()
        print(f"Available collections: {len(collections)}")
        for collection in collections[:3]:  # Show first 3
            print(f"  - {collection['name']} ({collection['type']})")
        
        # Test search
        results = await provider.search(
            query="test search",
            vector_store_id="unified_all_collections",
            limit=5
        )
        print(f"Search results: {len(results)}")
        
        # Test context generation
        context = await unified_rag_vector_search(
            query="test context generation",
            vector_store_id="unified_all_collections",
            limit=3
        )
        print(f"Generated context length: {len(context)} characters")
        
    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(test_unified_rag_provider())
