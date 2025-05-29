#!/usr/bin/env python3
"""
Test script for Qdrant Vector Database Integration
Verifies that the Python client can connect and perform basic operations.
"""

import sys
import os
import logging
import random
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.vector_store.vector_store import QdrantVectorStore, QdrantConfig, create_rag_collections, Collections

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """Test basic connection to Qdrant"""
    print("\n=== Testing Qdrant Connection ===")
    
    try:
        # Create client
        config = QdrantConfig.from_env()
        print(f"Connecting to Qdrant at {config.host}:{config.port}")
        
        client = QdrantVectorStore(config)
        print("✅ Successfully connected to Qdrant")
        
        # List existing collections
        collections = client.list_collections()
        print(f"📁 Existing collections: {collections}")
        
        return client
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None


def test_collection_operations(client: QdrantVectorStore):
    """Test collection creation and management"""
    print("\n=== Testing Collection Operations ===")
    
    test_collection = "test_collection"
    vector_size = 384  # Smaller size for testing
    
    try:
        # Create test collection
        print(f"Creating collection: {test_collection}")
        success = client.create_collection(
            collection_name=test_collection,
            vector_size=vector_size,
            recreate=True
        )
        
        if success:
            print("✅ Collection created successfully")
        else:
            print("❌ Failed to create collection")
            return False
        
        # Get collection info
        info = client.get_collection_info(test_collection)
        if info:
            print(f"📊 Collection info: {info}")
        
        # List collections again
        collections = client.list_collections()
        print(f"📁 Collections after creation: {collections}")
        
        return True
        
    except Exception as e:
        print(f"❌ Collection operations failed: {e}")
        return False


def test_vector_operations(client: QdrantVectorStore):
    """Test vector insertion, search, and deletion"""
    print("\n=== Testing Vector Operations ===")
    
    test_collection = "test_collection"
    vector_size = 384
    
    try:
        # Generate test vectors and payloads
        num_vectors = 5
        test_vectors = []
        test_payloads = []
        test_ids = []
        
        for i in range(num_vectors):
            # Create random vector
            vector = [random.random() for _ in range(vector_size)]
            test_vectors.append(vector)
            
            # Create payload with metadata
            payload = {
                "text": f"Sample document {i+1}",
                "category": "test" if i % 2 == 0 else "demo",
                "index": i,
                "metadata": {"source": "test_script", "created": "2024-01-01"}
            }
            test_payloads.append(payload)
            
            # Create ID
            test_ids.append(i+1)  # Use integer IDs
        
        # Insert vectors
        print(f"Inserting {num_vectors} test vectors...")
        success = client.upsert_vectors(
            collection_name=test_collection,
            vectors=test_vectors,
            payloads=test_payloads,
            ids=test_ids
        )
        
        if success:
            print("✅ Vectors inserted successfully")
        else:
            print("❌ Failed to insert vectors")
            return False
        
        # Count vectors
        count = client.count_vectors(test_collection)
        print(f"📊 Vector count: {count}")
        
        # Test similarity search
        print("🔍 Testing similarity search...")
        query_vector = test_vectors[0]  # Use first vector as query
        
        results = client.search_similar(
            collection_name=test_collection,
            query_vector=query_vector,
            limit=3,
            with_vectors=False
        )
        
        print(f"🎯 Found {len(results)} similar vectors:")
        for i, result in enumerate(results):
            print(f"  {i+1}. ID: {result.id}, Score: {result.score:.4f}")
            print(f"      Payload: {result.payload}")
        
        # Test filtered search
        print("🔍 Testing filtered search...")
        filter_results = client.search_similar(
            collection_name=test_collection,
            query_vector=query_vector,
            limit=5,
            filter_conditions={"category": "test"}
        )
        
        print(f"🎯 Found {len(filter_results)} filtered results:")
        for result in filter_results:
            print(f"  ID: {result.id}, Category: {result.payload.get('category')}")
        
        # Test vector deletion
        print("🗑️ Testing vector deletion...")
        delete_ids = [test_ids[0], test_ids[1]]  # Delete first two vectors
        success = client.delete_vectors(test_collection, delete_ids)
        
        if success:
            print(f"✅ Deleted {len(delete_ids)} vectors")
            new_count = client.count_vectors(test_collection)
            print(f"📊 New vector count: {new_count}")
        else:
            print("❌ Failed to delete vectors")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector operations failed: {e}")
        return False


def test_rag_collections(client: QdrantVectorStore):
    """Test creation of RAG-specific collections"""
    print("\n=== Testing RAG Collections Setup ===")
    
    try:
        # Create all RAG collections
        print("Creating RAG system collections...")
        results = create_rag_collections(
            client=client,
            vector_size=1536,  # OpenAI embedding size
            recreate=True
        )
        
        print("📁 RAG Collection creation results:")
        for collection_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {collection_name}")
        
        # List all collections
        all_collections = client.list_collections()
        print(f"📁 All collections: {all_collections}")
        
        # Get info for one collection
        if Collections.DOCUMENTS in all_collections:
            info = client.get_collection_info(Collections.DOCUMENTS)
            print(f"📊 Documents collection info: {info}")
        
        return all(results.values())
        
    except Exception as e:
        print(f"❌ RAG collections setup failed: {e}")
        return False


def cleanup(client: QdrantVectorStore):
    """Clean up test collections"""
    print("\n=== Cleanup ===")
    
    try:
        # Delete test collection
        test_collections = ["test_collection"]
        
        for collection in test_collections:
            if collection in client.list_collections():
                success = client.delete_collection(collection)
                status = "✅" if success else "❌"
                print(f"{status} Deleted collection: {collection}")
        
        # Close client
        client.close()
        print("✅ Client connection closed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def main():
    """Run all tests"""
    print("🚀 Starting Qdrant Integration Tests")
    print("=" * 50)
    
    # Test connection
    client = test_connection()
    if not client:
        sys.exit(1)
    
    try:
        # Run tests
        tests_passed = 0
        total_tests = 4
        
        if test_collection_operations(client):
            tests_passed += 1
        
        if test_vector_operations(client):
            tests_passed += 1
        
        if test_rag_collections(client):
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 50)
        print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! Qdrant integration is working correctly.")
            exit_code = 0
        else:
            print(f"⚠️  {total_tests - tests_passed} test(s) failed.")
            exit_code = 1
        
    finally:
        # Always cleanup
        cleanup(client)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
