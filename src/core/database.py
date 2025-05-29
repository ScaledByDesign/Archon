"""
Database utilities and connection management for the FastAPI backend
Provides database connections, session management, and query helpers
"""

import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from contextlib import asynccontextmanager
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import asyncpg

from src.config.settings import get_settings
from src.core.exceptions import DatabaseError, ConnectionError


logger = logging.getLogger(__name__)
settings = get_settings()

# SQLAlchemy Base for ORM models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self._mongo_client: Optional[AsyncIOMotorClient] = None
        self._redis_client: Optional[redis.Redis] = None
        self._postgres_engine = None
        self._postgres_session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize all database connections"""
        if self._initialized:
            return
        
        try:
            await self._init_mongodb()
            await self._init_redis()
            await self._init_postgres()
            self._initialized = True
            logger.info("Database connections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            # Use the MongoDB URL property from settings
            episodic_uri = settings.database.mongodb_url
            
            self._mongo_client = AsyncIOMotorClient(episodic_uri)
            
            # Test connection
            await self._mongo_client.admin.command('ping')
            logger.info("MongoDB connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"MongoDB connection failed: {e}")
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self._redis_client = redis.Redis(
                host=settings.database.redis_host,
                port=settings.database.redis_port,
                password=settings.database.redis_password,
                db=settings.database.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._redis_client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            # PostgreSQL connection string
            postgres_uri = (
                f"postgresql+asyncpg://{settings.database.postgres_username}:"
                f"{settings.database.postgres_password}@"
                f"{settings.database.postgres_host}:"
                f"{settings.database.postgres_port}/"
                f"{settings.database.postgres_database}"
            )
            
            self._postgres_engine = create_async_engine(
                postgres_uri,
                echo=False,  # Default to False since echo_sql is not in DatabaseSettings
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            self._postgres_session_factory = async_sessionmaker(
                self._postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self._postgres_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.info("PostgreSQL connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionError(f"PostgreSQL connection failed: {e}")
    
    async def close(self):
        """Close all database connections"""
        try:
            if self._mongo_client:
                self._mongo_client.close()
                logger.info("MongoDB connection closed")
            
            if self._redis_client:
                await self._redis_client.close()
                logger.info("Redis connection closed")
            
            if self._postgres_engine:
                await self._postgres_engine.dispose()
                logger.info("PostgreSQL connection closed")
            
            self._initialized = False
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    @property
    def mongo(self) -> AsyncIOMotorClient:
        """Get MongoDB client"""
        if not self._mongo_client:
            raise DatabaseError("MongoDB client not initialized")
        return self._mongo_client
    
    @property
    def redis(self) -> redis.Redis:
        """Get Redis client"""
        if not self._redis_client:
            raise DatabaseError("Redis client not initialized")
        return self._redis_client
    
    @asynccontextmanager
    async def postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get PostgreSQL session context manager"""
        if not self._postgres_session_factory:
            raise DatabaseError("PostgreSQL session factory not initialized")
        
        async with self._postgres_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_mongo_database(self, database_name: str) -> AsyncIOMotorDatabase:
        """Get MongoDB database instance"""
        return self.mongo[database_name]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all database connections"""
        health = {
            "mongodb": {"status": "unknown", "error": None},
            "redis": {"status": "unknown", "error": None},
            "postgresql": {"status": "unknown", "error": None}
        }
        
        # Check MongoDB
        try:
            if self._mongo_client:
                await self._mongo_client.admin.command('ping')
                health["mongodb"]["status"] = "healthy"
            else:
                health["mongodb"]["status"] = "not_initialized"
        except Exception as e:
            health["mongodb"]["status"] = "unhealthy"
            health["mongodb"]["error"] = str(e)
        
        # Check Redis
        try:
            if self._redis_client:
                await self._redis_client.ping()
                health["redis"]["status"] = "healthy"
            else:
                health["redis"]["status"] = "not_initialized"
        except Exception as e:
            health["redis"]["status"] = "unhealthy"
            health["redis"]["error"] = str(e)
        
        # Check PostgreSQL
        try:
            if self._postgres_engine:
                async with self._postgres_engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                health["postgresql"]["status"] = "healthy"
            else:
                health["postgresql"]["status"] = "not_initialized"
        except Exception as e:
            health["postgresql"]["status"] = "unhealthy"
            health["postgresql"]["error"] = str(e)
        
        return health


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    if not db_manager._initialized:
        await db_manager.initialize()
    return db_manager


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get MongoDB client"""
    manager = await get_database_manager()
    return manager.mongo


