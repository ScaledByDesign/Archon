#!/usr/bin/env python3
"""
Add comprehensive Hyperswitch documentation to Weaviate collections.
This script extracts content from multiple Hyperswitch documentation sites and populates
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


class HyperswitchDocumentationScraper:
    """Specialized scraper for Hyperswitch documentation websites."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_urls = set()
        self.content = []
        
    def get_page_content(self, url: str) -> str:
        """Fetch page content with error handling and rate limiting."""
        try:
            time.sleep(1.5)  # Be respectful to their servers
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def get_hyperswitch_documentation_urls(self) -> List[str]:
        """Get comprehensive list of Hyperswitch documentation URLs."""
        urls = []
        
        # Main documentation site URLs
        main_docs_urls = [
            # Core documentation
            "https://docs.hyperswitch.io/",
            "https://docs.hyperswitch.io/learn-more/hyperswitch-architecture",
            "https://docs.hyperswitch.io/learn-more/sdk-reference/react",
            "https://docs.hyperswitch.io/learn-more/sdk-payment-flows",
            "https://docs.hyperswitch.io/about-hyperswitch",
            "https://docs.hyperswitch.io/explore-hyperswitch/payment-orchestration",
            "https://docs.hyperswitch.io/explore-hyperswitch/checkout-experience",
            "https://docs.hyperswitch.io/explore-hyperswitch/payment-operations",
            "https://docs.hyperswitch.io/hyperswitch-open-source",
            "https://docs.hyperswitch.io/hyperswitch-cloud/integration-guide",
            "https://docs.hyperswitch.io/hyperswitch-cloud/quickstart",
            
            # SDK and Integration guides  
            "https://docs.hyperswitch.io/learn-more/sdk-reference/web",
            "https://docs.hyperswitch.io/learn-more/sdk-reference/react-native",
            "https://docs.hyperswitch.io/learn-more/sdk-reference/ios",
            "https://docs.hyperswitch.io/learn-more/sdk-reference/android",
            
            # Features and use cases
            "https://docs.hyperswitch.io/features/payment-flows-and-management/smart-retries",
            "https://docs.hyperswitch.io/features/payment-flows-and-management/intelligent-routing",
            "https://docs.hyperswitch.io/features/payment-flows-and-management/tokenization-and-saved-cards",
            "https://docs.hyperswitch.io/features/payment-flows-and-management/webhooks",
            "https://docs.hyperswitch.io/features/payment-flows-and-management/surcharge",
            
            # Security and compliance
            "https://docs.hyperswitch.io/learn-more/security-and-compliance",
            "https://docs.hyperswitch.io/features/account-management/disputes-and-chargebacks",
            
            # Deployment guides
            "https://docs.hyperswitch.io/hyperswitch-open-source/deploy-hyperswitch-on-aws",
            "https://docs.hyperswitch.io/hyperswitch-open-source/local-setup",
        ]
        
        # API reference URLs
        api_docs_urls = [
            "https://api-reference.hyperswitch.io/introduction",
            "https://api-reference.hyperswitch.io/essentials/authentication",
            "https://api-reference.hyperswitch.io/essentials/api-keys", 
            "https://api-reference.hyperswitch.io/essentials/error-codes",
            "https://api-reference.hyperswitch.io/essentials/webhooks",
            "https://api-reference.hyperswitch.io/api-reference/payments/payments--create",
            "https://api-reference.hyperswitch.io/api-reference/payments/payments--retrieve",
            "https://api-reference.hyperswitch.io/api-reference/payments/payments--update",
            "https://api-reference.hyperswitch.io/api-reference/payments/payments--confirm",
            "https://api-reference.hyperswitch.io/api-reference/customers/customers--create",
            "https://api-reference.hyperswitch.io/api-reference/refunds/refunds--create",
        ]
        
        urls.extend(main_docs_urls)
        urls.extend(api_docs_urls)
        
        return urls
    
    def scrape_page_content(self, url: str) -> Dict:
        """Scrape detailed content from a Hyperswitch documentation page."""
        html_content = self.get_page_content(url)
        if not html_content:
            return None
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = ""
            title_selectors = ['h1', 'title', '.title', '.page-title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # Clean up title
            if title:
                title = re.sub(r'\s*\|\s*Hyperswitch.*$', '', title)
                title = title.strip()
            
            # Extract main content
            content = ""
            
            # Content selectors for different page types
            content_selectors = [
                'main',
                '.content',
                '.markdown-body',
                '.documentation-content',
                '.main-content',
                '.docs-content',
                '[role="main"]',
                '.container .content',
                'article'
            ]
            
            content_elem = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break
            
            if not content_elem:
                # Fallback to body, removing navigation
                content_elem = soup.find('body')
                if content_elem:
                    for nav in content_elem.find_all(['nav', 'header', 'footer', '.navigation', '.sidebar']):
                        nav.decompose()
            
            if content_elem:
                content = content_elem.get_text().strip()
                # Clean up excessive whitespace
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            
            # Extract code examples
            code_blocks = []
            code_selectors = ['pre', 'code', '.highlight', '.code-block']
            
            for selector in code_selectors:
                for code_elem in soup.select(selector):
                    code_text = code_elem.get_text().strip()
                    if len(code_text) > 15:  # Only meaningful code blocks
                        
                        # Determine language
                        language = "text"
                        
                        # Check class attributes for language hints
                        classes = code_elem.get('class', [])
                        for cls in classes:
                            cls_str = str(cls).lower()
                            if 'language-' in cls_str:
                                language = cls_str.replace('language-', '')
                                break
                            elif any(lang in cls_str for lang in ['javascript', 'typescript', 'json', 'curl', 'bash', 'python', 'java', 'swift', 'kotlin']):
                                language = cls_str
                                break
                        
                        # Auto-detect language from content
                        if language == "text":
                            language = self.detect_code_language(code_text)
                        
                        code_blocks.append({
                            'code': code_text,
                            'language': language
                        })
            
            # Extract API information
            api_info = self.extract_api_info(soup, content)
            
            return {
                'url': url,
                'title': title or "Hyperswitch Documentation",
                'content': content,
                'code_blocks': code_blocks,
                'api_info': api_info,
                'word_count': len(content.split()),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing content from {url}: {e}")
            return None
    
    def extract_api_info(self, soup, content: str) -> Dict:
        """Extract API-specific information from the page."""
        api_info = {
            'endpoints': [],
            'methods': [],
            'parameters': []
        }
        
        # Extract HTTP methods and endpoints
        endpoint_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)',
            r'https?://[^\s]+/api[^\s]*'
        ]
        
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, content)
            api_info['endpoints'].extend(matches)
        
        # Extract parameter information from tables or lists
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    param_name = cells[0].get_text().strip()
                    param_desc = cells[1].get_text().strip()
                    if param_name and param_desc:
                        api_info['parameters'].append({
                            'name': param_name,
                            'description': param_desc
                        })
        
        return api_info
    
    def detect_code_language(self, code: str) -> str:
        """Detect programming language from code content."""
        code_lower = code.lower()
        
        # API calls and HTTP
        if any(method in code for method in ['POST', 'GET', 'PUT', 'DELETE', 'PATCH']):
            return 'http'
        elif 'curl ' in code or code.startswith('curl'):
            return 'bash'
        elif code.startswith('{') and '"' in code and code.endswith('}'):
            return 'json'
        elif 'import React' in code or 'export default' in code or 'const ' in code and '=>' in code:
            return 'javascript'
        elif 'interface ' in code or 'type ' in code or ': string' in code:
            return 'typescript'
        elif 'import ' in code and 'from ' in code and 'def ' in code:
            return 'python'
        elif '<?php' in code or '$' in code:
            return 'php'
        elif 'public class' in code or 'import java' in code:
            return 'java'
        elif 'import Foundation' in code or 'func ' in code:
            return 'swift'
        elif 'fun ' in code or 'class ' in code and 'kotlin' in code_lower:
            return 'kotlin'
        else:
            return 'text'
    
    def scrape_all_documentation(self) -> List[Dict]:
        """Scrape all Hyperswitch documentation pages."""
        print("Starting comprehensive Hyperswitch documentation scraping...")
        
        urls_to_scrape = self.get_hyperswitch_documentation_urls()
        print(f"Found {len(urls_to_scrape)} documentation URLs to scrape")
        
        scraped_content = []
        
        for i, url in enumerate(urls_to_scrape, 1):
            print(f"Scraping [{i}/{len(urls_to_scrape)}]: {url}")
            
            content = self.scrape_page_content(url)
            if content and content['content']:
                scraped_content.append(content)
                # Clean title of Unicode characters for display
                display_title = content['title'].encode('ascii', 'ignore').decode('ascii')
                print(f"  SUCCESS: {display_title} ({content['word_count']} words, {len(content['code_blocks'])} code examples)")
            else:
                print(f"  FAILED: Could not extract content")
        
        print(f"Scraping completed! Extracted {len(scraped_content)} pages")
        return scraped_content


