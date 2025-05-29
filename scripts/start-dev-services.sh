#!/bin/bash
# Start development services for Zoi FastAPI application
# Run this script after docker-compose up to ensure all services are available

echo "Starting core infrastructure services..."
docker-compose up -d postgres redis rabbitmq vault

echo "Starting database services..."
docker-compose up -d mongo-episodic mongo-procedural

echo "Starting vector database..."
docker-compose up -d qdrant

echo "Starting FastAPI services..."
docker-compose up -d fastapi-1 fastapi-2 fastapi-3

echo "Waiting for services to be healthy..."
sleep 15

echo "Checking service health..."
echo "FastAPI-1 (8000):"
curl -s http://localhost:8000/health | jq .status

echo "FastAPI-2 (8010):"
curl -s http://localhost:8010/health | jq .status

echo "FastAPI-3 (8020):"
curl -s http://localhost:8020/health | jq .status

echo "All services started! 🚀"
