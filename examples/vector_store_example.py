#!/usr/bin/env python3
"""
Example: RAG System Vector Store Usage
Demonstrates practical usage of the Qdrant vector store integration
"""

import sys
import os
import random
import json
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vector_store import QdrantVectorStore, QdrantConfig, create_rag_collections, Collections


class RAGVectorStore:
    """High-level interface for RAG system vector operations"""
    
    def __init__(self):
        """Initialize the RAG vector store"""
        config = QdrantConfig.from_env()
        self.client = QdrantVectorStore(config)
        
        # Ensure RAG collections exist
        print("🔧 Setting up RAG collections...")
        results = create_rag_collections(self.client, vector_size=1536, recreate=False)
        
        success_count = sum(results.values())
        print(f"✅ RAG collections ready: {success_count}/{len(results)} collections")
    
    def add_document(self, title: str, content: str, source: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Add a document to the vector store"""
        payload = {
            "title": title,
            "content": content,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Generate unique ID
        doc_id = hash(f"{source}:{title}") % (10**9)  # Simple ID generation
        
        success = self.client.upsert_vectors(
            collection_name=Collections.DOCUMENTS,
            vectors=[embedding],
            payloads=[payload],
            ids=[doc_id]
        )
        
        if success:
            print(f"📄 Added document: {title}")
        
        return success
    
    def add_document_chunk(self, content: str, document_id: str, chunk_index: int, embedding: List[float], overlap: bool = False) -> bool:
        """Add a document chunk to the vector store"""
        payload = {
            "content": content,
            "document_id": document_id,
            "chunk_index": chunk_index,
            "overlap": overlap,
            "created_at": datetime.now().isoformat()
        }
        
        chunk_id = hash(f"{document_id}:chunk:{chunk_index}") % (10**9)
        
        success = self.client.upsert_vectors(
            collection_name=Collections.CHUNKS,
            vectors=[embedding],
            payloads=[payload],
            ids=[chunk_id]
        )
        
        if success:
            print(f"📝 Added chunk {chunk_index} for document {document_id}")
        
        return success
    
    def store_query(self, query: str, intent: str, embedding: List[float], context: Dict[str, Any] = None) -> bool:
        """Store a user query for query expansion and analysis"""
        payload = {
            "query": query,
            "intent": intent,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        query_id = hash(f"{query}:{datetime.now().timestamp()}") % (10**9)
        
        success = self.client.upsert_vectors(
            collection_name=Collections.QUERIES,
            vectors=[embedding],
            payloads=[payload],
            ids=[query_id]
        )
        
        if success:
            print(f"🔍 Stored query: {query[:50]}...")
        
        return success
    
    def search_documents(self, query_embedding: List[float], limit: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        filter_conditions = {}
        if source_filter:
            filter_conditions["source"] = source_filter
        
        results = self.client.search_similar(
            collection_name=Collections.DOCUMENTS,
            query_vector=query_embedding,
            limit=limit,
            filter_conditions=filter_conditions if filter_conditions else None
        )
        
        documents = []
        for result in results:
            documents.append({
                "id": result.id,
                "score": result.score,
                "title": result.payload.get("title", ""),
                "content": result.payload.get("content", ""),
                "source": result.payload.get("source", ""),
                "metadata": result.payload.get("metadata", {})
            })
        
        print(f"📚 Found {len(documents)} similar documents")
        return documents
    
    def search_chunks(self, query_embedding: List[float], limit: int = 10, document_id_filter: str = None) -> List[Dict[str, Any]]:
        """Search for similar document chunks"""
        filter_conditions = {}
        if document_id_filter:
            filter_conditions["document_id"] = document_id_filter
        
        results = self.client.search_similar(
            collection_name=Collections.CHUNKS,
            query_vector=query_embedding,
            limit=limit,
            filter_conditions=filter_conditions if filter_conditions else None
        )
        
        chunks = []
        for result in results:
            chunks.append({
                "id": result.id,
                "score": result.score,
                "content": result.payload.get("content", ""),
                "document_id": result.payload.get("document_id", ""),
                "chunk_index": result.payload.get("chunk_index", 0)
            })
        
        print(f"📑 Found {len(chunks)} similar chunks")
        return chunks
    
    def find_similar_queries(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar historical queries for query expansion"""
        results = self.client.search_similar(
            collection_name=Collections.QUERIES,
            query_vector=query_embedding,
            limit=limit
        )
        
        queries = []
        for result in results:
            queries.append({
                "id": result.id,
                "score": result.score,
                "query": result.payload.get("query", ""),
                "intent": result.payload.get("intent", ""),
                "context": result.payload.get("context", {})
            })
        
        print(f"❓ Found {len(queries)} similar queries")
        return queries
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        stats = {}
        
        for collection in [Collections.DOCUMENTS, Collections.CHUNKS, Collections.QUERIES, Collections.EPISODIC, Collections.PROCEDURAL, Collections.TOOLS]:
            try:
                count = self.client.count_vectors(collection)
                info = self.client.get_collection_info(collection)
                stats[collection] = {
                    "count": count,
                    "status": str(info.get("status", "unknown")),
                    "vector_size": info.get("config", {}).get("vector_size", 0)
                }
            except Exception as e:
                stats[collection] = {"error": str(e)}
        
        return stats


def generate_sample_embedding(size: int = 1536) -> List[float]:
    """Generate a random embedding for testing purposes"""
    return [random.random() for _ in range(size)]


def demo_document_storage():
    """Demonstrate document storage and retrieval"""
    print("\n🚀 Demo: Document Storage and Retrieval")
    print("=" * 50)
    
    rag_store = RAGVectorStore()
    
    # Sample documents
    documents = [
        {
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data...",
            "source": "ml_textbook",
            "metadata": {"chapter": 1, "difficulty": "beginner"}
        },
        {
            "title": "Neural Network Fundamentals", 
            "content": "Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes...",
            "source": "ml_textbook",
            "metadata": {"chapter": 3, "difficulty": "intermediate"}
        },
        {
            "title": "Vector Databases Overview",
            "content": "Vector databases are specialized databases designed to store and query high-dimensional vectors efficiently...",
            "source": "database_guide",
            "metadata": {"category": "databases", "year": 2024}
        }
    ]
    
    # Add documents
    for doc in documents:
        embedding = generate_sample_embedding()
        rag_store.add_document(
            title=doc["title"],
            content=doc["content"],
            source=doc["source"],
            embedding=embedding,
            metadata=doc["metadata"]
        )
    
    # Add document chunks
    print("\n📝 Adding document chunks...")
    for i, doc in enumerate(documents):
        # Split content into chunks (simplified)
        words = doc["content"].split()
        chunk_size = len(words) // 2
        
        for chunk_idx in range(2):
            start_idx = chunk_idx * chunk_size
            end_idx = start_idx + chunk_size
            chunk_content = " ".join(words[start_idx:end_idx])
            
            embedding = generate_sample_embedding()
            rag_store.add_document_chunk(
                content=chunk_content,
                document_id=doc["title"],
                chunk_index=chunk_idx,
                embedding=embedding
            )
    
    # Search for similar documents
    print("\n🔍 Searching for similar documents...")
    query_embedding = generate_sample_embedding()
    similar_docs = rag_store.search_documents(query_embedding, limit=3)
    
    for i, doc in enumerate(similar_docs, 1):
        print(f"  {i}. {doc['title']} (score: {doc['score']:.4f})")
        print(f"     Source: {doc['source']}")
    
    # Search chunks
    print("\n📑 Searching for similar chunks...")
    similar_chunks = rag_store.search_chunks(query_embedding, limit=5)
    
    for i, chunk in enumerate(similar_chunks, 1):
        print(f"  {i}. Document: {chunk['document_id']}, Chunk: {chunk['chunk_index']}")
        print(f"     Score: {chunk['score']:.4f}")
        print(f"     Content: {chunk['content'][:80]}...")


def demo_query_management():
    """Demonstrate query storage and similarity search"""
    print("\n🚀 Demo: Query Management")
    print("=" * 50)
    
    rag_store = RAGVectorStore()
    
    # Sample queries
    queries = [
        {"query": "What is machine learning?", "intent": "definition"},
        {"query": "How do neural networks work?", "intent": "explanation"},
        {"query": "Explain backpropagation algorithm", "intent": "technical_details"},
        {"query": "What are the types of machine learning?", "intent": "classification"},
        {"query": "How to implement a neural network?", "intent": "implementation"}
    ]
    
    # Store queries
    for query_data in queries:
        embedding = generate_sample_embedding()
        rag_store.store_query(
            query=query_data["query"],
            intent=query_data["intent"],
            embedding=embedding,
            context={"session": "demo", "user_type": "student"}
        )
    
    # Find similar queries
    print("\n❓ Finding similar queries...")
    test_query_embedding = generate_sample_embedding()
    similar_queries = rag_store.find_similar_queries(test_query_embedding, limit=3)
    
    for i, query in enumerate(similar_queries, 1):
        print(f"  {i}. \"{query['query']}\" (score: {query['score']:.4f})")
        print(f"     Intent: {query['intent']}")


def demo_system_stats():
    """Show system statistics"""
    print("\n🚀 Demo: System Statistics")
    print("=" * 50)
    
    rag_store = RAGVectorStore()
    stats = rag_store.get_stats()
    
    print("📊 Vector Store Statistics:")
    for collection, data in stats.items():
        if "error" in data:
            print(f"  ❌ {collection}: {data['error']}")
        else:
            print(f"  ✅ {collection}: {data['count']} vectors, {data['vector_size']}D, {data['status']}")


def main():
    """Run all demonstrations"""
    print("🎯 RAG Vector Store Integration Demo")
    print("=" * 60)
    
    try:
        # Run demonstrations
        demo_document_storage()
        demo_query_management()
        demo_system_stats()
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext Steps:")
        print("1. Integrate with your embedding service (OpenAI, Hugging Face, etc.)")
        print("2. Connect to your FastAPI backend")
        print("3. Implement real document chunking and preprocessing")
        print("4. Add proper error handling and logging")
        print("5. Set up monitoring and backup procedures")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
