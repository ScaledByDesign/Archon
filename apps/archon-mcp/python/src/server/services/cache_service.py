"""
Redis Cache Service for Archon MCP System

This module provides a centralized caching layer for all archon services
to reduce database load and improve response times.
"""

import json
import os
import hashlib
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Centralized Redis cache service for Archon MCP system.
    Uses Redis DB 10 for archon-specific caching.
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize cache service with optional Redis client."""
        self._redis_client = redis_client
        self._connected = False
        
        # Cache configuration
        self.db_number = 10  # Dedicated DB for archon-mcp caching
        self.default_ttl = 300  # 5 minutes default TTL
        self.key_prefix = "archon:"
        
        # Cache TTL settings for different data types
        self.ttl_settings = {
            "projects": 300,      # 5 minutes - projects change frequently
            "project_sources": 600,  # 10 minutes - source links change less often
            "sources": 1800,      # 30 minutes - source metadata is more stable
            "health": 60,         # 1 minute - health checks need fresh data
            "mcp_tools": 3600,    # 1 hour - tool definitions are stable
            "credentials": 900,   # 15 minutes - credentials may change
        }
    
    async def connect(self) -> bool:
        """
        Connect to Redis server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self._connected and self._redis_client:
            return True
            
        try:
            # Get Redis connection details from environment
            redis_host = os.getenv("REDIS_HOST", "redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_password = os.getenv("REDIS_PASSWORD")
            
            # Create Redis client
            if redis_password:
                redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{self.db_number}"
            else:
                redis_url = f"redis://{redis_host}:{redis_port}/{self.db_number}"
            
            self._redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._redis_client.ping()
            self._connected = True
            
            logger.info(f"Redis cache service connected - DB {self.db_number}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis cache: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis_client:
            await self._redis_client.close()
            self._connected = False
            logger.info("Redis cache service disconnected")
    
    def _make_key(self, category: str, identifier: str) -> str:
        """
        Create a cache key with consistent formatting.
        
        Args:
            category: Data category (e.g., 'projects', 'sources')
            identifier: Unique identifier for the data
            
        Returns:
            Formatted cache key
        """
        return f"{self.key_prefix}{category}:{identifier}"
    
    def _hash_key(self, data: Union[str, Dict, List]) -> str:
        """
        Create a hash from data for use as cache key.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA256 hash string
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    async def get(self, category: str, identifier: str) -> Optional[Any]:
        """
        Get cached data.
        
        Args:
            category: Data category
            identifier: Data identifier
            
        Returns:
            Cached data or None if not found/expired
        """
        if not self._connected:
            if not await self.connect():
                return None
        
        try:
            key = self._make_key(category, identifier)
            cached_data = await self._redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache hit: {key}")
                return data
            else:
                logger.debug(f"Cache miss: {key}")
                return None
                
        except Exception as e:
            logger.warning(f"Cache get error for {category}:{identifier}: {e}")
            return None
    
    async def set(
        self, 
        category: str, 
        identifier: str, 
        data: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached data with TTL.
        
        Args:
            category: Data category
            identifier: Data identifier
            data: Data to cache
            ttl: Time to live in seconds (uses category default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            if not await self.connect():
                return False
        
        try:
            key = self._make_key(category, identifier)
            
            # Use category-specific TTL or provided TTL
            if ttl is None:
                ttl = self.ttl_settings.get(category, self.default_ttl)
            
            # Serialize data
            serialized_data = json.dumps(data, default=str)
            
            # Set with TTL
            await self._redis_client.setex(key, ttl, serialized_data)
            
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.warning(f"Cache set error for {category}:{identifier}: {e}")
            return False
    
    async def delete(self, category: str, identifier: str) -> bool:
        """
        Delete cached data.
        
        Args:
            category: Data category
            identifier: Data identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            if not await self.connect():
                return False
        
        try:
            key = self._make_key(category, identifier)
            result = await self._redis_client.delete(key)
            
            logger.debug(f"Cache delete: {key} (existed: {bool(result)})")
            return True
            
        except Exception as e:
            logger.warning(f"Cache delete error for {category}:{identifier}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., 'archon:projects:*')
            
        Returns:
            Number of keys deleted
        """
        if not self._connected:
            if not await self.connect():
                return 0
        
        try:
            keys = await self._redis_client.keys(pattern)
            if keys:
                deleted = await self._redis_client.delete(*keys)
                logger.info(f"Cache invalidated: {deleted} keys matching '{pattern}'")
                return deleted
            return 0
            
        except Exception as e:
            logger.warning(f"Cache invalidation error for pattern '{pattern}': {e}")
            return 0
    
    async def invalidate_category(self, category: str) -> int:
        """
        Invalidate all cached data for a category.
        
        Args:
            category: Data category to invalidate
            
        Returns:
            Number of keys deleted
        """
        pattern = f"{self.key_prefix}{category}:*"
        return await self.invalidate_pattern(pattern)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self._connected:
            if not await self.connect():
                return {"connected": False}
        
        try:
            info = await self._redis_client.info()
            
            return {
                "connected": True,
                "db_number": self.db_number,
                "keys": info.get("db10", {}).get("keys", 0) if "db10" in info else 0,
                "memory_used": info.get("used_memory_human", "0B"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
            
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """
    Get the global cache service instance.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()
    
    return _cache_service


async def cleanup_cache_service():
    """Cleanup the global cache service instance."""
    global _cache_service
    
    if _cache_service:
        await _cache_service.disconnect()
        _cache_service = None
