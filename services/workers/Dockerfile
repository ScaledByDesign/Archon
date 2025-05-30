FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker source code
COPY worker.py .
COPY tasks/ ./tasks/

# Create user for security
RUN useradd --create-home --shell /bin/bash worker
USER worker

# Default command
CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--concurrency=1"]