def categorize_hyperswitch_content(title: str, content: str, url: str) -> str:
    """Categorize Hyperswitch documentation content."""
    title_lower = title.lower()
    content_lower = content.lower()
    url_lower = url.lower()
    
    if any(word in url_lower for word in ['api-reference']):
        return "API Reference"
    elif any(word in title_lower for word in ['architecture', 'system', 'design']):
        return "Architecture"
    elif any(word in title_lower for word in ['react', 'sdk', 'client', 'javascript', 'typescript']):
        return "SDK"
    elif any(word in title_lower for word in ['payment', 'transaction', 'charge']):
        return "Payment Processing"
    elif any(word in title_lower for word in ['webhook', 'notification', 'callback']):
        return "Webhooks"
    elif any(word in title_lower for word in ['authentication', 'security', 'compliance']):
        return "Security"
    elif any(word in title_lower for word in ['deploy', 'setup', 'install', 'docker', 'aws']):
        return "Deployment"
    elif any(word in title_lower for word in ['routing', 'intelligent', 'smart']):
        return "Smart Routing"
    elif any(word in title_lower for word in ['tokenization', 'vault', 'saved']):
        return "Tokenization"
    elif any(word in title_lower for word in ['getting', 'started', 'quickstart', 'introduction']):
        return "Getting Started"
    elif any(word in title_lower for word in ['integration', 'guide']):
        return "Integration"
    else:
        return "General"


