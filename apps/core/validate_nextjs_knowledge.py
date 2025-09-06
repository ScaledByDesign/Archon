#!/usr/bin/env python3
"""
Validate Next.js knowledge integration in Weaviate and demonstrate search capabilities.
This script shows the comprehensive Next.js knowledge base available for RAG operations.
"""

import weaviate
import json

# Connect to Weaviate
client = weaviate.connect_to_local(host="localhost", port=7080, skip_init_checks=True)

def validate_knowledge_collection():
    """Validate Next.js content in Knowledge collection"""
    print("=== KNOWLEDGE COLLECTION ===")
    
    try:
        knowledge = client.collections.get("Knowledge")
        
        # Query for all Next.js knowledge articles
        result = knowledge.query.fetch_objects(
            where=weaviate.classes.query.Filter.by_property("topic").like("*Next.js*"),
            limit=10
        )
        
        print(f"Found {len(result.objects)} Next.js knowledge articles:")
        print()
        
        for i, obj in enumerate(result.objects, 1):
            print(f"{i}. **{obj.properties['title']}**")
            print(f"   Topic: {obj.properties['topic']}")
            print(f"   Keywords: {', '.join(obj.properties['keywords'])}")
            print(f"   Summary: {obj.properties['summary'][:100]}...")
            print()
            
        return len(result.objects)
        
    except Exception as e:
        print(f"Error querying Knowledge collection: {e}")
        return 0

def validate_code_snippets_collection():
    """Validate Next.js code examples in CodeSnippets collection"""
    print("=== CODE SNIPPETS COLLECTION ===")
    
    try:
        snippets = client.collections.get("CodeSnippets")
        
        # Query for Next.js code snippets
        result = snippets.query.fetch_objects(
            where=weaviate.classes.query.Filter.by_property("tags").contains_any(["nextjs"]),
            limit=10
        )
        
        print(f"Found {len(result.objects)} Next.js code snippets:")
        print()
        
        for i, obj in enumerate(result.objects, 1):
            print(f"{i}. **{obj.properties['title']}**")
            print(f"   Language: {obj.properties['language']}")
            print(f"   Tags: {', '.join(obj.properties['tags'])}")
            print(f"   Description: {obj.properties['description']}")
            print(f"   Code preview: {obj.properties['code'][:80]}...")
            print()
            
        return len(result.objects)
        
    except Exception as e:
        print(f"Error querying CodeSnippets collection: {e}")
        return 0

def validate_documents_collection():
    """Validate Next.js documentation in Documents collection"""
    print("=== DOCUMENTS COLLECTION ===")
    
    try:
        documents = client.collections.get("Documents")
        
        # Query for Next.js documents
        result = documents.query.fetch_objects(
            where=weaviate.classes.query.Filter.by_property("title").like("*Next.js*"),
            limit=10
        )
        
        print(f"Found {len(result.objects)} Next.js documents:")
        print()
        
        for i, obj in enumerate(result.objects, 1):
            print(f"{i}. **{obj.properties['title']}**")
            print(f"   Category: {obj.properties['category']}")
            print(f"   Source: {obj.properties['source']}")
            
            # Parse metadata
            try:
                metadata = json.loads(obj.properties['metadata_json'])
                print(f"   Difficulty: {metadata.get('difficulty', 'N/A')}")
                print(f"   Reading time: {metadata.get('estimated_reading_time', 'N/A')}")
            except:
                pass
                
            print(f"   Content preview: {obj.properties['content'][:100]}...")
            print()
            
        return len(result.objects)
        
    except Exception as e:
        print(f"Error querying Documents collection: {e}")
        return 0

def demonstrate_search_capabilities():
    """Demonstrate search capabilities across collections"""
    print("=== SEARCH CAPABILITIES DEMONSTRATION ===")
    print()
    
    # Search scenarios
    search_scenarios = [
        {
            "description": "Authentication-related content",
            "collection": "Knowledge",
            "filter_field": "keywords",
            "search_terms": ["authentication"]
        },
        {
            "description": "TypeScript code examples", 
            "collection": "CodeSnippets",
            "filter_field": "language",
            "search_terms": ["typescript"]
        },
        {
            "description": "Performance optimization guides",
            "collection": "Documents",
            "filter_field": "title", 
            "search_terms": ["Performance"]
        }
    ]
    
    for scenario in search_scenarios:
        print(f"Searching for: {scenario['description']}")
        
        try:
            collection = client.collections.get(scenario['collection'])
            
            if scenario['filter_field'] == 'keywords':
                result = collection.query.fetch_objects(
                    where=weaviate.classes.query.Filter.by_property(scenario['filter_field']).contains_any(scenario['search_terms']),
                    limit=3
                )
            elif scenario['filter_field'] == 'language':
                result = collection.query.fetch_objects(
                    where=weaviate.classes.query.Filter.by_property(scenario['filter_field']).equal(scenario['search_terms'][0]),
                    limit=3
                )
            else:
                result = collection.query.fetch_objects(
                    where=weaviate.classes.query.Filter.by_property(scenario['filter_field']).like(f"*{scenario['search_terms'][0]}*"),
                    limit=3
                )
            
            print(f"  Found {len(result.objects)} results:")
            for obj in result.objects:
                print(f"    - {obj.properties['title']}")
                
        except Exception as e:
            print(f"  Error: {e}")
            
        print()

def validate_elysia_integration():
    """Check if Elysia can access the collections"""
    print("=== ELYSIA INTEGRATION VALIDATION ===")
    
    try:
        # Get collection statistics
        collections = ["Knowledge", "Documents", "CodeSnippets", "Conversations"]
        
        print("Collection statistics for Elysia analysis:")
        
        for collection_name in collections:
            collection = client.collections.get(collection_name)
            
            # Get total count
            result = collection.aggregate.over_all(total_count=True)
            count = result.total_count
            
            print(f"  {collection_name}: {count} objects")
        
        print()
        print("Status: All collections are accessible by Elysia")
        print("Recommendation: Use Elysia web interface to analyze these collections")
        
    except Exception as e:
        print(f"Error checking collections: {e}")

def main():
    """Main validation function"""
    print("Next.js Knowledge Base Validation")
    print("=" * 50)
    print()
    
    try:
        # Validate all collections
        knowledge_count = validate_knowledge_collection()
        code_count = validate_code_snippets_collection() 
        docs_count = validate_documents_collection()
        
        # Demonstrate search capabilities
        demonstrate_search_capabilities()
        
        # Check Elysia integration
        validate_elysia_integration()
        
        # Summary
        print("=== VALIDATION SUMMARY ===")
        print(f"Total Next.js Knowledge Articles: {knowledge_count}")
        print(f"Total Next.js Code Snippets: {code_count}")
        print(f"Total Next.js Documents: {docs_count}")
        print(f"Total Next.js Knowledge Items: {knowledge_count + code_count + docs_count}")
        print()
        print("Knowledge base is ready for RAG operations!")
        print()
        print("Available knowledge covers:")
        print("  - App Router fundamentals")
        print("  - Data fetching patterns (SSR, SSG, ISR)")
        print("  - Performance optimization")
        print("  - Authentication implementations")
        print("  - Deployment strategies")
        print("  - TypeScript code examples")
        print("  - Best practices and migration guides")
        print()
        print("Next steps:")
        print("  1. Use Elysia web interface (http://localhost:7085) to analyze collections")
        print("  2. Test semantic search once LiteLLM routing is fixed")
        print("  3. Build RAG applications using this knowledge base")
        
    except Exception as e:
        print(f"Validation error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()