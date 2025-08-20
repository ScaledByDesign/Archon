"""
Secure JWT Token Storage and Handling

This module provides secure storage and handling mechanisms for JWT tokens
in the Production RAG System, implementing best practices for token security.
"""

import logging
import json
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import asyncio
import aiofiles
from dataclasses import dataclass, asdict
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Token information structure"""
    token: str
    token_type: str  # 'access', 'refresh', 'id'
    expires_at: datetime
    user_id: str
    scopes: List[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


class SecureTokenStorage:
    """Secure token storage with encryption and Redis backend"""
    
    def __init__(self, encryption_key: Optional[str] = None, redis_url: Optional[str] = None):
        # Initialize encryption
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            self.encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY', '').encode()
            
        if not self.encryption_key:
            # Generate a new key if none provided (for development)
            self.encryption_key = Fernet.generate_key()
            logger.warning("No encryption key provided, generated new key (not suitable for production)")
        
        # Derive encryption key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'token_storage_salt',  # In production, use a random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key))
        self.cipher = Fernet(key)
        
        # Initialize Redis connection
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://zoi.local:6379')
        self.redis_client = None
        
        # Token storage configuration
        self.token_prefix = "jwt_token:"
        self.user_tokens_prefix = "user_tokens:"
        self.blacklist_prefix = "token_blacklist:"
        
        logger.info("Secure token storage initialized")
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            await self.redis_client.ping()
            logger.info("Connected to Redis for token storage")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    def _encrypt_token(self, token: str) -> bytes:
        """Encrypt a token"""
        return self.cipher.encrypt(token.encode())
    
    def _decrypt_token(self, encrypted_token: bytes) -> str:
        """Decrypt a token"""
        return self.cipher.decrypt(encrypted_token).decode()
    
    def _generate_token_id(self, token: str) -> str:
        """Generate a unique token ID"""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    async def store_token(self, token_info: TokenInfo) -> str:
        """
        Store a token securely
        
        Returns:
            Token ID for reference
        """
        if not self.redis_client:
            await self.connect()
        
        token_id = self._generate_token_id(token_info.token)
        
        # Encrypt the token
        encrypted_token = self._encrypt_token(token_info.token)
        
        # Prepare token data
        token_data = {
            'encrypted_token': encrypted_token,
            'token_type': token_info.token_type,
            'expires_at': token_info.expires_at.isoformat(),
            'user_id': token_info.user_id,
            'scopes': json.dumps(token_info.scopes),
            'created_at': token_info.created_at.isoformat(),
            'last_used': token_info.last_used.isoformat() if token_info.last_used else None,
            'device_id': token_info.device_id,
            'ip_address': token_info.ip_address
        }
        
        # Store in Redis with expiration
        ttl = int((token_info.expires_at - datetime.utcnow()).total_seconds())
        if ttl > 0:
            await self.redis_client.hset(f"{self.token_prefix}{token_id}", mapping=token_data)
            await self.redis_client.expire(f"{self.token_prefix}{token_id}", ttl)
            
            # Add to user's token list
            await self.redis_client.sadd(f"{self.user_tokens_prefix}{token_info.user_id}", token_id)
            
            logger.debug(f"Stored {token_info.token_type} token for user {token_info.user_id}")
            return token_id
        else:
            logger.warning("Token already expired, not storing")
            raise ValueError("Token is already expired")
    
    async def retrieve_token(self, token_id: str) -> Optional[TokenInfo]:
        """Retrieve a token by ID"""
        if not self.redis_client:
            await self.connect()
        
        token_data = await self.redis_client.hgetall(f"{self.token_prefix}{token_id}")
        
        if not token_data:
            return None
        
        # Check if token is blacklisted
        if await self.redis_client.exists(f"{self.blacklist_prefix}{token_id}"):
            logger.warning(f"Attempted to retrieve blacklisted token: {token_id}")
            return None
        
        try:
            # Decrypt token
            encrypted_token = token_data[b'encrypted_token']
            decrypted_token = self._decrypt_token(encrypted_token)
            
            # Parse token data
            token_info = TokenInfo(
                token=decrypted_token,
                token_type=token_data[b'token_type'].decode(),
                expires_at=datetime.fromisoformat(token_data[b'expires_at'].decode()),
                user_id=token_data[b'user_id'].decode(),
                scopes=json.loads(token_data[b'scopes'].decode()),
                created_at=datetime.fromisoformat(token_data[b'created_at'].decode()),
                last_used=datetime.fromisoformat(token_data[b'last_used'].decode()) if token_data[b'last_used'] else None,
                device_id=token_data[b'device_id'].decode() if token_data[b'device_id'] else None,
                ip_address=token_data[b'ip_address'].decode() if token_data[b'ip_address'] else None
            )
            
            # Check if token is expired
            if token_info.expires_at <= datetime.utcnow():
                await self.revoke_token(token_id)
                return None
            
            # Update last used timestamp
            await self.update_last_used(token_id)
            
            return token_info
            
        except Exception as e:
            logger.error(f"Failed to retrieve token {token_id}: {e}")
            return None
    
    async def update_last_used(self, token_id: str):
        """Update the last used timestamp for a token"""
        if not self.redis_client:
            await self.connect()
        
        await self.redis_client.hset(
            f"{self.token_prefix}{token_id}",
            'last_used',
            datetime.utcnow().isoformat()
        )
    
    async def revoke_token(self, token_id: str):
        """Revoke a token (add to blacklist)"""
        if not self.redis_client:
            await self.connect()
        
        # Get token info to find user
        token_data = await self.redis_client.hgetall(f"{self.token_prefix}{token_id}")
        
        if token_data:
            user_id = token_data[b'user_id'].decode()
            
            # Add to blacklist
            await self.redis_client.setex(
                f"{self.blacklist_prefix}{token_id}",
                86400,  # Keep blacklist entry for 24 hours
                "revoked"
            )
            
            # Remove from user's token list
            await self.redis_client.srem(f"{self.user_tokens_prefix}{user_id}", token_id)
            
            # Delete the token
            await self.redis_client.delete(f"{self.token_prefix}{token_id}")
            
            logger.info(f"Revoked token {token_id} for user {user_id}")
    
    async def revoke_user_tokens(self, user_id: str, token_type: Optional[str] = None):
        """Revoke all tokens for a user"""
        if not self.redis_client:
            await self.connect()
        
        # Get all user tokens
        token_ids = await self.redis_client.smembers(f"{self.user_tokens_prefix}{user_id}")
        
        revoked_count = 0
        for token_id in token_ids:
            token_id = token_id.decode()
            
            if token_type:
                # Check token type if specified
                token_data = await self.redis_client.hgetall(f"{self.token_prefix}{token_id}")
                if token_data and token_data[b'token_type'].decode() != token_type:
                    continue
            
            await self.revoke_token(token_id)
            revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
        return revoked_count
    
    async def get_user_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active tokens for a user"""
        if not self.redis_client:
            await self.connect()
        
        token_ids = await self.redis_client.smembers(f"{self.user_tokens_prefix}{user_id}")
        tokens = []
        
        for token_id in token_ids:
            token_id = token_id.decode()
            token_data = await self.redis_client.hgetall(f"{self.token_prefix}{token_id}")
            
            if token_data:
                # Don't include the actual token, just metadata
                token_info = {
                    'token_id': token_id,
                    'token_type': token_data[b'token_type'].decode(),
                    'expires_at': token_data[b'expires_at'].decode(),
                    'created_at': token_data[b'created_at'].decode(),
                    'last_used': token_data[b'last_used'].decode() if token_data[b'last_used'] else None,
                    'device_id': token_data[b'device_id'].decode() if token_data[b'device_id'] else None,
                    'ip_address': token_data[b'ip_address'].decode() if token_data[b'ip_address'] else None
                }
                tokens.append(token_info)
        
        return tokens
    
    async def cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        if not self.redis_client:
            await self.connect()
        
        # This is handled automatically by Redis TTL, but we can also do manual cleanup
        # for tokens that might have been missed
        
        pattern = f"{self.token_prefix}*"
        async for key in self.redis_client.scan_iter(match=pattern):
            key = key.decode()
            token_data = await self.redis_client.hgetall(key)
            
            if token_data:
                expires_at = datetime.fromisoformat(token_data[b'expires_at'].decode())
                if expires_at <= datetime.utcnow():
                    token_id = key.replace(self.token_prefix, '')
                    await self.revoke_token(token_id)
        
        logger.info("Completed expired token cleanup")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if not self.redis_client:
            await self.connect()
        
        # Count tokens by type
        token_count = 0
        access_tokens = 0
        refresh_tokens = 0
        id_tokens = 0
        
        pattern = f"{self.token_prefix}*"
        async for key in self.redis_client.scan_iter(match=pattern):
            token_count += 1
            token_data = await self.redis_client.hgetall(key)
            
            if token_data:
                token_type = token_data[b'token_type'].decode()
                if token_type == 'access':
                    access_tokens += 1
                elif token_type == 'refresh':
                    refresh_tokens += 1
                elif token_type == 'id':
                    id_tokens += 1
        
        # Count blacklisted tokens
        blacklist_pattern = f"{self.blacklist_prefix}*"
        blacklisted_count = 0
        async for key in self.redis_client.scan_iter(match=blacklist_pattern):
            blacklisted_count += 1
        
        return {
            'total_tokens': token_count,
            'access_tokens': access_tokens,
            'refresh_tokens': refresh_tokens,
            'id_tokens': id_tokens,
            'blacklisted_tokens': blacklisted_count,
            'timestamp': datetime.utcnow().isoformat()
        }


