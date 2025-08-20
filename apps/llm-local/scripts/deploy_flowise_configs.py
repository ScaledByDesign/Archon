#!/usr/bin/env python3
"""
Flowise Configuration Deployment Script
=======================================

This script deploys Flowise chatflow configurations via API calls,
allowing for Infrastructure as Code (IaC) approach to Flowise setup.

Features:
- Deploy chatflows from JSON files
- Create credentials programmatically
- Validate configurations before deployment
- Support for batch deployment
- Environment-specific configurations
"""

import requests
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Configuration
FLOWISE_URL = "http://localhost:7070"
FLOWISE_API_BASE = f"{FLOWISE_URL}/api/v1"
CONFIG_DIR = Path(__file__).parent.parent / "flowise-configs"

class FlowiseDeployer:
    def __init__(self, base_url: str = FLOWISE_API_BASE, api_key: str = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
    def check_flowise_health(self) -> bool:
        """Check if Flowise is accessible."""
        try:
            response = requests.get(f"{FLOWISE_URL}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Flowise health check failed: {e}")
            return False
    
    def get_existing_chatflows(self) -> List[Dict]:
        """Get list of existing chatflows."""
        try:
            response = requests.get(f"{self.base_url}/chatflows", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get existing chatflows: {e}")
            return []
    
    def create_chatflow(self, chatflow_data: Dict) -> Dict:
        """Create a new chatflow."""
        try:
            response = requests.post(
                f"{self.base_url}/chatflows",
                headers=self.headers,
                json=chatflow_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to create chatflow: {e}")
            return None
    
    def update_chatflow(self, chatflow_id: str, chatflow_data: Dict) -> Dict:
        """Update an existing chatflow."""
        try:
            response = requests.put(
                f"{self.base_url}/chatflows/{chatflow_id}",
                headers=self.headers,
                json=chatflow_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to update chatflow: {e}")
            return None
    
    def deploy_chatflow(self, config_file: Path) -> bool:
        """Deploy a chatflow from JSON configuration."""
        print(f"📁 Loading configuration: {config_file.name}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                chatflow_config = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load config file: {e}")
            return False
        
        # Validate required fields
        required_fields = ['name', 'nodes', 'edges']
        for field in required_fields:
            if field not in chatflow_config:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check if chatflow already exists
        existing_chatflows = self.get_existing_chatflows()
        existing_chatflow = None
        
        for cf in existing_chatflows:
            if cf.get('name') == chatflow_config['name']:
                existing_chatflow = cf
                break
        
        if existing_chatflow:
            print(f"🔄 Updating existing chatflow: {chatflow_config['name']}")
            result = self.update_chatflow(existing_chatflow['id'], chatflow_config)
        else:
            print(f"🆕 Creating new chatflow: {chatflow_config['name']}")
            result = self.create_chatflow(chatflow_config)
        
        if result:
            chatflow_id = result.get('id', 'unknown')
            print(f"✅ Successfully deployed chatflow: {chatflow_config['name']} (ID: {chatflow_id})")
            return True
        else:
            print(f"❌ Failed to deploy chatflow: {chatflow_config['name']}")
            return False
    
    def deploy_all_configs(self) -> bool:
        """Deploy all chatflow configurations in the config directory."""
        print("🚀 Starting batch deployment of Flowise configurations...")
        
        if not self.check_flowise_health():
            print("❌ Flowise is not accessible. Please ensure it's running.")
            return False
        
        config_files = list(CONFIG_DIR.glob("*chatflow.json"))
        if not config_files:
            print(f"❌ No chatflow configuration files found in {CONFIG_DIR}")
            return False
        
        print(f"📁 Found {len(config_files)} configuration files")
        
        success_count = 0
        for config_file in config_files:
            if self.deploy_chatflow(config_file):
                success_count += 1
            print()  # Add spacing between deployments
        
        print(f"🎉 Deployment complete: {success_count}/{len(config_files)} chatflows deployed successfully")
        return success_count == len(config_files)
    
    def validate_config(self, config_file: Path) -> bool:
        """Validate a chatflow configuration file."""
        print(f"🔍 Validating configuration: {config_file.name}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ Invalid JSON: {e}")
            return False
        
        # Basic validation
        required_fields = ['name', 'nodes', 'edges']
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate nodes
        if not isinstance(config['nodes'], list) or len(config['nodes']) == 0:
            print("❌ Nodes must be a non-empty list")
            return False
        
        # Validate edges
        if not isinstance(config['edges'], list):
            print("❌ Edges must be a list")
            return False
        
        print("✅ Configuration is valid")
        return True

def main():
    """Main deployment function."""
    print("🌊 Flowise Configuration Deployment Tool")
    print("=" * 50)
    
    deployer = FlowiseDeployer()
    
    if len(sys.argv) > 1:
        # Deploy specific file
        config_file = Path(sys.argv[1])
        if not config_file.exists():
            print(f"❌ Configuration file not found: {config_file}")
            sys.exit(1)
        
        if deployer.validate_config(config_file):
            success = deployer.deploy_chatflow(config_file)
            sys.exit(0 if success else 1)
    else:
        # Deploy all configurations
        success = deployer.deploy_all_configs()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

# Example usage:
# python deploy_flowise_configs.py                                    # Deploy all configs
# python deploy_flowise_configs.py litellm-development-chatflow.json  # Deploy specific config
