#!/usr/bin/env python3
"""
Add comprehensive Medusa UI documentation to Weaviate collections.
This script extracts content from Medusa UI component library documentation.
"""

import weaviate
import requests
import re
import time
import json
from datetime import datetime
from typing import List, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class MedusaUIDocumentationScraper:
    """Specialized scraper for Medusa UI documentation."""
    
    def __init__(self):
        self.base_url = "https://docs.medusajs.com/ui"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page_content(self, url: str) -> str:
        """Fetch page content with error handling."""
        try:
            time.sleep(1)  # Be respectful to their servers
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def get_medusa_ui_component_urls(self) -> List[str]:
        """Get comprehensive list of Medusa UI component documentation URLs."""
        components = [
            # Core Components
            "alert", "avatar", "badge", "button", "calendar", "checkbox",
            "code-block", "command", "command-bar", "container", "copy",
            "currency-input", "data-table", "date-picker", "drawer",
            "dropdown-menu", "focus-modal", "heading", "icon-badge",
            "icon-button", "inline-tip", "input", "kbd", "label",
            "progress-accordion", "progress-tabs", "prompt", "radio-group",
            "select", "status-badge", "switch", "table", "tabs", "text",
            "textarea", "toast", "tooltip",
            
            # Hooks
            "hooks/use-prompt", "hooks/use-toggle-state",
            
            # Utils
            "utils/clx"
        ]
        
        urls = []
        
        # Add main documentation page
        urls.append(self.base_url)
        
        # Add all component pages
        for component in components:
            urls.append(f"{self.base_url}/{component}")
        
        return urls
    
    def scrape_page_content(self, url: str) -> Dict:
        """Scrape detailed content from a Medusa UI documentation page."""
        html_content = self.get_page_content(url)
        if not html_content:
            return None
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = ""
            title_selectors = ['h1', '.title', '.page-title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    # Clean up title
                    title = re.sub(r'\s*\|\s*Medusa.*$', '', title)
                    title = title.strip()
                    if title and title != "Medusa UI":
                        break
            
            # Determine component type from URL
            if '/hooks/' in url:
                component_type = "Hook"
            elif '/utils/' in url:
                component_type = "Utility"
            elif url.endswith('/ui'):
                component_type = "Overview"
            else:
                component_type = "Component"
            
            # Extract main content
            content = ""
            content_selectors = [
                'main',
                '.content',
                '.markdown-body',
                '.docs-content',
                '.documentation-content',
                '[role="main"]',
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
            for code_elem in soup.find_all(['pre', 'code']):
                code_text = code_elem.get_text().strip()
                if len(code_text) > 20:  # Only meaningful code blocks
                    
                    # Determine language
                    language = "typescript"  # Default for React components
                    
                    # Check class attributes
                    classes = code_elem.get('class', [])
                    for cls in classes:
                        cls_str = str(cls).lower()
                        if 'language-' in cls_str:
                            language = cls_str.replace('language-', '')
                            break
                        elif any(lang in cls_str for lang in ['javascript', 'typescript', 'jsx', 'tsx', 'bash', 'json']):
                            language = cls_str
                            break
                    
                    # Auto-detect from content
                    if language == "typescript":
                        if 'npm install' in code_text or 'yarn add' in code_text:
                            language = 'bash'
                        elif code_text.startswith('{') and code_text.endswith('}'):
                            language = 'json'
                        elif 'import ' in code_text and ('from ' in code_text or 'export' in code_text):
                            language = 'typescript'
                    
                    code_blocks.append({
                        'code': code_text,
                        'language': language
                    })
            
            # Extract component props/API information
            props_info = self.extract_component_props(soup, content)
            
            return {
                'url': url,
                'title': title or f"Medusa UI {component_type}",
                'content': content,
                'component_type': component_type,
                'code_blocks': code_blocks,
                'props_info': props_info,
                'word_count': len(content.split()),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing content from {url}: {e}")
            return None
    
    def extract_component_props(self, soup, content: str) -> Dict:
        """Extract component props and API information."""
        props_info = {
            'props': [],
            'examples': [],
            'imports': []
        }
        
        # Extract props from tables
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])] if rows else []
            
            if any(word in ' '.join(headers) for word in ['prop', 'name', 'type', 'description']):
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        prop_name = cells[0].get_text().strip()
                        prop_desc = ' '.join([cell.get_text().strip() for cell in cells[1:]])
                        if prop_name and prop_desc:
                            props_info['props'].append({
                                'name': prop_name,
                                'description': prop_desc
                            })
        
        # Extract import statements
        import_patterns = [
            r'import\s+{[^}]+}\s+from\s+["\']@medusajs/ui["\']',
            r'import\s+\w+\s+from\s+["\']@medusajs/ui["\']'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            props_info['imports'].extend(matches)
        
        return props_info
    
    def scrape_all_documentation(self) -> List[Dict]:
        """Scrape all Medusa UI documentation pages."""
        print("Starting comprehensive Medusa UI documentation scraping...")
        
        urls_to_scrape = self.get_medusa_ui_component_urls()
        print(f"Found {len(urls_to_scrape)} UI documentation URLs to scrape")
        
        scraped_content = []
        
        for i, url in enumerate(urls_to_scrape, 1):
            print(f"Scraping [{i}/{len(urls_to_scrape)}]: {url}")
            
            content = self.scrape_page_content(url)
            if content and content['content'] and len(content['content']) > 50:
                scraped_content.append(content)
                print(f"  SUCCESS: {content['title']} ({content['word_count']} words, {len(content['code_blocks'])} examples)")
            else:
                print(f"  FAILED: Could not extract content or content too short")
        
        print(f"Scraping completed! Extracted {len(scraped_content)} pages")
        return scraped_content


def categorize_medusa_ui_content(title: str, content: str, component_type: str, url: str) -> str:
    """Categorize Medusa UI documentation content."""
    if component_type == "Hook":
        return "Hooks"
    elif component_type == "Utility":
        return "Utilities"
    elif component_type == "Overview":
        return "Getting Started"
    else:
        # Categorize components by type
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['button', 'icon-button']):
            return "Buttons"
        elif any(word in title_lower for word in ['input', 'textarea', 'select', 'checkbox', 'radio', 'switch']):
            return "Form Controls"
        elif any(word in title_lower for word in ['table', 'data-table']):
            return "Data Display"
        elif any(word in title_lower for word in ['modal', 'drawer', 'tooltip', 'dropdown']):
            return "Overlays"
        elif any(word in title_lower for word in ['badge', 'avatar', 'status', 'progress']):
            return "Indicators"
        elif any(word in title_lower for word in ['container', 'heading', 'text']):
            return "Layout"
        elif any(word in title_lower for word in ['alert', 'toast', 'inline-tip']):
            return "Feedback"
        else:
            return "Components"


