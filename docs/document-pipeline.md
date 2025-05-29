# Document Embedding Pipeline

## Overview

The Document Embedding Pipeline is a comprehensive system for processing, chunking, embedding, and storing documents for retrieval in the RAG system. It converts various document formats into vector embeddings suitable for semantic search.

## Architecture

The pipeline consists of several modular components:

1. **Text Extraction**: Extracts text from various document formats (PDF, DOCX, HTML, etc.)
2. **Text Cleaning**: Preprocesses text to remove noise and improve quality
3. **Document Chunking**: Splits documents into appropriate segments for embedding
4. **Embedding Generation**: Converts text chunks into vector embeddings
5. **Vector Storage**: Stores embeddings in Qdrant for retrieval
6. **Queue System**: Handles asynchronous document processing via RabbitMQ

## Key Features

- **Format Support**: Handles PDF, DOCX, HTML, TXT, and more
- **Configurable Chunking**: Multiple strategies including fixed-size, paragraph, semantic
- **Flexible Embedding Models**: Support for both local models and API-based embedding services
- **Asynchronous Processing**: Queue-based architecture for scalable document processing
- **Observability**: Langfuse integration for monitoring and tracing
- **Fault Tolerance**: Error handling, retry mechanisms, and dead-letter queues

## Components

### Text Extraction (`text_extraction.py`)

Extracts text from various document formats and handles document metadata.

```python
# Usage example
extractor = TextExtractor()
result = extractor.extract_text(file_content, filename)
```

### Text Cleaning (`text_cleaning.py`)

Cleans and normalizes extracted text, removing noise and irrelevant content.

```python
# Usage example
cleaner = TextCleaner()
cleaned_text = cleaner.clean_text(raw_text)
```

### Document Chunking (`document_chunker.py`)

Splits documents into smaller chunks for more effective embedding and retrieval.

- **Strategies**: 
  - `fixed_size`: Equal-sized chunks
  - `paragraph`: Split by paragraphs
  - `sentence`: Split by sentences
  - `hybrid`: Combine paragraphs until size limit
  - `semantic`: Split by semantic boundaries using NLP
  - `overlap`: Fixed size with overlapping content

```python
# Usage example
chunker = DocumentChunker(config=ChunkingConfig(
    strategy="hybrid",
    chunk_size=512,
    chunk_overlap=50
))
chunks = chunker.chunk_document(text, metadata, document_id)
```

### Embedding Generator (`embedding_generator.py`)

Generates vector embeddings from text chunks using various models.

- **Model Support**:
  - Local sentence-transformers models
  - OpenAI compatible embedding APIs via LiteLLM

```python
# Usage example
generator = EmbeddingGenerator(config=EmbeddingConfig(
    model_name=EmbeddingModel.MINILM_L6_V2
))
embeddings = generator.generate(text_chunks)
```

### Document Processor (`document_processor.py`)

Orchestrates the entire pipeline, coordinating between components.

```python
# Usage example
processor = DocumentProcessor()
await processor.process_document(file_content, filename, metadata)
```

### Queue Consumer (`queue_consumer.py`)

Handles asynchronous document processing via RabbitMQ.

```python
# Usage example
consumer = DocumentQueueConsumer()
await consumer.start()
```

## API Endpoints

The Document Pipeline exposes several FastAPI endpoints:

- **POST `/api/documents/upload`**: Upload and process a document
- **GET `/api/documents/{document_id}`**: Get document processing status
- **POST `/api/documents/search`**: Search for similar document chunks
- **GET `/api/documents/`**: List processed documents
- **DELETE `/api/documents/{document_id}`**: Delete a document

## Configuration

The pipeline is highly configurable through environment variables:

### General Settings
- `MONGODB_DOCUMENTS_COLLECTION`: Collection for document metadata
- `MONGODB_CHUNKS_COLLECTION`: Collection for document chunks
- `VECTOR_COLLECTION`: Collection for document embeddings
- `VECTOR_SIZE`: Embedding vector dimension

### Chunking Settings
- `DOCUMENT_CHUNKING_STRATEGY`: Chunking strategy (default: "hybrid")
- `DOCUMENT_CHUNK_SIZE`: Target characters per chunk (default: 512)
- `DOCUMENT_CHUNK_OVERLAP`: Overlap between chunks (default: 50)
- `DOCUMENT_MIN_CHUNK_SIZE`: Minimum chunk size (default: 100)
- `DOCUMENT_MAX_CHUNK_SIZE`: Maximum chunk size (default: 1024)
- `DOCUMENT_USE_SPACY`: Whether to use spaCy (default: false)

### Embedding Settings
- `EMBEDDING_MODEL`: Model name (default: "all-MiniLM-L6-v2")
- `EMBEDDING_BATCH_SIZE`: Batch size for embedding generation (default: 32)
- `EMBEDDING_USE_GPU`: Whether to use GPU (default: false)
- `EMBEDDING_NORMALIZE`: Whether to normalize embeddings (default: true)

### Queue Settings
- `RABBITMQ_URL`: RabbitMQ connection URL (default: "amqp://guest:guest@rabbitmq:5672/")

## Langfuse Observability Integration

The pipeline integrates with Langfuse for comprehensive tracing and monitoring:

- **Processing Traces**: Track document processing time and status
- **Component Spans**: Monitor individual component performance
- **Error Tracking**: Capture and analyze processing errors
- **Cost Monitoring**: Track embedding API usage and costs

## Performance Considerations

- **Vector Dimensions**: Higher dimensions provide better accuracy but increase storage and computation needs
- **Chunking Strategy**: Affects retrieval quality and storage requirements
- **Batch Processing**: Use batch processing for better throughput
- **Caching**: Embedding results are cached to avoid redundant processing

## Security Considerations

- **Sensitive Content**: Document content is stored in MongoDB and vector payloads
- **API Authentication**: All endpoints require authentication
- **Data Isolation**: Multi-tenant implementations should use collection namespacing

## Future Enhancements

- Metadata extraction from documents
- PDF table and image extraction
- Multi-lingual support
- Hybrid search capabilities
- Document versioning and update tracking