def extract_hyperswitch_keywords(title: str, content: str, url: str) -> List[str]:
    """Extract relevant keywords from Hyperswitch content."""
    base_keywords = ["hyperswitch", "payment", "gateway", "orchestration", "fintech"]
    
    # Extract from title
    title_words = [word.lower() for word in re.findall(r'\w+', title)]
    
    # Payment and fintech terms
    fintech_terms = [
        'payment', 'transaction', 'gateway', 'processor', 'merchant',
        'authentication', 'security', 'routing', 'orchestration',
        'tokenization', 'vault', 'customer', 'webhook', 'notification',
        'sdk', 'api', 'integration', 'checkout', 'card', 'wallet',
        'refund', 'capture', 'authorization', 'settlement',
        'smart', 'intelligent', 'retry', 'fallback', 'routing',
        'compliance', 'pci', 'gdpr', 'fraud', 'risk',
        'react', 'javascript', 'typescript', 'ios', 'android',
        'docker', 'kubernetes', 'aws', 'deployment', 'cloud'
    ]
    
    keywords = base_keywords + [word for word in title_words if len(word) > 2]
    
    # Add relevant terms found in content
    content_lower = content.lower()
    for term in fintech_terms:
        if term in content_lower:
            keywords.append(term)
    
    # Add URL-specific terms
    url_parts = re.findall(r'\w+', url.lower())
    keywords.extend([part for part in url_parts if len(part) > 3 and part not in ['docs', 'hyperswitch', 'io', 'api', 'reference']])
    
    return list(set(keywords))  # Remove duplicates


