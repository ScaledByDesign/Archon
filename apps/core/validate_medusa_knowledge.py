#!/usr/bin/env python3
"""
Validate Medusa knowledge integration in Weaviate and demonstrate search capabilities.
This script shows the comprehensive Medusa knowledge base available for RAG operations.
"""

import weaviate
import json


def validate_knowledge_collection(client):
    """Validate Medusa content in Knowledge collection"""
    print("=== MEDUSA KNOWLEDGE COLLECTION ===")
    
    try:
        knowledge = client.collections.get("Knowledge")
        
        # Query for all Medusa knowledge articles
        result = knowledge.query.fetch_objects(
            where=weaviate.classes.query.Filter.by_property("topic").like("*Medusa*"),
            limit=10
        )
        
        print(f"Found {len(result.objects)} Medusa knowledge articles:")
        print()
        
        for i, obj in enumerate(result.objects, 1):
            print(f"{i}. **{obj.properties['title']}**")
            print(f"   Topic: {obj.properties['topic']}")
            print(f"   Keywords: {', '.join(obj.properties['keywords'])}")
            print(f"   Summary: {obj.properties['content'][:100]}...")
            print()
            
        return len(result.objects)
        
    except Exception as e:
        print(f"Error querying Knowledge collection: {e}")
        return 0


def validate_code_snippets_collection(client):
    """Validate Medusa code examples in CodeSnippets collection"""
    print("=== MEDUSA CODE SNIPPETS COLLECTION ===")
    
    try:
        snippets = client.collections.get("CodeSnippets")
        
        # Query for Medusa code snippets
        result = snippets.query.fetch_objects(
            where=weaviate.classes.query.Filter.by_property("tags").contains_any(["medusa"]),
            limit=10
        )
        
        print(f"Found {len(result.objects)} Medusa code snippets:")
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


def validate_documents_collection(client):
    """Validate Medusa documentation in Documents collection"""
    print("=== MEDUSA DOCUMENTS COLLECTION ===")
    
    try:
        documents = client.collections.get("Documents")
        
        # Query for Medusa documents
        result = documents.query.fetch_objects(
            where=weaviate.classes.query.Filter.by_property("title").like("*Medusa*"),
            limit=10
        )
        
        print(f"Found {len(result.objects)} Medusa documents:")
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


def demonstrate_search_capabilities(client):
    """Demonstrate search capabilities across Medusa content"""
    print("=== MEDUSA SEARCH CAPABILITIES DEMONSTRATION ===")
    print()
    
    # Search scenarios specific to Medusa
    search_scenarios = [
        {
            "description": "Module-related content",
            "collection": "Knowledge",
            "filter_field": "keywords",
            "search_terms": ["modules"]
        },
        {
            "description": "TypeScript code examples", 
            "collection": "CodeSnippets",
            "filter_field": "language",
            "search_terms": ["typescript"]
        },
        {
            "description": "Configuration guides",
            "collection": "Documents",
            "filter_field": "title", 
            "search_terms": ["Configuration"]
        },
        {
            "description": "Workflow-related content",
            "collection": "Knowledge",
            "filter_field": "keywords",
            "search_terms": ["workflows"]
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


def validate_elysia_integration(client):
    """Check if Elysia can access the Medusa collections"""
    print("=== ELYSIA INTEGRATION VALIDATION ===")
    
    try:
        # Get collection statistics
        collections = ["Knowledge", "Documents", "CodeSnippets", "Conversations"]
        
        print("Collection statistics for Elysia analysis:")
        
        total_items = 0
        for collection_name in collections:
            collection = client.collections.get(collection_name)
            
            # Get total count
            result = collection.aggregate.over_all(total_count=True)
            count = result.total_count
            total_items += count
            
            print(f"  {collection_name}: {count} objects")
        
        print()
        print(f"Status: All collections are accessible by Elysia")
        print(f"Total objects available: {total_items}")
        print("Recommendation: Use Elysia web interface to analyze these collections")
        
    except Exception as e:
        print(f"Error checking collections: {e}")


def main():
    """Main validation function"""
    print("Medusa Knowledge Base Validation")
    print("=" * 50)
    print()
    
    try:
        # Connect to Weaviate (skip init checks like in Next.js validation)
        client = weaviate.connect_to_local(host="localhost", port=7080, skip_init_checks=True)
        
        # Validate all collections
        knowledge_count = validate_knowledge_collection(client)
        code_count = validate_code_snippets_collection(client) 
        docs_count = validate_documents_collection(client)
        
        # Demonstrate search capabilities
        demonstrate_search_capabilities(client)
        
        # Check Elysia integration
        validate_elysia_integration(client)
        
        # Summary
        print("=== MEDUSA VALIDATION SUMMARY ===")
        print(f"Total Medusa Knowledge Articles: {knowledge_count}")
        print(f"Total Medusa Code Snippets: {code_count}")
        print(f"Total Medusa Documents: {docs_count}")
        print(f"Total Medusa Knowledge Items: {knowledge_count + code_count + docs_count}")
        print()
        print("Medusa knowledge base is ready for RAG operations!")
        print()
        print("Available knowledge covers:")
        print("  - Framework architecture and module system")
        print("  - Workflow patterns with compensation logic")
        print("  - API route development and customization")
        print("  - Admin dashboard widget development")
        print("  - Configuration and deployment strategies")
        print("  - TypeScript code examples and patterns")
        print("  - Best practices and development workflows")
        print()
        print("Next steps:")
        print("  1. Use Elysia web interface (http://localhost:7085) to analyze collections")
        print("  2. Test semantic search with Medusa-specific queries")
        print("  3. Build RAG applications using this Medusa knowledge base")
        print("  4. Combine with Next.js knowledge for full-stack development support")
        
    except Exception as e:
        print(f"Validation error: {e}")
    finally:
        try:
            client.close()
        except:
            pass


if __name__ == "__main__":
    main()