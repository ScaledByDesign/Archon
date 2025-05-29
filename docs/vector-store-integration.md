# Qdrant Vector Database Integration

## Overview

This document outlines the integration of Qdrant as the vector database for the RAG (Retrieval-Augmented Generation) system. Qdrant provides high-performance vector similarity search capabilities for document embeddings, query vectors, and episodic memory.

## Architecture

### Components

1. **Qdrant Service**: Docker-containerized vector database
2. **Python Client**: Custom wrapper for Qdrant operations
3. **Collections**: Pre-configured vector collections for different data types
4. **Integration Layer**: Connection management and configuration

### Directory Structure

```
src/vector_store/
├── __init__.py              # Package initialization
├── vector_store.py          # Main Qdrant client implementation
└── test_qdrant.py          # Integration tests
```

## Configuration

### Environment Variables

Create or update your `.env` file with Qdrant configuration:

```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=                # Optional for cloud instances
QDRANT_TIMEOUT=60              # Request timeout in seconds
```

### Docker Configuration

The Qdrant service is configured in `docker-compose.yml`:

```yaml
qdrant:
  image: qdrant/qdrant:v1.7.0
  container_name: qdrant
  ports:
    - "6333:6333"    # REST API
    - "6334:6334"    # gRPC API
  volumes:
    - qdrant_data:/qdrant/storage
  environment:
    - QDRANT__SERVICE__HTTP_PORT=6333
    - QDRANT__SERVICE__GRPC_PORT=6334
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

## Collections Schema

The system automatically creates the following collections:

### 1. Documents Collection
- **Purpose**: Store document embeddings for retrieval
- **Vector Size**: 1536 (OpenAI embedding size)
- **Distance Metric**: Cosine similarity
- **Payload Schema**:
  ```json
  {
    "title": "string",
    "content": "string", 
    "source": "string",
    "created_at": "datetime",
    "metadata": "object"
  }
  ```

### 2. Queries Collection
- **Purpose**: Store user query embeddings for query expansion
- **Vector Size**: 1536
- **Distance Metric**: Cosine similarity
- **Payload Schema**:
  ```json
  {
    "query": "string",
    "intent": "string",
    "context": "object",
    "timestamp": "datetime"
  }
  ```

### 3. Chunks Collection
- **Purpose**: Store document chunk embeddings for fine-grained retrieval
- **Vector Size**: 1536
- **Distance Metric**: Cosine similarity
- **Payload Schema**:
  ```json
  {
    "content": "string",
    "document_id": "string",
    "chunk_index": "integer",
    "overlap": "boolean",
    "metadata": "object"
  }
  ```

### 4. Episodic Memory Collection
- **Purpose**: Store conversation context and user interactions
- **Vector Size**: 1536
- **Distance Metric**: Cosine similarity
- **Payload Schema**:
  ```json
  {
    "conversation_id": "string",
    "turn_index": "integer",
    "content": "string",
    "role": "string",
    "timestamp": "datetime"
  }
  ```

### 5. Procedural Memory Collection
- **Purpose**: Store task procedures and workflow patterns
- **Vector Size**: 1536
- **Distance Metric**: Cosine similarity
- **Payload Schema**:
  ```json
  {
    "procedure_name": "string",
    "steps": "array",
    "category": "string",
    "success_rate": "float",
    "metadata": "object"
  }
  ```

### 6. Tools Collection
- **Purpose**: Store tool descriptions and usage patterns
- **Vector Size**: 1536
- **Distance Metric**: Cosine similarity
- **Payload Schema**:
  ```json
  {
    "tool_name": "string",
    "description": "string",
    "parameters": "object",
    "usage_examples": "array",
    "category": "string"
  }
  ```

## Usage Examples

### Basic Setup

```python
from vector_store import QdrantVectorStore, QdrantConfig, create_rag_collections

# Initialize client
config = QdrantConfig.from_env()
client = QdrantVectorStore(config)

# Create RAG collections
results = create_rag_collections(client, vector_size=1536, recreate=True)
```

### Inserting Vectors

```python
# Prepare data
vectors = [[0.1, 0.2, 0.3, ...]]  # 1536-dimensional embeddings
payloads = [{
    "title": "Sample Document",
    "content": "This is a sample document for testing.",
    "source": "test_data",
    "created_at": "2024-01-01T00:00:00Z"
}]
ids = [1]  # Integer IDs or UUIDs

