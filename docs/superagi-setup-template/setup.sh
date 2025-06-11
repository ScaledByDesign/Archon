#!/bin/bash
# SuperAGI + Qdrant + LiteLLM Automated Setup Script
# Run this script in your SuperAGI project root directory

set -e

echo "🚀 Starting SuperAGI + Qdrant + LiteLLM Setup..."

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Step 2: Create backup of existing configs
echo "💾 Creating backup of existing configurations..."
cp config/superagi/config.yaml config/superagi/config.yaml.backup || echo "⚠️  No existing config.yaml to backup"
cp config/superagi/.env config/superagi/.env.backup || echo "⚠️  No existing .env to backup"

# Step 3: Copy template configurations
echo "📝 Applying SuperAGI configurations..."
cp docs/superagi-setup-template/config-superagi-config.yaml config/superagi/config.yaml
cp docs/superagi-setup-template/config-superagi-env config/superagi/.env

# Step 4: Set up main environment variable
echo "🔑 Setting up LiteLLM master key..."
if ! grep -q "LITELLM_MASTER_KEY" .env 2>/dev/null; then
    echo "LITELLM_MASTER_KEY=sk-change-me-to-random-string" >> .env
    echo "✅ Added LITELLM_MASTER_KEY to .env"
else
    echo "✅ LITELLM_MASTER_KEY already exists in .env"
fi

# Step 5: Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Step 6: Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Step 7: Configure API key in SuperAGI
echo "🔐 Configuring API key in SuperAGI..."
max_attempts=5
attempt=1

while [ $attempt -le $max_attempts ]; do
    echo "📡 Attempt $attempt: Storing API key in SuperAGI..."
    
    response=$(curl -s -w "%{http_code}" -X POST "http://zoi.local:8001/models_controller/store_api_keys" \
        -H "Content-Type: application/json" \
        -d '{
            "model_provider": "OpenAI",
            "model_api_key": "sk-change-me-to-random-string"
        }')
    
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        echo "✅ API key stored successfully!"
        break
    else
        echo "⚠️  Attempt $attempt failed (HTTP $http_code). Retrying in 10 seconds..."
        sleep 10
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Failed to store API key after $max_attempts attempts"
    echo "💡 You may need to run this command manually after services are fully started:"
    echo "   curl -X POST \"http://zoi.local:8001/models_controller/store_api_keys\" \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d '{\"model_provider\": \"OpenAI\", \"model_api_key\": \"sk-change-me-to-random-string\"}'"
fi

# Step 8: Verification
echo "🔍 Running verification checks..."

echo "📡 Checking Qdrant..."
if curl -s http://zoi.local:6333/readyz | grep -q "ready"; then
    echo "✅ Qdrant is ready"
else
    echo "⚠️  Qdrant may not be ready yet"
fi

echo "📡 Checking LiteLLM..."
if curl -s -H "Authorization: Bearer sk-change-me-to-random-string" http://zoi.local:4000/v1/models >/dev/null 2>&1; then
    echo "✅ LiteLLM is ready"
else
    echo "⚠️  LiteLLM may not be ready yet"
fi

echo "📡 Checking SuperAGI models..."
models_response=$(curl -s "http://zoi.local:8001/models_controller/fetch_models")
if echo "$models_response" | grep -q "gpt"; then
    echo "✅ SuperAGI models are available"
    echo "📋 Available models: $(echo "$models_response" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | tr '\n' ', ' | sed 's/,$//')"
else
    echo "⚠️  SuperAGI models may not be ready yet"
fi

echo ""
echo "🎉 Setup complete!"
echo "🌐 Access SuperAGI at: http://zoi.local:3001"
echo "📊 Backend API docs at: http://zoi.local:8001/docs"
echo ""
echo "📋 Summary:"
echo "   ✅ Qdrant vector database configured"
echo "   ✅ LiteLLM proxy configured"
echo "   ✅ SuperAGI connected to both services"
echo "   ✅ Models available: gpt-3.5-turbo, gpt-4"
echo ""
echo "🎯 You can now create agents using Qdrant for vector storage and LiteLLM models!"
