#!/usr/bin/env python3
"""
Add comprehensive NMI payments documentation to Weaviate collections.
This script extracts content from the NMI Developer Portal and populates
Knowledge, CodeSnippets, and Documents collections.
"""

import weaviate
import requests
import re
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class NMIDocumentationScraper:
    """Specialized scraper for NMI documentation website."""
    
    def __init__(self, base_url="https://docs.nmi.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_urls = set()
        self.content = []
        
    def get_page_content(self, url: str) -> str:
        """Fetch page content with error handling and rate limiting."""
        try:
            time.sleep(1)  # Be respectful to their servers
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def extract_main_sections(self) -> List[str]:
        """Extract main documentation URLs from the site structure."""
        known_sections = [
            "/reference/getting-started",
            "/reference/authentication", 
            "/reference/testing-methods",
            "/reference/rate-limiting",
            "/reference/pagination",
            "/reference/response-codes",
            "/reference/payment-processing",
            "/reference/gateway-features", 
            "/reference/processors-and-services",
            "/reference/data-and-transaction-reporting",
            "/reference/customer-token-vault",
            "/reference/txt2pay",
            "/reference/webhooks-overview",
            "/reference/retry-logic",
            "/reference/transaction-events",
            "/reference/device-sdks"
        ]
        
        return [urljoin(self.base_url, section) for section in known_sections]
    
    def scrape_page_content(self, url: str) -> Dict:
        """Scrape detailed content from a documentation page."""
        html_content = self.get_page_content(url)
        if not html_content:
            return None
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = ""
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()
            
            # Extract main content
            content = ""
            
            # Look for main content areas
            content_selectors = [
                '.content',
                '.main-content', 
                '.documentation-content',
                'main',
                '[role="main"]',
                '.markdown-body'
            ]
            
            content_elem = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break
            
            if not content_elem:
                # Fallback to body content, excluding navigation
                content_elem = soup.find('body')
                if content_elem:
                    # Remove navigation elements
                    for nav in content_elem.find_all(['nav', 'header', 'footer']):
                        nav.decompose()
            
            if content_elem:
                content = content_elem.get_text().strip()
            
            # Extract code examples
            code_blocks = []
            for code_elem in soup.find_all(['code', 'pre']):
                code_text = code_elem.get_text().strip()
                if len(code_text) > 10:  # Only meaningful code blocks
                    
                    # Determine language from class attributes
                    language = "text"
                    classes = code_elem.get('class', [])
                    for cls in classes:
                        if 'language-' in str(cls):
                            language = str(cls).replace('language-', '')
                            break
                        elif any(lang in str(cls).lower() for lang in ['json', 'javascript', 'curl', 'bash', 'xml', 'html']):
                            language = str(cls).lower()
                            break
                    
                    # Auto-detect language from content
                    if language == "text":
                        language = self.detect_code_language(code_text)
                    
                    code_blocks.append({
                        'code': code_text,
                        'language': language
                    })
            
            # Extract API endpoints if present
            api_endpoints = []
            endpoint_patterns = [
                r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)',
                r'https?://[^\s]+/api[^\s]*'
            ]
            
            for pattern in endpoint_patterns:
                matches = re.findall(pattern, content)
                api_endpoints.extend(matches)
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'code_blocks': code_blocks,
                'api_endpoints': api_endpoints,
                'word_count': len(content.split()),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing content from {url}: {e}")
            return None
    
    def detect_code_language(self, code: str) -> str:
        """Detect programming language from code content."""
        code_lower = code.lower()
        
        # API calls and HTTP
        if any(method in code for method in ['POST', 'GET', 'PUT', 'DELETE']):
            return 'http'
        elif 'curl ' in code or 'curl-' in code:
            return 'bash'
        elif code.startswith('{') and code.endswith('}'):
            return 'json'
        elif '<?xml' in code or '<xml' in code:
            return 'xml'
        elif '<html' in code or '<div' in code:
            return 'html'
        elif 'function ' in code or 'var ' in code or '=>' in code:
            return 'javascript'
        elif 'import ' in code and 'from ' in code:
            return 'python'
        elif '#include' in code or 'int main' in code:
            return 'c'
        elif 'public class' in code or 'import java' in code:
            return 'java'
        elif 'SELECT ' in code.upper() or 'INSERT ' in code.upper():
            return 'sql'
        else:
            return 'text'
    
    def scrape_all_documentation(self) -> List[Dict]:
        """Scrape all NMI documentation pages."""
        print("Starting comprehensive NMI documentation scraping...")
        
        urls_to_scrape = self.extract_main_sections()
        print(f"Found {len(urls_to_scrape)} main sections to scrape")
        
        scraped_content = []
        
        for i, url in enumerate(urls_to_scrape, 1):
            print(f"Scraping [{i}/{len(urls_to_scrape)}]: {url}")
            
            content = self.scrape_page_content(url)
            if content and content['content']:
                scraped_content.append(content)
                print(f"  SUCCESS: Extracted: {content['title']} ({content['word_count']} words)")
            else:
                print(f"  FAILED: Failed to extract content from {url}")
        
        print(f"Scraping completed! Extracted {len(scraped_content)} pages")
        return scraped_content


