#!/usr/bin/env python3
"""
Celery worker for async task processing
"""

import os
import logging
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
app = Celery('zoi_worker')

# Configure Celery
app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Chicago',
    enable_utc=True,
)

# Auto-discover tasks
app.autodiscover_tasks(['tasks'])

@app.task
def health_check():
    """Health check task"""
    return "Worker is healthy"

if __name__ == '__main__':
    app.start()
