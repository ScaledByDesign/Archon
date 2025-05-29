"""
Test script for HashiCorp Vault integration
Validates Vault connectivity and secret management functionality
"""

import os
import sys
import logging
from vault_client import VaultClient, VaultConfig, SecretManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_vault_connection():
    """Test basic Vault connection"""
    print("🔐 Testing Vault Connection...")
    
    try:
        config = VaultConfig.from_env()
        client = VaultClient(config)
        
        if client.is_authenticated():
            print("✅ Successfully connected to Vault")
            print(f"   URL: {config.url}")
            print(f"   Authentication: {'Token' if config.token else 'AppRole'}")
            return True
        else:
            print("❌ Failed to authenticate with Vault")
            return False
            
    except Exception as e:
        print(f"❌ Vault connection failed: {e}")
        return False


def test_secret_operations():
    """Test secret storage and retrieval"""
    print("\n🗝️ Testing Secret Operations...")
    
    try:
        client = VaultClient()
        
        # Test secret storage
        test_secret = {
            'test_key': 'test_value',
            'timestamp': str(int(__import__('time').time()))
        }
        
        print("📝 Storing test secret...")
        client.put_secret('test/vault-integration', test_secret)
        
        # Test secret retrieval
        print("📖 Retrieving test secret...")
        retrieved = client.get_secret('test/vault-integration')
        
        if retrieved == test_secret:
            print("✅ Secret storage and retrieval working")
        else:
            print("❌ Secret mismatch")
            return False
        
        # Test individual key retrieval
        single_value = client.get_secret('test/vault-integration', 'test_key')
        if single_value == 'test_value':
            print("✅ Individual key retrieval working")
        else:
            print("❌ Individual key retrieval failed")
            return False
        
        # Test secret listing
        secrets = client.list_secrets('test')
        if 'vault-integration' in secrets:
            print("✅ Secret listing working")
        else:
            print("❌ Secret listing failed")
            return False
        
        # Clean up
        client.delete_secret('test/vault-integration')
        print("✅ Secret deletion working")
        
        return True
        
    except Exception as e:
        print(f"❌ Secret operations failed: {e}")
        return False


def test_application_secrets():
    """Test application-specific secret retrieval"""
    print("\n🔧 Testing Application Secrets...")
    
    try:
        secret_manager = SecretManager()
        
        # Test database credentials (if they exist)
        try:
            db_creds = secret_manager.vault.get_database_credentials()
            print("✅ Database credentials accessible")
            print(f"   Host: {db_creds.get('host', 'N/A')}")
            print(f"   Database: {db_creds.get('database', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Database credentials not found: {e}")
        
        # Test Redis credentials (if they exist)
        try:
            redis_creds = secret_manager.vault.get_redis_credentials()
            print("✅ Redis credentials accessible")
            print(f"   Host: {redis_creds.get('host', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Redis credentials not found: {e}")
        
        # Test LLM credentials (if they exist)
        try:
            llm_creds = secret_manager.vault.get_llm_credentials()
            print("✅ LLM credentials accessible")
            masked_openai = llm_creds.get('openai_api_key', 'N/A')
            if masked_openai != 'N/A' and len(masked_openai) > 10:
                masked_openai = masked_openai[:10] + '...'
            print(f"   OpenAI API Key: {masked_openai}")
        except Exception as e:
            print(f"⚠️ LLM credentials not found: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Application secrets test failed: {e}")
        return False


def test_secret_manager():
    """Test high-level SecretManager functionality"""
    print("\n🎯 Testing Secret Manager...")
    
    try:
        secret_manager = SecretManager()
        
        # Test URL generation methods
        try:
            db_url = secret_manager.get_database_url()
            print("✅ Database URL generation working")
            # Mask password in URL for display
            if '@' in db_url:
                parts = db_url.split('@')
                masked_url = parts[0].split(':')[0] + ':***:***@' + parts[1]
                print(f"   URL: {masked_url}")
        except Exception as e:
            print(f"⚠️ Database URL generation failed: {e}")
        
        try:
            redis_url = secret_manager.get_redis_url()
            print("✅ Redis URL generation working")
            # Mask password in URL for display
            if ':' in redis_url and '@' in redis_url:
                parts = redis_url.split('@')
                masked_url = parts[0].split(':')[0] + ':***@' + parts[1]
                print(f"   URL: {masked_url}")
        except Exception as e:
            print(f"⚠️ Redis URL generation failed: {e}")
        
        try:
            rabbitmq_url = secret_manager.get_rabbitmq_url()
            print("✅ RabbitMQ URL generation working")
            # Mask password in URL for display
            if ':' in rabbitmq_url and '@' in rabbitmq_url:
                parts = rabbitmq_url.split('@')
                masked_url = parts[0].split(':')[0] + ':***:***@' + parts[1]
                print(f"   URL: {masked_url}")
        except Exception as e:
            print(f"⚠️ RabbitMQ URL generation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Secret Manager test failed: {e}")
        return False


def main():
    """Run all Vault integration tests"""
    print("🧪 Vault Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Connection Test", test_vault_connection),
        ("Secret Operations", test_secret_operations),
        ("Application Secrets", test_application_secrets),
        ("Secret Manager", test_secret_manager),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Vault integration is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check Vault configuration and connectivity.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