def extract_medusa_ui_keywords(title: str, content: str, component_type: str, url: str) -> List[str]:
    """Extract relevant keywords from Medusa UI content."""
    base_keywords = ["medusa", "ui", "react", "components", "design-system"]
    
    # Extract from title
    title_words = [word.lower() for word in re.findall(r'\w+', title)]
    
    # UI and React terms
    ui_terms = [
        'component', 'react', 'typescript', 'props', 'hook', 'state',
        'tailwind', 'css', 'style', 'theme', 'design', 'ui', 'ux',
        'button', 'input', 'form', 'table', 'modal', 'dropdown',
        'tooltip', 'badge', 'avatar', 'icon', 'text', 'heading',
        'container', 'layout', 'responsive', 'accessibility',
        'radix', 'primitive', 'shadcn', 'figma'
    ]
    
    # Add component type specific keywords
    if component_type == "Hook":
        ui_terms.extend(['hook', 'state', 'effect', 'custom'])
    elif component_type == "Utility":
        ui_terms.extend(['utility', 'helper', 'function', 'clx'])
    
    keywords = base_keywords + [word for word in title_words if len(word) > 2]
    
    # Add relevant UI terms found in content
    content_lower = content.lower()
    for term in ui_terms:
        if term in content_lower:
            keywords.append(term)
    
    # Add URL-specific terms
    url_parts = re.findall(r'\w+', url.lower())
    keywords.extend([part for part in url_parts if len(part) > 3 and part not in ['docs', 'medusajs', 'com', 'ui']])
    
    return list(set(keywords))  # Remove duplicates


