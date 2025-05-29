"""
Document Queue Consumer
Consumes document processing messages from RabbitMQ
"""

import os
import json
import logging
import asyncio
import base64
import time
import signal
from typing import Dict, Any, Optional, Callable, List
import uuid
from io import BytesIO

# import aio_pika
# from aio_pika.abc import AbstractIncomingMessage

from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class DocumentQueueConsumer:
    """Consumer for document processing queue"""
    
    def __init__(
        self,
        processor: Optional[DocumentProcessor] = None,
        rabbitmq_url: Optional[str] = None,
        queue_name: str = "document_processing",
        prefetch_count: int = 10,
        max_retries: int = 3,
        error_queue_name: str = "document_processing_errors"
    ):
        """Initialize document queue consumer
        
        Args:
            processor: Document processor instance
            rabbitmq_url: RabbitMQ connection URL
            queue_name: Queue name for document processing
            prefetch_count: Number of messages to prefetch
            max_retries: Maximum number of retries for failed messages
            error_queue_name: Queue name for error messages
        """
        # Initialize document processor
        self.processor = processor or DocumentProcessor()
        
        # RabbitMQ configuration
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.queue_name = queue_name
        self.error_queue_name = error_queue_name
        self.prefetch_count = prefetch_count
        self.max_retries = max_retries
        
        # Runtime state
        self.connection = None
        self.channel = None
        self.running = False
        self.tasks = []
    
    async def setup(self):
        """Set up RabbitMQ connection and channels"""
        # Setup document processor
        await self.processor.setup()
        
        # Connect to RabbitMQ
        # self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        
        # Create channel
        # self.channel = await self.connection.channel()
        # await self.channel.set_qos(prefetch_count=self.prefetch_count)
        
        # Declare queues
        # await self.channel.declare_queue(self.queue_name, durable=True)
        # await self.channel.declare_queue(self.error_queue_name, durable=True)
        
        logger.info(f"Connected to RabbitMQ, consuming from {self.queue_name}")
    
    async def start(self):
        """Start consuming messages"""
        if not self.channel:
            await self.setup()
        
        # Mark as running
        self.running = True
        
        # Get queue
        # queue = await self.channel.declare_queue(self.queue_name, durable=True)
        
        # Start consuming
        # await queue.consume(self.process_message)
        
        logger.info("Started document queue consumer")
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
    
    async def shutdown(self):
        """Shut down the consumer gracefully"""
        if not self.running:
            return
        
        logger.info("Shutting down document queue consumer...")
        self.running = False
        
        # Wait for all tasks to complete
        if self.tasks:
            logger.info(f"Waiting for {len(self.tasks)} tasks to complete...")
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close channel and connection
        # if self.channel:
        #     await self.channel.close()
        #     self.channel = None
        
        # if self.connection:
        #     await self.connection.close()
        #     self.connection = None
        
        logger.info("Document queue consumer shut down")
    
    async def process_message(self, message):
        """Process a message from the queue
        
        Args:
            message: Incoming message
        """
        # Create a task to process the message
        task = asyncio.create_task(self._handle_message(message))
        self.tasks.append(task)
        
        # Remove task when done
        task.add_done_callback(lambda t: self.tasks.remove(t) if t in self.tasks else None)
    
    async def _handle_message(self, message):
        """Handle a message from the queue
        
        Args:
            message: Incoming message
        """
        # async with message.process():
        #     body = message.body.decode()
            
        #     # Parse message
        #     try:
        #         data = json.loads(body)
        #         logger.info(f"Received document processing message: {data.get('document_id', 'unknown')}")
                
        #         # Extract message data
        #         document_id = data.get("document_id", str(uuid.uuid4()))
        #         filename = data.get("filename", f"document_{document_id}")
        #         file_content_b64 = data.get("file_content")
        #         metadata = data.get("metadata", {})
        #         trace_id = data.get("trace_id")
                
        #         # Check retry count
        #         retry_count = data.get("retry_count", 0)
                
        #         # Decode file content
        #         if file_content_b64:
        #             file_content = base64.b64decode(file_content_b64)
        #         else:
        #             raise ValueError("No file content provided")
                
        #         # Process document
        #         result = await self.processor.process_document(
        #             file_content=BytesIO(file_content),
        #             filename=filename,
        #             metadata=metadata,
        #             document_id=document_id,
        #             trace_id=trace_id
        #         )
                
        #         logger.info(f"Document processed successfully: {document_id}")
                
        #     except Exception as e:
        #         logger.error(f"Error processing document: {str(e)}")
                
        #         # Retry if not exceeded max retries
        #         if retry_count < self.max_retries:
        #             # Increment retry count
        #             data["retry_count"] = retry_count + 1
        #             data["last_error"] = str(e)
                    
        #             # Send to queue with delay
        #             await self._requeue_with_delay(data, retry_count)
        #         else:
        #             # Send to error queue
        #             data["error"] = str(e)
        #             await self._send_to_error_queue(data)
    
    async def _requeue_with_delay(self, data, retry_count):
        """Requeue a message with delay
        
        Args:
            data: Message data
            retry_count: Current retry count
        """
        # Calculate delay (exponential backoff)
        # delay_seconds = min(60, 5 * (2 ** retry_count))
        
        # Create exchange and queue for delayed messages
        # exchange = await self.channel.declare_exchange("delayed", "x-delayed-message", durable=True, arguments={
        #     "x-delayed-type": "direct"
        # })
        
        # Create message with delay header
        # message_body = json.dumps(data).encode()
        # message = aio_pika.Message(
        #     body=message_body,
        #     delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        #     headers={"x-delay": delay_seconds * 1000}  # delay in ms
        # )
        
        # Publish to delayed exchange
        # await exchange.publish(message, routing_key=self.queue_name)
        # logger.info(f"Requeued document with ID {data.get('document_id')} for retry in {delay_seconds}s")
    
    async def _send_to_error_queue(self, data):
        """Send a message to the error queue
        
        Args:
            data: Message data
        """
        # Add timestamp
        # data["error_timestamp"] = time.time()
        
        # Create message
        # message_body = json.dumps(data).encode()
        # message = aio_pika.Message(
        #     body=message_body,
        #     delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        # )
        
        # Publish to error queue
        # await self.channel.default_exchange.publish(message, routing_key=self.error_queue_name)
        # logger.error(f"Sent document with ID {data.get('document_id')} to error queue after max retries")
    
    async def enqueue_document(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Enqueue a document for processing
        
        Args:
            file_content: Binary file content
            filename: Original filename
            metadata: Additional document metadata
            document_id: Document ID (generated if not provided)
            trace_id: Trace ID for observability
            
        Returns:
            Document ID
        """
        if not self.channel:
            await self.setup()
        
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Create message data
        data = {
            "document_id": document_id,
            "filename": filename,
            "file_content": base64.b64encode(file_content).decode(),
            "metadata": metadata,
            "trace_id": trace_id,
            "enqueued_at": time.time()
        }
        
        # Create message
        # message_body = json.dumps(data).encode()
        # message = aio_pika.Message(
        #     body=message_body,
        #     delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        # )
        
        # Publish to queue
        # await self.channel.default_exchange.publish(message, routing_key=self.queue_name)
        # logger.info(f"Enqueued document for processing: {document_id}")
        
        return document_id


async def run_consumer():
    """Run the document queue consumer"""
    # Create consumer
    consumer = DocumentQueueConsumer()
    
    # Start consumer
    await consumer.start()
    
    try:
        # Keep running until shutdown
        while consumer.running:
            await asyncio.sleep(1)
    finally:
        # Ensure shutdown
        await consumer.shutdown()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run consumer
    asyncio.run(run_consumer())