async def get_redis_client() -> redis.Redis:
    """Get Redis client"""
    manager = await get_database_manager()
    return manager.redis


async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """Get PostgreSQL session"""
    manager = await get_database_manager()
    async with manager.postgres_session() as session:
        yield session


class MongoHelper:
    """Helper class for MongoDB operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
    
    async def create_collection_if_not_exists(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        """Create collection if it doesn't exist"""
        try:
            collections = await self.db.list_collection_names()
            if collection_name not in collections:
                await self.db.create_collection(collection_name, **kwargs)
                logger.info(f"Created MongoDB collection: {collection_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise DatabaseError(f"Collection creation failed: {e}")
    
    async def create_index(
        self,
        collection_name: str,
        index_spec: List[tuple],
        **kwargs
    ):
        """Create index on collection"""
        try:
            collection = self.db[collection_name]
            await collection.create_index(index_spec, **kwargs)
            logger.info(f"Created index on {collection_name}: {index_spec}")
        except Exception as e:
            logger.error(f"Failed to create index on {collection_name}: {e}")
            raise DatabaseError(f"Index creation failed: {e}")
    
    async def insert_document(
        self,
        collection_name: str,
        document: Dict[str, Any]
    ) -> str:
        """Insert document and return ID"""
        try:
            collection = self.db[collection_name]
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert document in {collection_name}: {e}")
            raise DatabaseError(f"Document insertion failed: {e}")
    
    async def find_documents(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any] = None,
        limit: int = None,
        skip: int = None,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Find documents with optional filtering and pagination"""
        try:
            collection = self.db[collection_name]
            cursor = collection.find(filter_dict or {})
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            raise DatabaseError(f"Document query failed: {e}")


class RedisHelper:
    """Helper class for Redis operations"""
    
    def __init__(self, client: redis.Redis):
        self.client = client
    
    async def set_with_ttl(
        self,
        key: str,
        value: str,
        ttl_seconds: int
    ) -> bool:
        """Set key with TTL"""
        try:
            return await self.client.setex(key, ttl_seconds, value)
        except Exception as e:
            logger.error(f"Failed to set Redis key {key}: {e}")
            raise DatabaseError(f"Redis set operation failed: {e}")
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get and parse JSON value"""
        try:
            import json
            value = await self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Failed to get JSON from Redis key {key}: {e}")
            return None
    
    async def set_json(
        self,
        key: str,
        value: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set JSON value"""
        try:
            import json
            json_str = json.dumps(value)
            if ttl_seconds:
                return await self.client.setex(key, ttl_seconds, json_str)
            else:
                return await self.client.set(key, json_str)
        except Exception as e:
            logger.error(f"Failed to set JSON in Redis key {key}: {e}")
            raise DatabaseError(f"Redis JSON set operation failed: {e}")
    
    async def increment_counter(
        self,
        key: str,
        amount: int = 1,
        ttl_seconds: Optional[int] = None
    ) -> int:
        """Increment counter with optional TTL"""
        try:
            async with self.client.pipeline() as pipe:
                pipe.incr(key, amount)
                if ttl_seconds:
                    pipe.expire(key, ttl_seconds)
                results = await pipe.execute()
                return results[0]
        except Exception as e:
            logger.error(f"Failed to increment Redis counter {key}: {e}")
            raise DatabaseError(f"Redis counter operation failed: {e}")


async def initialize_databases():
    """Initialize all database connections"""
    await db_manager.initialize()


async def close_databases():
    """Close all database connections"""
    await db_manager.close()