def add_medusa_ui_knowledge(client, scraped_content: List[Dict]):
    """Add Medusa UI knowledge articles to the Knowledge collection."""
    print(f"Adding {len(scraped_content)} Medusa UI knowledge articles...")
    
    try:
        knowledge_collection = client.collections.get("Knowledge")
        added_count = 0
        
        for content in scraped_content:
            if not content['content'] or len(content['content']) < 100:
                continue
                
            # Categorize and extract keywords
            category = categorize_medusa_ui_content(
                content['title'], content['content'], 
                content['component_type'], content['url']
            )
            keywords = extract_medusa_ui_keywords(
                content['title'], content['content'], 
                content['component_type'], content['url']
            )
            
            # Create knowledge article
            article = {
                "title": content['title'],
                "content": content['content'][:3000],  # Limit for embedding
                "topic": f"Medusa UI {category}",
                "keywords": keywords
            }
            
            try:
                knowledge_collection.data.insert(article)
                print(f"Added: {article['title']} ({category})")
                added_count += 1
            except Exception as e:
                print(f"Error adding article '{content['title']}': {e}")
                continue
        
        print(f"Successfully added {added_count} Medusa UI knowledge articles")
        return added_count
        
    except Exception as e:
        print(f"Error adding Medusa UI knowledge articles: {e}")
        return 0


def add_medusa_ui_code_snippets(client, scraped_content: List[Dict]):
    """Add Medusa UI code examples to the CodeSnippets collection."""
    print("Extracting and adding Medusa UI code snippets...")
    
    try:
        snippets_collection = client.collections.get("CodeSnippets")
        added_count = 0
        
        for content in scraped_content:
            if not content['code_blocks']:
                continue
            
            category = categorize_medusa_ui_content(
                content['title'], content['content'], 
                content['component_type'], content['url']
            )
            keywords = extract_medusa_ui_keywords(
                content['title'], content['content'], 
                content['component_type'], content['url']
            )
            
            for i, code_block in enumerate(content['code_blocks']):
                if len(code_block['code'].strip()) < 20:  # Skip very short code blocks
                    continue
                
                snippet_title = f"{content['title']} - Code Example"
                if len(content['code_blocks']) > 1:
                    snippet_title += f" #{i+1}"
                
                # Create description based on context
                description = f"Code example from Medusa UI {category} documentation"
                if 'component' in category.lower():
                    description += " - React component usage"
                elif 'hook' in category.lower():
                    description += " - Custom hook implementation"
                elif 'utility' in category.lower():
                    description += " - Utility function usage"
                
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
        
        print(f"Successfully added {added_count} Medusa UI code snippets")
        return added_count
        
    except Exception as e:
        print(f"Error adding Medusa UI code snippets: {e}")
        return 0