def categorize_nmi_content(title: str, content: str, url: str) -> str:
    """Categorize NMI documentation content."""
    title_lower = title.lower()
    content_lower = content.lower()
    url_lower = url.lower()
    
    if any(word in title_lower for word in ['getting started', 'overview', 'introduction']):
        return "Getting Started"
    elif any(word in title_lower for word in ['authentication', 'auth', 'security']):
        return "Authentication"  
    elif any(word in title_lower for word in ['payment', 'transaction', 'charge']):
        return "Payment Processing"
    elif any(word in title_lower for word in ['api', 'endpoint', 'reference']):
        return "API Reference"
    elif any(word in title_lower for word in ['webhook', 'notification', 'callback']):
        return "Webhooks"
    elif any(word in title_lower for word in ['sdk', 'library', 'client']):
        return "SDKs"
    elif any(word in title_lower for word in ['testing', 'sandbox', 'test']):
        return "Testing"
    elif any(word in title_lower for word in ['error', 'response', 'status']):
        return "Error Handling"
    elif any(word in title_lower for word in ['vault', 'token', 'customer']):
        return "Token Vault"
    elif any(word in title_lower for word in ['reporting', 'data', 'analytics']):
        return "Reporting"
    else:
        return "General"


def extract_nmi_keywords(title: str, content: str, url: str) -> List[str]:
    """Extract relevant keywords from NMI content."""
    base_keywords = ["nmi", "payment", "gateway", "api"]
    
    # Extract from title
    title_words = [word.lower() for word in re.findall(r'\w+', title)]
    
    # Payment and fintech terms
    fintech_terms = [
        'payment', 'transaction', 'gateway', 'merchant', 'processor',
        'authentication', 'security', 'token', 'vault', 'customer',
        'charge', 'refund', 'void', 'settlement', 'batch',
        'webhook', 'notification', 'callback', 'event',
        'sdk', 'api', 'endpoint', 'integration', 'sandbox',
        'credit', 'debit', 'card', 'ach', 'bank', 'account',
        'recurring', 'subscription', 'billing', 'invoice',
        'fraud', 'risk', 'compliance', 'pci', 'security'
    ]
    
    keywords = base_keywords + [word for word in title_words if len(word) > 2]
    
    # Add relevant fintech terms found in content
    content_lower = content.lower()
    for term in fintech_terms:
        if term in content_lower:
            keywords.append(term)
    
    # Add URL-specific terms
    url_parts = re.findall(r'\w+', url.lower())
    keywords.extend([part for part in url_parts if len(part) > 3 and part not in ['docs', 'nmi', 'com', 'reference']])
    
    return list(set(keywords))  # Remove duplicates


def add_nmi_knowledge(client, scraped_content: List[Dict]):
    """Add NMI knowledge articles to the Knowledge collection."""
    print(f"Adding {len(scraped_content)} NMI knowledge articles...")
    
    try:
        knowledge_collection = client.collections.get("Knowledge")
        added_count = 0
        
        for content in scraped_content:
            if not content['content'] or len(content['content']) < 100:
                continue
                
            # Categorize and extract keywords
            category = categorize_nmi_content(content['title'], content['content'], content['url'])
            keywords = extract_nmi_keywords(content['title'], content['content'], content['url'])
            
            # Create knowledge article
            article = {
                "title": content['title'] or "NMI Documentation",
                "content": content['content'][:3000],  # Limit for embedding
                "topic": f"NMI {category}",
                "keywords": keywords
            }
            
            try:
                knowledge_collection.data.insert(article)
                print(f"Added: {article['title']} ({category})")
                added_count += 1
            except Exception as e:
                print(f"Error adding article '{content['title']}': {e}")
                continue
        
        print(f"Successfully added {added_count} NMI knowledge articles")
        return added_count
        
    except Exception as e:
        print(f"Error adding NMI knowledge articles: {e}")
        return 0


def add_nmi_code_snippets(client, scraped_content: List[Dict]):
    """Add NMI code examples to the CodeSnippets collection."""
    print("Extracting and adding NMI code snippets...")
    
    try:
        snippets_collection = client.collections.get("CodeSnippets")
        added_count = 0
        
        for content in scraped_content:
            if not content['code_blocks']:
                continue
            
            category = categorize_nmi_content(content['title'], content['content'], content['url'])
            keywords = extract_nmi_keywords(content['title'], content['content'], content['url'])
            
            for i, code_block in enumerate(content['code_blocks']):
                if len(code_block['code'].strip()) < 20:  # Skip very short code blocks
                    continue
                
                snippet_title = f"{content['title']} - Code Example"
                if len(content['code_blocks']) > 1:
                    snippet_title += f" #{i+1}"
                
                # Create description based on context
                description = f"Code example from NMI {category} documentation"
                if 'payment' in category.lower():
                    description += " - Payment processing implementation"
                elif 'webhook' in category.lower():
                    description += " - Webhook integration"
                elif 'auth' in category.lower():
                    description += " - Authentication setup"
                elif 'api' in category.lower():
                    description += " - API integration"
                
                snippet = {
                    'title': snippet_title,
                    'language': code_block['language'],
                    'tags': keywords,
                    'description': description,
                    'code': code_block['code'].strip(),
                    'source_section': content['title']
                }
                
                try:
                    snippets_collection.data.insert(snippet)
                    print(f"Added: {snippet['title']} ({code_block['language']})")
                    added_count += 1
                except Exception as e:
                    print(f"Error adding snippet '{snippet['title']}': {e}")
                    continue
        
        print(f"Successfully added {added_count} NMI code snippets")
        return added_count
        
    except Exception as e:
        print(f"Error adding NMI code snippets: {e}")
        return 0


