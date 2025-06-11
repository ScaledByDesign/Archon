# SuperAGI + Qdrant + LiteLLM Setup Template

This directory contains everything needed to quickly set up SuperAGI with Qdrant vector database and LiteLLM on a new server.

## 🚀 Quick Setup (Automated)

### Option 1: Run the Setup Script
```bash
# From your SuperAGI project root directory
./docs/superagi-setup-template/setup.sh
```

### Option 2: Manual Setup

#### Step 1: Copy Configuration Files
```bash
# Copy SuperAGI config
cp docs/superagi-setup-template/config-superagi-config.yaml config/superagi/config.yaml

# Copy SuperAGI environment variables  
cp docs/superagi-setup-template/config-superagi-env config/superagi/.env
```

#### Step 2: Set Environment Variables
```bash
# Add LiteLLM master key to main .env file
echo "LITELLM_MASTER_KEY=sk-change-me-to-random-string" >> .env
```

#### Step 3: Start Services
```bash
docker-compose up -d
```

#### Step 4: Configure API Key
```bash
# Wait for services to start, then run:
curl -X POST "http://zoi.local:8001/models_controller/store_api_keys" \
  -H "Content-Type: application/json" \
  -d '{
    "model_provider": "OpenAI", 
    "model_api_key": "sk-change-me-to-random-string"
  }'
```

## 📋 File Descriptions

- `config-superagi-config.yaml` - SuperAGI main configuration template
- `config-superagi-env` - SuperAGI environment variables template
- `setup.sh` - Automated setup script
- `README.md` - This file

## ✅ Expected Results

After setup completion:
- **SuperAGI UI**: http://zoi.local:3001
- **Available Models**: gpt-3.5-turbo, gpt-4 
- **Vector Database**: Qdrant (system-level configured)
- **LLM Provider**: LiteLLM proxy

## 🔧 Key Configuration Changes

### SuperAGI config.yaml Changes:
- `OPENAI_API_BASE: http://litellm:4000/v1`
- `WEAVIATE_USE_EMBEDDED: false`
- `QDRANT_HOST_NAME: qdrant`
- `QDRANT_PORT: 6333`
- `VECTOR_STORE: qdrant`

### SuperAGI .env Additions:
- `ENV=DEV`
- `QDRANT_HOST_NAME=qdrant`
- `QDRANT_PORT=6333`
- `LITELLM_API_BASE=http://litellm:4000`
- `OPENAI_API_KEY=${LITELLM_MASTER_KEY}`

## 🚨 Important Notes

1. **Prerequisites**: Docker, Docker Compose, SuperAGI codebase
2. **Service Dependencies**: Ensure Qdrant and LiteLLM services are in docker-compose.yml
3. **API Key Storage**: Must be done after services start
4. **Development Mode**: ENV=DEV enables simplified authentication

## 🔍 Verification Commands

```bash
# Check Qdrant
curl -s http://zoi.local:6333/readyz

# Check LiteLLM
curl -s -H "Authorization: Bearer sk-change-me-to-random-string" http://zoi.local:4000/v1/models

# Check SuperAGI Models
curl -s "http://zoi.local:8001/models_controller/fetch_models"
```

## 🏆 Success Criteria

✅ All services running without errors
✅ SuperAGI shows gpt-3.5-turbo and gpt-4 models available
✅ Qdrant accessible and responding
✅ LiteLLM proxy working with authentication
✅ SuperAGI UI accessible at zoi.local:3001

This template provides a complete, reproducible setup for SuperAGI with Qdrant vector storage and LiteLLM multi-model support!