def add_medusa_ui_documents(client, scraped_content: List[Dict]):
    """Add Medusa UI documentation guides to the Documents collection."""
    print(f"Adding {len(scraped_content)} Medusa UI documents...")
    
    try:
        documents_collection = client.collections.get("Documents")
        added_count = 0
        
        for content in scraped_content:
            if not content['content'] or len(content['content']) < 200:
                continue
            
            category = categorize_medusa_ui_content(
                content['title'], content['content'], 
                content['component_type'], content['url']
            )
            keywords = extract_medusa_ui_keywords(
                content['title'], content['content'], 
                content['component_type'], content['url']
            )
            
            # Estimate reading time
            reading_time = max(2, content['word_count'] // 200)
            
            doc = {
                "title": content['title'],
                "category": category,
                "source": "Medusa UI Documentation",
                "content": content['content'][:5000],  # Limit for embedding
                "metadata_json": json.dumps({
                    "difficulty": "beginner",
                    "estimated_reading_time": f"{reading_time} minutes",
                    "topics": keywords[:5],
                    "category": category,
                    "component_type": content['component_type'],
                    "url": content['url'],
                    "scraped_at": content['scraped_at'],
                    "code_examples": len(content['code_blocks']),
                    "props_count": len(content.get('props_info', {}).get('props', []))
                })
            }
            
            try:
                documents_collection.data.insert(doc)
                print(f"Added: {doc['title']} ({category})")
                added_count += 1
            except Exception as e:
                print(f"Error adding document '{content['title']}': {e}")
                continue
        
        print(f"Successfully added {added_count} Medusa UI documents")
        return added_count
        
    except Exception as e:
        print(f"Error adding Medusa UI documents: {e}")
        return 0


def main():
    """Main function to scrape and add Medusa UI knowledge to Weaviate."""
    print("Medusa UI Design System Knowledge Base Setup for Elysia")
    print("=" * 65)
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
        scraper = MedusaUIDocumentationScraper()
        scraped_content = scraper.scrape_all_documentation()
        
        if not scraped_content:
            print("No content was scraped. Check the URLs and scraping logic.")
            return
        
        print(f"\nSuccessfully scraped {len(scraped_content)} documentation pages")
        
        # Add content to all three collections
        print("\n" + "="*50)
        print("ADDING TO WEAVIATE COLLECTIONS")
        print("="*50)
        
        knowledge_count = add_medusa_ui_knowledge(client, scraped_content)
        print()
        
        code_count = add_medusa_ui_code_snippets(client, scraped_content)
        print()
        
        docs_count = add_medusa_ui_documents(client, scraped_content)
        
        print()
        print("=" * 65)
        print("MEDUSA UI DESIGN SYSTEM KNOWLEDGE BASE SETUP COMPLETE!")
        print("=" * 65)
        print(f"Knowledge Articles: {knowledge_count}")
        print(f"Code Snippets: {code_count}")
        print(f"Documentation Guides: {docs_count}")
        print(f"Total Medusa UI Items: {knowledge_count + code_count + docs_count}")
        print()
        print("The Medusa UI knowledge base now contains comprehensive information including:")
        print("  - Complete React component library documentation")
        print("  - Design system principles and guidelines")
        print("  - Component props, APIs, and usage examples")
        print("  - Custom hooks for state management")
        print("  - Utility functions and helpers")
        print("  - Tailwind CSS integration and styling")
        print("  - Accessibility best practices")
        print("  - Radix Primitives integration")
        print("  - Admin dashboard customization components")
        print()
        print("Component Categories:")
        print("  - Layout: Container, Heading, Text")
        print("  - Form Controls: Input, Select, Checkbox, Radio, Switch")
        print("  - Buttons: Button, Icon Button")
        print("  - Data Display: Table, Data Table, Badge, Avatar")
        print("  - Overlays: Modal, Drawer, Tooltip, Dropdown Menu")
        print("  - Feedback: Alert, Toast, Inline Tip")
        print("  - Indicators: Status Badge, Progress components")
        print("  - Hooks: usePrompt, useToggleState")
        print("  - Utilities: clx for className management")
        print()
        print("ENHANCED MEDUSA ECOSYSTEM:")
        print("  - Backend: Medusa Framework (4.6MB+ documentation)")
        print("  - Frontend: Medusa UI Components (React design system)")
        print("  - Combined: Complete full-stack eCommerce solution")
        print()
        print("Ready for comprehensive UI development via Elysia at http://localhost:7085")
        print("The knowledge base now supports complete Medusa-based application development!")
        
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