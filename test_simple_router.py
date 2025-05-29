#!/usr/bin/env python3
"""
Simple test for model router imports and basic functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, '/app/src')

def test_imports():
    """Test basic imports"""
    print("🧪 Testing Model Router Imports")
    print("=" * 40)
    
    try:
        from services.model_router import ModelRouter, RouteStrategy, TaskComplexity, ModelCapability
        print("✅ ModelRouter imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_router_creation():
    """Test router creation"""
    print("\n🔧 Testing Router Creation")
    print("=" * 30)
    
    try:
        from services.model_router import ModelRouter
        
        router = ModelRouter(
            litellm_base_url="http://litellm:4000",
            api_key="sk-change-me-to-random-string"
        )
        print("✅ Router created successfully")
        print(f"   LiteLLM URL: {router.litellm_base_url}")
        print(f"   Model groups: {len(router.model_groups)}")
        print(f"   Routing rules: {len(router.routing_rules)}")
        return True
    except Exception as e:
        print(f"❌ Router creation failed: {e}")
        return False

def test_vault_basic():
    """Test basic Vault client"""
    print("\n🔐 Testing Vault Client")
    print("=" * 25)
    
    try:
        from secrets.vault_client import VaultClient
        print("✅ VaultClient imported successfully")
        
        # Check environment variables
        vault_addr = os.getenv('VAULT_ADDR', 'Not set')
        vault_token = os.getenv('VAULT_ROOT_TOKEN', 'Not set')
        print(f"   VAULT_ADDR: {vault_addr}")
        print(f"   VAULT_TOKEN: {'***' if vault_token != 'Not set' else 'Not set'}")
        
        return True
    except Exception as e:
        print(f"❌ Vault import failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Simple Model Router Tests")
    print("=" * 35)
    
    # Test imports
    import_success = test_imports()
    
    # Test router creation
    router_success = test_router_creation() if import_success else False
    
    # Test vault
    vault_success = test_vault_basic()
    
    # Summary
    print("\n" + "=" * 35)
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"   Router: {'✅ PASS' if router_success else '❌ FAIL'}")
    print(f"   Vault: {'✅ PASS' if vault_success else '❌ FAIL'}")
    
    overall = import_success and router_success and vault_success
    print(f"   Overall: {'✅ ALL PASS' if overall else '❌ SOME FAILED'}")
    
    return overall

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
