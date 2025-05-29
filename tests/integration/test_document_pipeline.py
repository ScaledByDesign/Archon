#!/usr/bin/env python3
"""
Test Document Embedding Pipeline
Script to test document processing with various formats
"""

import os
import sys
import json
import time
import uuid
import requests
from pathlib import Path
from datetime import datetime

# API configuration
API_URL = "http://localhost:8000/api/documents"
UPLOAD_URL = f"{API_URL}/upload"
SEARCH_URL = f"{API_URL}/search"

# Test data directory
TEST_DIR = Path("./test_data")
TEST_DIR.mkdir(exist_ok=True)

# Create sample documents
def create_sample_documents():
    """Create sample documents in various formats"""
    print("Creating sample test documents...")
    
    # Create text file
    txt_path = TEST_DIR / "sample.txt"
    with open(txt_path, "w") as f:
        f.write("""
This is a sample text document for testing the document pipeline.
It contains multiple paragraphs to test text extraction and chunking.

Second paragraph with some content to ensure we have enough text
for proper chunking and embedding generation.

Third paragraph with more information about RAG systems and vector databases.
We want to ensure the semantic meaning is preserved in the embeddings.
        """)
    
    # Create HTML file
    html_path = TEST_DIR / "sample.html"
    with open(html_path, "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Sample HTML Document</title>
</head>
<body>
    <h1>Sample HTML for Testing</h1>
    <p>This is a sample HTML document to test the extraction capabilities.</p>
    <div>
        <h2>Section with Structured Content</h2>
        <p>The HTML extractor should be able to handle various HTML elements.</p>
        <ul>
            <li>Lists should be properly extracted</li>
            <li>Formatting should be preserved where possible</li>
        </ul>
    </div>
    <div>
        <h2>Another Section</h2>
        <p>More content to ensure we have enough text for testing chunking and embeddings.</p>
    </div>
</body>
</html>
        """)
    
    # Create Markdown file
    md_path = TEST_DIR / "sample.md"
    with open(md_path, "w") as f:
        f.write("""
# Sample Markdown Document

This is a sample markdown document for testing the extraction capabilities.

## Section 1

- Bullet point 1
- Bullet point 2

## Section 2

Some text with **bold** and *italic* formatting.

```python
def sample_code():
    return "This is code that should be extracted properly"
```

More text for testing chunking and embeddings.
        """)
    
    print(f"Created sample documents in {TEST_DIR}")
    return {
        "txt": txt_path,
        "html": html_path,
        "md": md_path
    }

def upload_document(file_path):
    """Upload document to API and return document ID"""
    print(f"Uploading {file_path}...")
    
    # Prepare file and metadata
    filename = file_path.name
    metadata = {
        "source": "test_script",
        "timestamp": datetime.now().isoformat(),
        "test_id": str(uuid.uuid4())
    }
    
    # Create multipart form data
    files = {
        'file': (filename, open(file_path, 'rb'), 'application/octet-stream')
    }
    
    data = {
        'metadata': json.dumps(metadata),
        'process_async': 'false'  # Process synchronously for testing
    }
    
    # Send request
    try:
        response = requests.post(UPLOAD_URL, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        document_id = result.get("document_id")
        print(f"Uploaded document {filename} with ID: {document_id}")
        return document_id
    except Exception as e:
        print(f"Error uploading document: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def check_document_status(document_id, max_retries=10, delay=2):
    """Check document processing status"""
    url = f"{API_URL}/{document_id}"
    
    for i in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            status = result.get("status")
            
            print(f"Document {document_id} status: {status}")
            
            if status == "completed":
                print(f"Processing stats: {json.dumps(result.get('processing_stats', {}), indent=2)}")
                return True
            elif status == "failed":
                print(f"Processing failed: {result.get('error')}")
                return False
            
            # Still processing, wait and retry
            print(f"Still processing, waiting {delay} seconds... (attempt {i+1}/{max_retries})")
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error checking status: {e}")
            time.sleep(delay)
    
    print(f"Timed out waiting for document {document_id} to process")
    return False

def search_documents(query, doc_ids=None, limit=5):
    """Search for documents matching query"""
    print(f'Searching for "{query}"...')
    
    # Prepare search request
    search_data = {
        "query": query,
        "limit": limit
    }
    
    # Add filter if document IDs provided
    if doc_ids:
        search_data["filter"] = {
            "document_id": {"$in": doc_ids}
        }
    
    # Send search request
    try:
        response = requests.post(SEARCH_URL, json=search_data)
        response.raise_for_status()
        result = response.json()
        
        print(f"Found {len(result['results'])} results for query: {query}")
        
        # Print top results
        for i, item in enumerate(result["results"]):
            print(f"\nResult {i+1} (score: {item.get('score', 'N/A')}):")
            print(f"Document: {item.get('document_filename', 'Unknown')}")
            print(f"Content: {item.get('content', '')[:150]}...")
        
        return result["results"]
    except Exception as e:
        print(f"Error searching documents: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return []

def main():
    """Main test function"""
    print("Testing Document Embedding Pipeline")
    print("==================================")
    
    # Create sample documents
    documents = create_sample_documents()
    
    # Upload documents and track IDs
    document_ids = {}
    for doc_type, file_path in documents.items():
        doc_id = upload_document(file_path)
        if doc_id:
            document_ids[doc_type] = doc_id
    
    if not document_ids:
        print("No documents were successfully uploaded. Exiting.")
        return
    
    print("\nUploaded Documents:")
    for doc_type, doc_id in document_ids.items():
        print(f"- {doc_type}: {doc_id}")
    
    # Check processing status for each document
    print("\nChecking Processing Status:")
    processed_docs = {}
    for doc_type, doc_id in document_ids.items():
        print(f"\nChecking status for {doc_type} document...")
        if check_document_status(doc_id):
            processed_docs[doc_type] = doc_id
    
    if not processed_docs:
        print("No documents were successfully processed. Exiting.")
        return
    
    # Wait a moment to ensure indexing is complete
    time.sleep(2)
    
    # Test search queries
    print("\nTesting Search Functionality:")
    queries = [
        "vector database",
        "HTML extraction",
        "markdown formatting",
        "RAG systems",
        "document testing"
    ]
    
    for query in queries:
        print(f"\nSearching for: {query}")
        search_documents(query, list(processed_docs.values()))
    
    print("\nDocument Pipeline Test Complete!")
    print("================================")

if __name__ == "__main__":
    main()
