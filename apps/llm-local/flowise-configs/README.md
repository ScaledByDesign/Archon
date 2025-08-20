# 📁 Flowise Configuration as Code

This directory contains JSON-based Flowise chatflow configurations that can be deployed programmatically, enabling Infrastructure as Code (IaC) for your AI workflows.

## 🎯 **Benefits of Flat File Configuration**

### ✅ **Version Control**
- Track changes to AI workflows in Git
- Collaborate on chatflow development
- Rollback to previous configurations
- Branch and merge workflow changes

### ✅ **Automation & CI/CD**
- Deploy chatflows via scripts
- Integrate with deployment pipelines
- Environment-specific configurations
- Automated testing of workflows

### ✅ **Consistency & Reproducibility**
- Identical deployments across environments
- No manual UI configuration errors
- Standardized workflow patterns
- Easy backup and restore

## 📂 **File Structure**

```
flowise-configs/
├── README.md                           # This file
├── litellm-development-chatflow.json   # Basic development assistant
├── litellm-rag-chatflow.json          # RAG-enhanced knowledge assistant
├── litellm-credentials.json           # Credential configurations
└── templates/                         # Reusable templates
    ├── basic-chat-template.json
    ├── rag-template.json
    └── agent-template.json
```

## 🔧 **Configuration Files**

### **1. litellm-development-chatflow.json**
**Purpose**: Basic development-focused chatbot
**Features**:
- ChatOpenAI node configured for LiteLLM
- Buffer memory for conversation history
- Development-optimized system prompt
- Temperature: 0.1 for precise code generation

### **2. litellm-rag-chatflow.json**
**Purpose**: RAG-enhanced knowledge assistant
**Features**:
- ChatOpenAI + OpenAI Embeddings integration
- Qdrant vector store connection
- Conversational Retrieval QA Chain
- Source document return capability

### **3. litellm-credentials.json**
**Purpose**: Credential and environment configuration
**Features**:
- API key management
- Environment variables
- Model parameter presets
- Endpoint configurations

## 🚀 **Deployment Methods**

### **Method 1: Python Script (Recommended)**

```bash
# Deploy all configurations
python scripts/deploy_flowise_configs.py

# Deploy specific configuration
python scripts/deploy_flowise_configs.py litellm-development-chatflow.json

# Validate configuration before deployment
python scripts/deploy_flowise_configs.py --validate litellm-rag-chatflow.json
```

### **Method 2: PowerShell Script**

```powershell
# Deploy all configurations
.\scripts\deploy_flowise_configs.ps1

# Deploy specific configuration
.\scripts\deploy_flowise_configs.ps1 -ConfigFile "litellm-development-chatflow.json"

# With custom Flowise URL and API key
.\scripts\deploy_flowise_configs.ps1 -FlowiseUrl "http://localhost:7070" -ApiKey "your-api-key"
```

### **Method 3: Direct API Calls**

```bash
# Create new chatflow
curl -X POST "http://localhost:7070/api/v1/chatflows" \
  -H "Content-Type: application/json" \
  -d @litellm-development-chatflow.json

# Update existing chatflow
curl -X PUT "http://localhost:7070/api/v1/chatflows/{chatflow-id}" \
  -H "Content-Type: application/json" \
  -d @litellm-development-chatflow.json
```

### **Method 4: Import via Flowise UI**

1. Open Flowise at http://localhost:7070
2. Click "Add New Chatflow"
3. Click "Load Chatflow" button
4. Select JSON file from this directory
5. Click "Save Chatflow"

## 🔧 **Configuration Structure**

### **Basic Chatflow JSON Structure**

```json
{
  "name": "Chatflow Name",
  "description": "Chatflow description",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "node_id",
      "position": {"x": 400, "y": 200},
      "type": "customNode",
      "data": {
        "label": "Node Label",
        "name": "nodeName",
        "type": "NodeType",
        "inputs": {
          "parameter": "value"
        }
      }
    }
  ],
  "edges": [
    {
      "source": "source_node_id",
      "target": "target_node_id",
      "type": "buttonedge"
    }
  ],
  "chatflowid": "unique-chatflow-id",
  "category": "Category Name",
  "type": "CHATFLOW"
}
```