def add_nmi_documents(client, scraped_content: List[Dict]):
    """Add NMI documentation guides to the Documents collection."""
    print(f"Adding {len(scraped_content)} NMI documents...")
    
    try:
        documents_collection = client.collections.get("Documents")
        added_count = 0
        
        for content in scraped_content:
            if not content['content'] or len(content['content']) < 200:
                continue
            
            category = categorize_nmi_content(content['title'], content['content'], content['url'])
            keywords = extract_nmi_keywords(content['title'], content['content'], content['url'])
            
            # Estimate reading time
            reading_time = max(2, content['word_count'] // 200)
            
            doc = {
                "title": content['title'] or "NMI Documentation",
                "category": category,
                "source": "NMI Developer Portal",
                "content": content['content'][:5000],  # Limit for embedding
                "metadata_json": json.dumps({
                    "difficulty": "intermediate",
                    "estimated_reading_time": f"{reading_time} minutes",
                    "topics": keywords[:5],
                    "category": category,
                    "url": content['url'],
                    "scraped_at": content['scraped_at']
                })
            }
            
            try:
                documents_collection.data.insert(doc)
                print(f"Added: {doc['title']} ({category})")
                added_count += 1
            except Exception as e:
                print(f"Error adding document '{content['title']}': {e}")
                continue
        
        print(f"Successfully added {added_count} NMI documents")
        return added_count
        
    except Exception as e:
        print(f"Error adding NMI documents: {e}")
        return 0


def main():
    """Main function to scrape and add NMI knowledge to Weaviate."""
    print("NMI Payments Knowledge Base Setup for Elysia")
    print("=" * 60)
    print()
    
    # Connect to Weaviate
    try:
        client = weaviate.connect_to_local(host="localhost", port=7080, skip_init_checks=True)
        print("Connected to Weaviate successfully!")
    except Exception as e:
        print(f"Failed to connect to Weaviate: {e}")
        return
    
    try:
        # Initialize scraper and extract content
        scraper = NMIDocumentationScraper()
        scraped_content = scraper.scrape_all_documentation()
        
        if not scraped_content:
            print("No content was scraped. Check the URLs and scraping logic.")
            return
        
        print(f"\nSuccessfully scraped {len(scraped_content)} documentation pages")
        
        # Add content to all three collections
        print("\n" + "="*50)
        print("ADDING TO WEAVIATE COLLECTIONS")
        print("="*50)
        
        knowledge_count = add_nmi_knowledge(client, scraped_content)
        print()
        
        code_count = add_nmi_code_snippets(client, scraped_content)
        print()
        
        docs_count = add_nmi_documents(client, scraped_content)
        
        print()
        print("=" * 60)
        print("NMI PAYMENTS KNOWLEDGE BASE SETUP COMPLETE!")
        print("=" * 60)
        print(f"Knowledge Articles: {knowledge_count}")
        print(f"Code Snippets: {code_count}")
        print(f"Documentation Guides: {docs_count}")
        print(f"Total NMI Items: {knowledge_count + code_count + docs_count}")
        print()
        print("The NMI knowledge base now contains comprehensive information including:")
        print("  - Payment processing and gateway features")
        print("  - Authentication and security implementation")
        print("  - API endpoints and integration guides")
        print("  - Webhook configuration and event handling")
        print("  - SDKs and development tools")
        print("  - Testing and sandbox environments")
        print("  - Error handling and response codes")
        print("  - Customer token vault management")
        print("  - Transaction reporting and analytics")
        print()
        print("Coverage includes:")
        print("  - Complete API reference documentation")
        print("  - Real-world code examples and implementations")
        print("  - Integration guides for different scenarios")
        print("  - Security best practices and compliance")
        print("  - Troubleshooting and error resolution")
        print()
        print("Ready for comprehensive RAG operations via Elysia at http://localhost:7085")
        print("The knowledge base now supports Next.js, Medusa, and NMI Payments!")
        
    except Exception as e:
        print(f"Error during knowledge base setup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            client.close()
            print("\nWeaviate connection closed.")
        except:
            pass


if __name__ == "__main__":
    main()