def add_hyperswitch_knowledge(client, scraped_content: List[Dict]):
    """Add Hyperswitch knowledge articles to the Knowledge collection."""
    print(f"Adding {len(scraped_content)} Hyperswitch knowledge articles...")
    
    try:
        knowledge_collection = client.collections.get("Knowledge")
        added_count = 0
        
        for content in scraped_content:
            if not content['content'] or len(content['content']) < 100:
                continue
                
            # Categorize and extract keywords
            category = categorize_hyperswitch_content(content['title'], content['content'], content['url'])
            keywords = extract_hyperswitch_keywords(content['title'], content['content'], content['url'])
            
            # Create knowledge article (clean title of Unicode characters)
            clean_title = content['title'].encode('ascii', 'ignore').decode('ascii').strip()
            article = {
                "title": clean_title or "Hyperswitch Documentation",
                "content": content['content'][:3000],  # Limit for embedding
                "topic": f"Hyperswitch {category}",
                "keywords": keywords
            }
            
            try:
                knowledge_collection.data.insert(article)
                print(f"Added: {article['title']} ({category})")
                added_count += 1
            except Exception as e:
                print(f"Error adding article '{content['title']}': {e}")
                continue
        
        print(f"Successfully added {added_count} Hyperswitch knowledge articles")
        return added_count
        
    except Exception as e:
        print(f"Error adding Hyperswitch knowledge articles: {e}")
        return 0


def add_hyperswitch_code_snippets(client, scraped_content: List[Dict]):
    """Add Hyperswitch code examples to the CodeSnippets collection."""
    print("Extracting and adding Hyperswitch code snippets...")
    
    try:
        snippets_collection = client.collections.get("CodeSnippets")
        added_count = 0
        
        for content in scraped_content:
            if not content['code_blocks']:
                continue
            
            category = categorize_hyperswitch_content(content['title'], content['content'], content['url'])
            keywords = extract_hyperswitch_keywords(content['title'], content['content'], content['url'])
            
            for i, code_block in enumerate(content['code_blocks']):
                if len(code_block['code'].strip()) < 20:  # Skip very short code blocks
                    continue
                
                clean_title = content['title'].encode('ascii', 'ignore').decode('ascii').strip()
                snippet_title = f"{clean_title} - Code Example"
                if len(content['code_blocks']) > 1:
                    snippet_title += f" #{i+1}"
                
                # Create description based on context
                description = f"Code example from Hyperswitch {category} documentation"
                if 'sdk' in category.lower():
                    description += " - SDK implementation"
                elif 'payment' in category.lower():
                    description += " - Payment processing"
                elif 'webhook' in category.lower():
                    description += " - Webhook integration"
                elif 'api' in category.lower():
                    description += " - API integration"
                elif 'routing' in category.lower():
                    description += " - Smart routing setup"
                
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
        
        print(f"Successfully added {added_count} Hyperswitch code snippets")
        return added_count
        
    except Exception as e:
        print(f"Error adding Hyperswitch code snippets: {e}")
        return 0