### **Node Configuration Examples**

#### **ChatOpenAI Node (LiteLLM)**
```json
{
  "id": "chatOpenAI_0",
  "data": {
    "label": "ChatOpenAI",
    "name": "chatOpenAI",
    "inputs": {
      "modelName": "zoi-coder-vllm",
      "temperature": 0.1,
      "maxTokens": 4096,
      "basepath": "http://localhost:7010"
    }
  }
}
```

#### **OpenAI Embeddings Node (LiteLLM)**
```json
{
  "id": "openAIEmbeddings_0",
  "data": {
    "label": "OpenAI Embeddings",
    "name": "openAIEmbeddings",
    "inputs": {
      "modelName": "zoi-embed",
      "basepath": "http://localhost:7010"
    }
  }
}
```

#### **Qdrant Vector Store Node**
```json
{
  "id": "qdrant_0",
  "data": {
    "label": "Qdrant",
    "name": "qdrant",
    "inputs": {
      "qdrantServerUrl": "http://localhost:7050",
      "collectionName": "zoi_knowledge_base"
    }
  }
}
```

## 🎯 **Model Selection Guide**

| Use Case | Model | Temperature | Max Tokens | Best For |
|----------|-------|-------------|------------|----------|
| **Code Generation** | `zoi-coder-vllm` | 0.05-0.1 | 4096-6144 | Precise coding |
| **Quick Help** | `zoi-helper` | 0.1 | 3072 | Fast assistance |
| **Planning** | `zoi-thinker` | 0.2 | 4096 | Architecture |
| **RAG Q&A** | `zoi-rag-helper` | 0.15 | 5120 | Knowledge-aware |
| **Embeddings** | `zoi-embed` | N/A | N/A | Vector operations |

## 🔐 **Security Considerations**

### **API Keys**
- Store API keys in environment variables
- Use credential management systems in production
- Never commit API keys to version control
- Rotate keys regularly

### **Access Control**
- Set up Flowise authentication
- Use chatflow-level API keys
- Implement rate limiting
- Monitor API usage

## 🧪 **Testing Configurations**

### **Validation Checklist**
- [ ] JSON syntax is valid
- [ ] Required fields are present
- [ ] Node IDs are unique
- [ ] Edge connections are valid
- [ ] Model names match LiteLLM config
- [ ] Endpoints are accessible

### **Testing Commands**
```bash
# Validate JSON syntax
python -m json.tool litellm-development-chatflow.json

# Test chatflow deployment
python scripts/deploy_flowise_configs.py --validate litellm-development-chatflow.json

# Test API connectivity
curl -X GET "http://localhost:7070/api/v1/chatflows"
```

## 🔄 **Environment Management**

### **Development Environment**
```json
{
  "basepath": "http://localhost:7010",
  "qdrantServerUrl": "http://localhost:7050",
  "temperature": 0.1
}
```

### **Production Environment**
```json
{
  "basepath": "https://litellm.yourdomain.com",
  "qdrantServerUrl": "https://qdrant.yourdomain.com",
  "temperature": 0.05
}
```

## 📊 **Monitoring & Maintenance**

### **Health Checks**
- Monitor chatflow API endpoints
- Check model availability
- Validate vector store connections
- Test end-to-end workflows

### **Updates & Rollbacks**
- Version your configuration files
- Test changes in staging environment
- Use blue-green deployments
- Keep rollback configurations ready

## 🎉 **Getting Started**

1. **Deploy Basic Configuration**:
   ```bash
   python scripts/deploy_flowise_configs.py litellm-development-chatflow.json
   ```

2. **Test the Chatflow**:
   ```bash
   curl -X POST "http://localhost:7070/api/v1/prediction/{chatflow-id}" \
     -H "Content-Type: application/json" \
     -d '{"question": "Write a Python function to calculate fibonacci numbers"}'
   ```

3. **Deploy RAG Configuration**:
   ```bash
   python scripts/deploy_flowise_configs.py litellm-rag-chatflow.json
   ```

4. **Customize for Your Needs**:
   - Modify model parameters
   - Add new nodes and connections
   - Create environment-specific configs
   - Set up automated deployments

Your Flowise workflows are now managed as code! 🚀✨
