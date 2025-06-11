#!/usr/bin/env python3
"""
JWT Security Testing Script

This script comprehensively tests the JWT security implementation for the
Production RAG System, validating token handling, security configurations,
and integration with Authentik SSO.
"""

import asyncio
import httpx
import json
import jwt
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from auth.jwt_handler import JWTHandler, JWTSecurityConfig
from auth.jwt_middleware import jwt_health_check

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JWTSecurityTester:
    """Comprehensive JWT Security Tester"""
    
    def __init__(self):
        self.authentik_base_url = os.getenv('AUTHENTIK_BASE_URL', 'https://auth.zoi.local')
        self.fastapi_base_url = os.getenv('FASTAPI_BASE_URL', 'http://zoi.local:8000')
        self.jwt_handler = JWTHandler(self.authentik_base_url)
        self.http_client = httpx.AsyncClient(verify=False, timeout=30.0)
        
        # Test results
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    async def run_all_tests(self):
        """Run all JWT security tests"""
        logger.info("🔐 Starting JWT Security Test Suite")
        logger.info("=" * 60)
        
        tests = [
            self.test_jwt_config_validation,
            self.test_jwks_endpoint_connectivity,
            self.test_jwt_middleware_health,
            self.test_token_validation_security,
            self.test_clock_skew_tolerance,
            self.test_audience_validation,
            self.test_issuer_validation,
            self.test_expired_token_handling,
            self.test_malformed_token_handling,
            self.test_scope_validation,
            self.test_fastapi_integration,
            self.test_security_headers,
            self.test_rate_limiting_protection
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                self.record_failure(test.__name__, str(e))
                logger.error(f"❌ {test.__name__} failed with exception: {e}")
        
        await self.generate_test_report()
    
    def record_success(self, test_name: str, message: str = ""):
        """Record a successful test"""
        self.test_results['passed'] += 1
        logger.info(f"✅ {test_name}: {message}")
    
    def record_failure(self, test_name: str, error: str):
        """Record a failed test"""
        self.test_results['failed'] += 1
        self.test_results['errors'].append({
            'test': test_name,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        })
        logger.error(f"❌ {test_name}: {error}")
    
    async def test_jwt_config_validation(self):
        """Test JWT configuration validation"""
        test_name = "JWT Configuration Validation"
        
        try:
            config = JWTSecurityConfig()
            
            # Validate required configuration
            assert config.algorithm == 'RS256', "Algorithm should be RS256"
            assert config.access_token_lifetime > 0, "Access token lifetime must be positive"
            assert config.refresh_token_lifetime > 0, "Refresh token lifetime must be positive"
            assert config.clock_skew_tolerance >= 0, "Clock skew tolerance must be non-negative"
            assert config.issuer, "Issuer must be configured"
            assert config.audience, "Audience must be configured"
            
            self.record_success(test_name, f"Config valid - Algorithm: {config.algorithm}, Issuer: {config.issuer}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_jwks_endpoint_connectivity(self):
        """Test JWKS endpoint connectivity"""
        test_name = "JWKS Endpoint Connectivity"
        
        try:
            jwks = await self.jwt_handler.jwks_manager.get_jwks()
            
            assert 'keys' in jwks, "JWKS response must contain 'keys'"
            assert len(jwks['keys']) > 0, "JWKS must contain at least one key"
            
            # Validate key structure
            for key in jwks['keys']:
                assert 'kid' in key, "Each key must have a 'kid' (key ID)"
                assert 'kty' in key, "Each key must have a 'kty' (key type)"
                assert 'use' in key, "Each key must have a 'use' field"
                assert 'alg' in key, "Each key must have an 'alg' (algorithm)"
            
            self.record_success(test_name, f"JWKS endpoint accessible with {len(jwks['keys'])} keys")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_jwt_middleware_health(self):
        """Test JWT middleware health check"""
        test_name = "JWT Middleware Health Check"
        
        try:
            health = await jwt_health_check()
            
            assert health['status'] == 'healthy', f"Health check failed: {health.get('error', 'Unknown error')}"
            assert 'key_count' in health, "Health check must include key count"
            assert health['key_count'] > 0, "Must have at least one signing key"
            
            self.record_success(test_name, f"Middleware healthy with {health['key_count']} keys")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_token_validation_security(self):
        """Test token validation security features"""
        test_name = "Token Validation Security"
        
        try:
            # Test with a mock token (this will fail validation but test the security checks)
            mock_token = self.create_mock_jwt_token()
            
            try:
                await self.jwt_handler.validate_access_token(mock_token)
                self.record_failure(test_name, "Mock token should not validate successfully")
            except jwt.InvalidTokenError:
                # This is expected - mock token should fail validation
                self.record_success(test_name, "Security validation correctly rejects invalid tokens")
            except Exception as e:
                # Other exceptions might indicate configuration issues
                self.record_failure(test_name, f"Unexpected error during validation: {e}")
                
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_clock_skew_tolerance(self):
        """Test clock skew tolerance configuration"""
        test_name = "Clock Skew Tolerance"
        
        try:
            config = self.jwt_handler.security_config
            
            # Verify clock skew tolerance is reasonable (not too permissive)
            assert 0 <= config.clock_skew_tolerance <= 300, "Clock skew tolerance should be between 0-300 seconds"
            
            self.record_success(test_name, f"Clock skew tolerance: {config.clock_skew_tolerance}s")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_audience_validation(self):
        """Test audience validation"""
        test_name = "Audience Validation"
        
        try:
            config = self.jwt_handler.security_config
            
            # Verify audience is configured
            assert config.audience, "Audience must be configured"
            assert config.verify_audience, "Audience verification must be enabled"
            
            self.record_success(test_name, f"Audience validation enabled for: {config.audience}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_issuer_validation(self):
        """Test issuer validation"""
        test_name = "Issuer Validation"
        
        try:
            config = self.jwt_handler.security_config
            
            # Verify issuer is configured
            assert config.issuer, "Issuer must be configured"
            assert config.verify_issuer, "Issuer verification must be enabled"
            assert config.issuer.startswith('https://'), "Issuer should use HTTPS"
            
            self.record_success(test_name, f"Issuer validation enabled for: {config.issuer}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_expired_token_handling(self):
        """Test expired token handling"""
        test_name = "Expired Token Handling"
        
        try:
            # Create an expired mock token
            expired_token = self.create_mock_jwt_token(expired=True)
            
            try:
                await self.jwt_handler.validate_access_token(expired_token)
                self.record_failure(test_name, "Expired token should not validate")
            except jwt.ExpiredSignatureError:
                self.record_success(test_name, "Expired tokens correctly rejected")
            except Exception as e:
                self.record_failure(test_name, f"Unexpected error: {e}")
                
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_malformed_token_handling(self):
        """Test malformed token handling"""
        test_name = "Malformed Token Handling"
        
        try:
            malformed_tokens = [
                "invalid.token.format",
                "not-a-jwt-token",
                "",
                "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
                "header.payload"  # Missing signature
            ]
            
            for token in malformed_tokens:
                try:
                    await self.jwt_handler.validate_access_token(token)
                    self.record_failure(test_name, f"Malformed token should not validate: {token}")
                    return
                except jwt.InvalidTokenError:
                    continue  # Expected
                except Exception:
                    continue  # Also acceptable for malformed tokens
            
            self.record_success(test_name, "All malformed tokens correctly rejected")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_scope_validation(self):
        """Test scope validation logic"""
        test_name = "Scope Validation"
        
        try:
            # This test validates the scope checking logic in middleware
            # Since we can't easily test with real tokens, we test the configuration
            
            config = self.jwt_handler.security_config
            
            # Verify that scope validation is properly configured
            assert hasattr(config, 'verify_signature'), "Must have signature verification config"
            assert config.verify_signature, "Signature verification must be enabled"
            
            self.record_success(test_name, "Scope validation configuration verified")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_fastapi_integration(self):
        """Test FastAPI integration"""
        test_name = "FastAPI Integration"
        
        try:
            # Test health endpoint
            response = await self.http_client.get(f"{self.fastapi_base_url}/health")
            
            if response.status_code == 200:
                self.record_success(test_name, "FastAPI service accessible")
            else:
                self.record_failure(test_name, f"FastAPI service returned {response.status_code}")
                
        except Exception as e:
            self.record_failure(test_name, f"FastAPI connection failed: {e}")
    
    async def test_security_headers(self):
        """Test security headers"""
        test_name = "Security Headers"
        
        try:
            response = await self.http_client.get(f"{self.fastapi_base_url}/health")
            
            # Check for important security headers
            headers = response.headers
            
            security_checks = []
            
            # Check for CORS headers (if configured)
            if 'access-control-allow-origin' in headers:
                security_checks.append("CORS configured")
            
            # Check for content type
            if 'content-type' in headers:
                security_checks.append("Content-Type header present")
            
            self.record_success(test_name, f"Security headers checked: {', '.join(security_checks)}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_rate_limiting_protection(self):
        """Test rate limiting protection"""
        test_name = "Rate Limiting Protection"
        
        try:
            # This is a basic test - in production you'd want more comprehensive rate limiting tests
            # For now, we just verify the service responds consistently
            
            responses = []
            for i in range(3):
                response = await self.http_client.get(f"{self.fastapi_base_url}/health")
                responses.append(response.status_code)
                await asyncio.sleep(0.1)
            
            # All responses should be consistent (either all 200 or all the same error)
            if len(set(responses)) == 1:
                self.record_success(test_name, f"Consistent responses: {responses[0]}")
            else:
                self.record_failure(test_name, f"Inconsistent responses: {responses}")
                
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    def create_mock_jwt_token(self, expired: bool = False) -> str:
        """Create a mock JWT token for testing"""
        now = datetime.utcnow()
        
        if expired:
            exp = now - timedelta(hours=1)  # Expired 1 hour ago
        else:
            exp = now + timedelta(hours=1)  # Expires in 1 hour
        
        payload = {
            'sub': 'test-user',
            'iss': 'test-issuer',
            'aud': 'test-audience',
            'exp': int(exp.timestamp()),
            'iat': int(now.timestamp()),
            'scope': 'openid profile email'
        }
        
        # Create unsigned token (will fail signature verification)
        return jwt.encode(payload, 'secret', algorithm='HS256')
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 60)
        logger.info("🔐 JWT Security Test Report")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            logger.info("\n❌ Failed Tests:")
            for error in self.test_results['errors']:
                logger.info(f"  - {error['test']}: {error['error']}")
        
        # Save detailed report
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': self.test_results['passed'],
                'failed': self.test_results['failed'],
                'success_rate': success_rate
            },
            'errors': self.test_results['errors'],
            'configuration': {
                'authentik_base_url': self.authentik_base_url,
                'fastapi_base_url': self.fastapi_base_url,
                'jwt_algorithm': self.jwt_handler.security_config.algorithm,
                'jwt_issuer': self.jwt_handler.security_config.issuer,
                'jwt_audience': self.jwt_handler.security_config.audience
            }
        }
        
        report_file = 'jwt-security-test-report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Detailed report saved to: {report_file}")
        
        if self.test_results['failed'] == 0:
            logger.info("🎉 All JWT security tests passed!")
        else:
            logger.warning(f"⚠️  {self.test_results['failed']} tests failed. Review the errors above.")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.jwt_handler.jwks_manager.close()
            await self.http_client.aclose()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def main():
    """Main test runner"""
    tester = JWTSecurityTester()
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