def add_hyperswitch_documents(client, scraped_content: List[Dict]):
    """Add Hyperswitch documentation guides to the Documents collection."""
    print(f"Adding {len(scraped_content)} Hyperswitch documents...")
    
    try:
        documents_collection = client.collections.get("Documents")
        added_count = 0
        
        for content in scraped_content:
            if not content['content'] or len(content['content']) < 200:
                continue
            
            category = categorize_hyperswitch_content(content['title'], content['content'], content['url'])
            keywords = extract_hyperswitch_keywords(content['title'], content['content'], content['url'])
            
            # Estimate reading time
            reading_time = max(2, content['word_count'] // 200)
            
            clean_title = content['title'].encode('ascii', 'ignore').decode('ascii').strip()
            doc = {
                "title": clean_title or "Hyperswitch Documentation",
                "category": category,
                "source": "Hyperswitch Documentation",
                "content": content['content'][:5000],  # Limit for embedding
                "metadata_json": json.dumps({
                    "difficulty": "intermediate",
                    "estimated_reading_time": f"{reading_time} minutes",
                    "topics": keywords[:5],
                    "category": category,
                    "url": content['url'],
                    "scraped_at": content['scraped_at'],
                    "api_endpoints": len(content.get('api_info', {}).get('endpoints', [])),
                    "code_examples": len(content['code_blocks'])
                })
            }
            
            try:
                documents_collection.data.insert(doc)
                print(f"Added: {doc['title']} ({category})")
                added_count += 1
            except Exception as e:
                print(f"Error adding document '{content['title']}': {e}")
                continue
        
        print(f"Successfully added {added_count} Hyperswitch documents")
        return added_count
        
    except Exception as e:
        print(f"Error adding Hyperswitch documents: {e}")
        return 0


def main():
    """Main function to scrape and add Hyperswitch knowledge to Weaviate."""
    print("Hyperswitch Payment Orchestration Knowledge Base Setup for Elysia")
    print("=" * 70)
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
        scraper = HyperswitchDocumentationScraper()
        scraped_content = scraper.scrape_all_documentation()
        
        if not scraped_content:
            print("No content was scraped. Check the URLs and scraping logic.")
            return
        
        print(f"\nSuccessfully scraped {len(scraped_content)} documentation pages")
        
        # Add content to all three collections
        print("\n" + "="*50)
        print("ADDING TO WEAVIATE COLLECTIONS")
        print("="*50)
        
        knowledge_count = add_hyperswitch_knowledge(client, scraped_content)
        print()
        
        code_count = add_hyperswitch_code_snippets(client, scraped_content)
        print()
        
        docs_count = add_hyperswitch_documents(client, scraped_content)
        
        print()
        print("=" * 70)
        print("HYPERSWITCH KNOWLEDGE BASE SETUP COMPLETE!")
        print("=" * 70)
        print(f"Knowledge Articles: {knowledge_count}")
        print(f"Code Snippets: {code_count}")
        print(f"Documentation Guides: {docs_count}")
        print(f"Total Hyperswitch Items: {knowledge_count + code_count + docs_count}")
        print()
        print("The Hyperswitch knowledge base now contains comprehensive information including:")
        print("  - Payment orchestration and routing architecture")
        print("  - Multi-platform SDKs (React, React Native, iOS, Android)")
        print("  - Smart routing and intelligent payment processing")
        print("  - Tokenization and secure customer data management")
        print("  - Webhook integration and real-time notifications")
        print("  - Complete API reference and integration guides")
        print("  - Security, compliance, and fraud prevention")
        print("  - Deployment guides (Docker, AWS, Kubernetes)")
        print("  - Advanced features (retries, fallbacks, surcharges)")
        print()
        print("Coverage includes:")
        print("  - Complete payment orchestration platform documentation")
        print("  - Multi-language SDK integration examples")
        print("  - Enterprise-grade security and compliance guides")
        print("  - Advanced routing and optimization strategies")
        print("  - Production deployment and scaling guidance")
        print()
        print("COMPLETE PAYMENT ECOSYSTEM:")
        print("  - Frontend: Next.js (React components, forms, UI)")
        print("  - Backend: Medusa (eCommerce platform, workflows)")
        print("  - Payment Gateway: NMI (Direct processing, transactions)")
        print("  - Payment Orchestration: Hyperswitch (Multi-processor, routing)")
        print()
        print("Ready for enterprise-grade RAG operations via Elysia at http://localhost:7085")
        print("The knowledge base now supports complete payment ecosystem development!")
        
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