class TokenManager:
    """High-level token management interface"""
    
    def __init__(self, storage: SecureTokenStorage):
        self.storage = storage
        
        # Token limits
        self.max_tokens_per_user = int(os.getenv('MAX_TOKENS_PER_USER', '10'))
        self.max_concurrent_sessions = int(os.getenv('MAX_CONCURRENT_SESSIONS', '5'))
    
    async def store_user_tokens(self, user_id: str, access_token: str, refresh_token: str, 
                               id_token: str, scopes: List[str], device_id: Optional[str] = None,
                               ip_address: Optional[str] = None) -> Dict[str, str]:
        """Store a complete set of user tokens"""
        
        # Check token limits
        existing_tokens = await self.storage.get_user_tokens(user_id)
        if len(existing_tokens) >= self.max_tokens_per_user:
            # Remove oldest tokens
            oldest_tokens = sorted(existing_tokens, key=lambda x: x['created_at'])[:len(existing_tokens) - self.max_tokens_per_user + 3]
            for token in oldest_tokens:
                await self.storage.revoke_token(token['token_id'])
        
        now = datetime.utcnow()
        
        # Store access token
        access_token_info = TokenInfo(
            token=access_token,
            token_type='access',
            expires_at=now + timedelta(seconds=3600),  # 1 hour
            user_id=user_id,
            scopes=scopes,
            created_at=now,
            device_id=device_id,
            ip_address=ip_address
        )
        access_token_id = await self.storage.store_token(access_token_info)
        
        # Store refresh token
        refresh_token_info = TokenInfo(
            token=refresh_token,
            token_type='refresh',
            expires_at=now + timedelta(seconds=86400),  # 24 hours
            user_id=user_id,
            scopes=scopes,
            created_at=now,
            device_id=device_id,
            ip_address=ip_address
        )
        refresh_token_id = await self.storage.store_token(refresh_token_info)
        
        # Store ID token
        id_token_info = TokenInfo(
            token=id_token,
            token_type='id',
            expires_at=now + timedelta(seconds=3600),  # 1 hour
            user_id=user_id,
            scopes=scopes,
            created_at=now,
            device_id=device_id,
            ip_address=ip_address
        )
        id_token_id = await self.storage.store_token(id_token_info)
        
        logger.info(f"Stored token set for user {user_id}")
        
        return {
            'access_token_id': access_token_id,
            'refresh_token_id': refresh_token_id,
            'id_token_id': id_token_id
        }
    
    async def logout_user(self, user_id: str, device_id: Optional[str] = None):
        """Logout user (revoke tokens)"""
        if device_id:
            # Revoke tokens for specific device
            user_tokens = await self.storage.get_user_tokens(user_id)
            for token in user_tokens:
                if token.get('device_id') == device_id:
                    await self.storage.revoke_token(token['token_id'])
        else:
            # Revoke all tokens
            await self.storage.revoke_user_tokens(user_id)
        
        logger.info(f"Logged out user {user_id}" + (f" from device {device_id}" if device_id else " from all devices"))
    
    async def refresh_tokens(self, refresh_token_id: str) -> Optional[Dict[str, str]]:
        """Refresh user tokens"""
        refresh_token_info = await self.storage.retrieve_token(refresh_token_id)
        
        if not refresh_token_info or refresh_token_info.token_type != 'refresh':
            return None
        
        # Revoke old tokens
        await self.storage.revoke_user_tokens(refresh_token_info.user_id, 'access')
        await self.storage.revoke_user_tokens(refresh_token_info.user_id, 'id')
        
        # Note: In a real implementation, you would call Authentik to refresh the tokens
        # For now, this is a placeholder
        logger.info(f"Token refresh requested for user {refresh_token_info.user_id}")
        
        return None  # Placeholder


# Global token manager instance
_token_storage = None
_token_manager = None


async def get_token_storage() -> SecureTokenStorage:
    """Get global token storage instance"""
    global _token_storage
    if _token_storage is None:
        _token_storage = SecureTokenStorage()
        await _token_storage.connect()
    return _token_storage


async def get_token_manager() -> TokenManager:
    """Get global token manager instance"""
    global _token_manager
    if _token_manager is None:
        storage = await get_token_storage()
        _token_manager = TokenManager(storage)
    return _token_manager


async def cleanup_token_storage():
    """Cleanup token storage resources"""
    global _token_storage, _token_manager
    if _token_storage:
        await _token_storage.disconnect()
        _token_storage = None
    _token_manager = None