# Insert vectors
success = client.upsert_vectors(
    collection_name="documents",
    vectors=vectors,
    payloads=payloads,
    ids=ids
)
```

### Similarity Search

```python
# Basic search
results = client.search_similar(
    collection_name="documents",
    query_vector=query_embedding,
    limit=5,
    with_vectors=False
)

# Filtered search
filtered_results = client.search_similar(
    collection_name="documents", 
    query_vector=query_embedding,
    limit=5,
    filter_conditions={"source": "specific_source"}
)

# Process results
for result in results:
    print(f"ID: {result.id}, Score: {result.score}")
    print(f"Content: {result.payload['content']}")
```

### Collection Management

```python
# List collections
collections = client.list_collections()

# Get collection info
info = client.get_collection_info("documents")

# Count vectors
count = client.count_vectors("documents")

# Delete vectors
client.delete_vectors("documents", [1, 2, 3])

# Delete collection
client.delete_collection("test_collection")
```

## Testing

Run the integration tests to verify the setup:

```bash
# Install dependencies
python3 -m pip install -r requirements/vector_store.txt

# Run tests
python3 src/vector_store/test_qdrant.py
```

### Test Coverage

The test suite verifies:
- ✅ Connection to Qdrant service
- ✅ Collection creation and management
- ✅ Vector insertion and retrieval
- ✅ Similarity search functionality
- ✅ Filtered search capabilities
- ✅ Vector deletion operations
- ✅ RAG collections setup

## Performance Considerations

### Indexing

Qdrant automatically creates HNSW (Hierarchical Navigable Small World) indices for efficient similarity search. Key parameters:

- **m**: Number of connections in the graph (default: 16)
- **ef_construct**: Size of the dynamic candidate list (default: 100)
- **ef**: Search parameter controlling speed vs accuracy trade-off

### Memory Usage

- Vector storage: ~4 bytes per dimension (float32)
- Index overhead: ~20-50% of vector data size
- Payload storage: Variable based on JSON size

### Scaling

For production deployments:
- Use multiple Qdrant instances for horizontal scaling
- Implement sharding based on collection or data partitioning
- Monitor memory usage and optimize collection sizes
- Use quantization for reduced memory footprint

## Monitoring and Maintenance

### Health Checks

Monitor Qdrant health via:
- Docker health check: `curl -f http://localhost:6333/health`
- REST API: `GET /health`
- Collection status: Check collection info for status indicators

### Backup and Recovery

- Volume backups: Back up the `qdrant_data` Docker volume
- Collection exports: Use Qdrant's export functionality
- Point-in-time recovery: Implement incremental backup strategies

### Troubleshooting

Common issues and solutions:

1. **Connection refused**: Verify Qdrant service is running and ports are accessible
2. **Invalid point ID**: Ensure IDs are integers or valid UUIDs
3. **Dimension mismatch**: Verify vector dimensions match collection configuration
4. **Memory issues**: Monitor container resources and adjust limits

## Security

### Access Control

For production deployments:
- Enable API key authentication
- Use TLS/SSL for encrypted connections
- Implement network-level access controls
- Monitor access logs

### Data Protection

- Encrypt data at rest using volume encryption
- Implement secure backup procedures
- Use environment variables for sensitive configuration
- Regular security updates and patching

## Integration Points

### FastAPI Backend

```python
from fastapi import FastAPI
from vector_store import QdrantVectorStore, QdrantConfig

app = FastAPI()
vector_store = QdrantVectorStore(QdrantConfig.from_env())

@app.post("/search")
async def search_vectors(query_embedding: list[float]):
    results = vector_store.search_similar(
        collection_name="documents",
        query_vector=query_embedding,
        limit=10
    )
    return {"results": [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]}
```

### Embedding Services

```python
# OpenAI integration example
import openai
from vector_store import QdrantVectorStore

def embed_and_store(text: str, collection: str):
    # Generate embedding
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    embedding = response['data'][0]['embedding']
    
    # Store in Qdrant
    vector_store.upsert_vectors(
        collection_name=collection,
        vectors=[embedding],
        payloads=[{"text": text}],
        ids=[generate_id()]
    )
```

## Future Enhancements

- [ ] Implement collection aliasing for zero-downtime updates
- [ ] Add support for multiple vector spaces per collection
- [ ] Implement automatic rebalancing and optimization
- [ ] Add metrics and observability integration
- [ ] Support for hybrid search (vector + keyword)
- [ ] Implement caching layer for frequently accessed vectors
