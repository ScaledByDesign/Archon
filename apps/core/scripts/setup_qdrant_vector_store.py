#!/usr/bin/env python3
"""
Qdrant Vector Store Setup for Zoi AI Stack
==========================================

This script initializes Qdrant collections and tests vector store integration
with LiteLLM for RAG (Retrieval Augmented Generation) capabilities.

Features:
- Creates Qdrant collection for knowledge base
- Tests embedding generation via LiteLLM
- Stores sample documents with vectors
- Tests semantic search functionality
- Validates RAG pipeline end-to-end
"""

import requests
import json
import time
import sys
from typing import List, Dict, Any

# Configuration
QDRANT_URL = "http://localhost:7060"
LITELLM_URL = "http://localhost:7010"
LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"
COLLECTION_NAME = "zoi_knowledge_base"
VECTOR_SIZE = 1024  # mxbai-embed-large dimension

def check_services():
    """Check if Qdrant and LiteLLM services are available."""
    print("🔍 Checking service availability...")
    
    # Check Qdrant
    try:
        response = requests.get(f"{QDRANT_URL}/collections")
        print(f"✅ Qdrant: Available (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Qdrant: Not available - {e}")
        return False
    
    # Check LiteLLM
    try:
        headers = {"Authorization": f"Bearer {LITELLM_API_KEY}"}
        response = requests.get(f"{LITELLM_URL}/v1/models", headers=headers)
        print(f"✅ LiteLLM: Available (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ LiteLLM: Not available - {e}")
        return False
    
    return True

def create_collection():
    """Create Qdrant collection for vector storage."""
    print(f"📚 Creating Qdrant collection: {COLLECTION_NAME}")
    
    collection_config = {
        "name": COLLECTION_NAME,
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine"
        },
        "optimizers_config": {
            "default_segment_number": 2
        },
        "replication_factor": 1
    }
    
    try:
        response = requests.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
            json=collection_config
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Collection '{COLLECTION_NAME}' created successfully")
            return True
        else:
            print(f"❌ Failed to create collection: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return False

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using LiteLLM zoi-embed model."""
    headers = {
        "Authorization": f"Bearer {LITELLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "zoi-embed",
        "input": text
    }
    
    try:
        response = requests.post(
            f"{LITELLM_URL}/v1/embeddings",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["data"][0]["embedding"]
        else:
            print(f"❌ Embedding generation failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None

def store_sample_documents():
    """Store sample documents in Qdrant with embeddings."""
    print("📝 Storing sample documents with embeddings...")
    
    sample_docs = [
        {
            "id": 1,
            "text": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and AI.",
            "metadata": {"category": "programming", "language": "python"}
        },
        {
            "id": 2,
            "text": "Docker is a containerization platform that allows developers to package applications with their dependencies into lightweight, portable containers.",
            "metadata": {"category": "devops", "tool": "docker"}
        },
        {
            "id": 3,
            "text": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without explicit programming.",
            "metadata": {"category": "ai", "field": "machine_learning"}
        },
        {
            "id": 4,
            "text": "Redis is an in-memory data structure store used as a database, cache, and message broker. It supports various data structures like strings, hashes, and lists.",
            "metadata": {"category": "database", "type": "cache"}
        },
        {
            "id": 5,
            "text": "Vector databases like Qdrant are specialized for storing and searching high-dimensional vectors, enabling semantic search and RAG applications.",
            "metadata": {"category": "database", "type": "vector"}
        }
    ]
    
    points = []
    for doc in sample_docs:
        print(f"  📄 Processing: {doc['text'][:50]}...")
        
        # Generate embedding
        embedding = generate_embedding(doc["text"])
        if embedding is None:
            print(f"  ❌ Failed to generate embedding for document {doc['id']}")
            continue
        
        # Create point for Qdrant
        point = {
            "id": doc["id"],
            "vector": embedding,
            "payload": {
                "text": doc["text"],
                **doc["metadata"]
            }
        }
        points.append(point)
        print(f"  ✅ Embedded document {doc['id']} ({len(embedding)} dimensions)")
    
    # Store all points in Qdrant
    if points:
        try:
            response = requests.put(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points",
                json={"points": points}
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Stored {len(points)} documents in Qdrant")
                return True
            else:
                print(f"❌ Failed to store documents: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error storing documents: {e}")
            return False
    
    return False

def test_semantic_search(query: str):
    """Test semantic search functionality."""
    print(f"🔍 Testing semantic search with query: '{query}'")
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    if query_embedding is None:
        print("❌ Failed to generate query embedding")
        return False
    
    # Search in Qdrant
    search_payload = {
        "vector": query_embedding,
        "limit": 3,
        "with_payload": True
    }
    
    try:
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
            json=search_payload
        )
        
        if response.status_code == 200:
            results = response.json()["result"]
            print(f"✅ Found {len(results)} relevant documents:")
            
            for i, result in enumerate(results, 1):
                score = result["score"]
                text = result["payload"]["text"]
                category = result["payload"].get("category", "unknown")
                
                print(f"  {i}. Score: {score:.3f} | Category: {category}")
                print(f"     Text: {text[:100]}...")
                print()
            
            return True
        else:
            print(f"❌ Search failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return False

def main():
    """Main setup and testing function."""
    print("🚀 Qdrant Vector Store Setup for Zoi AI Stack")
    print("=" * 50)
    
    # Step 1: Check services
    if not check_services():
        print("❌ Required services not available. Please ensure Qdrant and LiteLLM are running.")
        sys.exit(1)
    
    print()
    
    # Step 2: Create collection
    if not create_collection():
        print("❌ Failed to create Qdrant collection")
        sys.exit(1)
    
    print()
    
    # Step 3: Store sample documents
    if not store_sample_documents():
        print("❌ Failed to store sample documents")
        sys.exit(1)
    
    print()
    
    # Step 4: Test semantic search
    test_queries = [
        "How to use containers for deployment?",
        "What is artificial intelligence?",
        "Database caching solutions"
    ]
    
    for query in test_queries:
        test_semantic_search(query)
        print("-" * 40)
    
    print("🎉 Qdrant Vector Store setup complete!")
    print("✅ RAG capabilities are now available through LiteLLM")

if __name__ == "__main__":
    main()
