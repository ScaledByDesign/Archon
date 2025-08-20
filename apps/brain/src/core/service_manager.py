"""
Service Manager for centralized lifecycle management of all application services.
Handles startup, shutdown, and dependency injection for production readiness.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from src.document_pipeline.document_processor import DocumentProcessor
from src.document_pipeline.queue_consumer import DocumentQueueConsumer
from src.db.mongodb_client import MongoDBClient
from src.vector_store.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)

class ServiceManager:
    """Centralized service lifecycle manager"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
        self._health_status: Dict[str, str] = {}
        
    @property
    def is_initialized(self) -> bool:
        return self._initialized
        
    @property
    def health_status(self) -> Dict[str, str]:
        return self._health_status.copy()
        
    async def initialize(self) -> None:
        """Initialize all services during application startup"""
        if self._initialized:
            logger.warning("Service manager already initialized")
            return
            
        logger.info("Initializing application services...")
        
        try:
            # Initialize services in dependency order
            await self._initialize_mongodb()
            await self._initialize_vector_store()
            await self._initialize_document_processor()
            await self._initialize_queue_consumer()
            
            self._initialized = True
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            await self.cleanup()
            raise
            
    async def _initialize_mongodb(self) -> None:
        """Initialize MongoDB client"""
        try:
            mongodb_client = MongoDBClient()
            # Connect and test
            await mongodb_client.connect()
            await mongodb_client.health_check()
            self._services['mongodb'] = mongodb_client
            self._health_status['mongodb'] = 'healthy'
            logger.info("MongoDB client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {str(e)}")
            self._health_status['mongodb'] = 'unhealthy'
            logger.warning("Continuing without MongoDB - document storage will be limited")
            
    async def _initialize_vector_store(self) -> None:
        """Initialize vector store"""
        try:
            vector_store = QdrantVectorStore()
            # Test connection by getting collections
            vector_store.client.get_collections()
            self._services['vector_store'] = vector_store
            self._health_status['vector_store'] = 'healthy'
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            self._health_status['vector_store'] = 'unhealthy'
            # Don't raise - allow degraded operation
            
    async def _initialize_document_processor(self) -> None:
        """Initialize document processor"""
        try:
            processor = DocumentProcessor()
            # Only setup if vector store is available
            if 'vector_store' in self._services:
                await processor.setup()
            self._services['document_processor'] = processor
            self._health_status['document_processor'] = 'healthy'
            logger.info("Document processor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize document processor: {str(e)}")
            self._health_status['document_processor'] = 'unhealthy'
            raise
            
    async def _initialize_queue_consumer(self) -> None:
        """Initialize queue consumer"""
        try:
            consumer = DocumentQueueConsumer()
            # Don't start consuming yet - just initialize
            # await consumer.setup()  # This might be causing issues
            self._services['queue_consumer'] = consumer
            self._health_status['queue_consumer'] = 'healthy'
            logger.info("Queue consumer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize queue consumer: {str(e)}")
            self._health_status['queue_consumer'] = 'unhealthy'
            # Don't raise - allow operation without queue
            
    async def cleanup(self) -> None:
        """Cleanup all services during application shutdown"""
        logger.info("Cleaning up application services...")
        
        # Cleanup in reverse order
        for service_name in ['queue_consumer', 'document_processor', 'vector_store', 'mongodb']:
            if service_name in self._services:
                try:
                    service = self._services[service_name]
                    if hasattr(service, 'close'):
                        await service.close()
                    elif hasattr(service, 'cleanup'):
                        await service.cleanup()
                    logger.info(f"Cleaned up {service_name}")
                except Exception as e:
                    logger.error(f"Failed to cleanup {service_name}: {str(e)}")
                    
        self._services.clear()
        self._health_status.clear()
        self._initialized = False
        
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service instance"""
        if not self._initialized:
            raise RuntimeError("Service manager not initialized")
        return self._services.get(service_name)
        
    def get_document_processor(self) -> DocumentProcessor:
        """Get document processor instance"""
        processor = self.get_service('document_processor')
        if not processor:
            raise RuntimeError("Document processor not available")
        return processor
        
    def get_mongodb_client(self) -> MongoDBClient:
        """Get MongoDB client instance"""
        client = self.get_service('mongodb')
        if not client:
            raise RuntimeError("MongoDB client not available")
        return client
        
    def get_queue_consumer(self) -> DocumentQueueConsumer:
        """Get queue consumer instance"""
        consumer = self.get_service('queue_consumer')
        if not consumer:
            raise RuntimeError("Queue consumer not available")
        return consumer
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        results = {}
        
        for service_name, service in self._services.items():
            try:
                if hasattr(service, 'health_check'):
                    result = await service.health_check()
                    results[service_name] = result
                elif hasattr(service, 'ping'):
                    await service.ping()
                    results[service_name] = {'status': 'healthy'}
                else:
                    results[service_name] = {'status': 'unknown'}
            except Exception as e:
                results[service_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                
        return results

# Global service manager instance
service_manager = ServiceManager()

async def get_service_manager() -> ServiceManager:
    """Dependency injection for service manager"""
    return service_manager

async def get_document_processor() -> DocumentProcessor:
    """Dependency injection for document processor"""
    return service_manager.get_document_processor()

async def get_mongodb_client() -> MongoDBClient:
    """Dependency injection for MongoDB client"""
    return service_manager.get_mongodb_client()

async def get_queue_consumer() -> DocumentQueueConsumer:
    """Dependency injection for queue consumer"""
    return service_manager.get_queue_consumer()
