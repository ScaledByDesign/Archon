// Neo4j Bootstrap Schema for Zoi Ecosystem
// Creates nodes, relationships, constraints, and indexes for AI/ML knowledge graphs

// ==============================================
// CONSTRAINTS (Unique identifiers)
// ==============================================

// User and Identity Management
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT user_email_unique IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE;
CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE;

// AI Models and Services
CREATE CONSTRAINT model_id_unique IF NOT EXISTS FOR (m:Model) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT model_name_unique IF NOT EXISTS FOR (m:Model) REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT service_name_unique IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE;

// Knowledge Management
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE;

// Workflow and Automation
CREATE CONSTRAINT workflow_id_unique IF NOT EXISTS FOR (w:Workflow) REQUIRE w.id IS UNIQUE;
CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE;

// ==============================================
// INDEXES (Performance optimization)
// ==============================================

// User and Session Indexes
CREATE INDEX user_created_at IF NOT EXISTS FOR (u:User) ON (u.created_at);
CREATE INDEX session_expires_at IF NOT EXISTS FOR (s:Session) ON (s.expires_at);
CREATE INDEX user_last_active IF NOT EXISTS FOR (u:User) ON (u.last_active);

// Model and Service Indexes
CREATE INDEX model_provider IF NOT EXISTS FOR (m:Model) ON (m.provider);
CREATE INDEX model_type IF NOT EXISTS FOR (m:Model) ON (m.type);
CREATE INDEX service_status IF NOT EXISTS FOR (s:Service) ON (s.status);
CREATE INDEX model_cost IF NOT EXISTS FOR (m:Model) ON (m.cost_per_token);

// Document and Knowledge Indexes
CREATE INDEX document_created_at IF NOT EXISTS FOR (d:Document) ON (d.created_at);
CREATE INDEX document_type IF NOT EXISTS FOR (d:Document) ON (d.type);
CREATE INDEX concept_category IF NOT EXISTS FOR (c:Concept) ON (c.category);
CREATE INDEX topic_created_at IF NOT EXISTS FOR (t:Topic) ON (t.created_at);

// Workflow and Task Indexes
CREATE INDEX workflow_status IF NOT EXISTS FOR (w:Workflow) ON (w.status);
CREATE INDEX task_priority IF NOT EXISTS FOR (t:Task) ON (t.priority);
CREATE INDEX task_status IF NOT EXISTS FOR (t:Task) ON (t.status);
CREATE INDEX agent_type IF NOT EXISTS FOR (a:Agent) ON (a.type);

// Full-text search indexes
CREATE FULLTEXT INDEX document_content IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.content];
CREATE FULLTEXT INDEX concept_search IF NOT EXISTS FOR (c:Concept) ON EACH [c.name, c.description];
CREATE FULLTEXT INDEX workflow_search IF NOT EXISTS FOR (w:Workflow) ON EACH [w.name, w.description];

// ==============================================
// INITIAL DATA SETUP
// ==============================================

// Create Zoi System Services
MERGE (litellm:Service {
  name: "LiteLLM",
  type: "AI_PROXY",
  description: "AI model proxy and routing service",
  endpoint: "http://litellm:4000",
  status: "active",
  created_at: datetime()
});

MERGE (authentik:Service {
  name: "Authentik",
  type: "AUTHENTICATION",
  description: "Identity and access management",
  endpoint: "http://authentik:9000",
  status: "active",
  created_at: datetime()
});

MERGE (n8n:Service {
  name: "n8n",
  type: "WORKFLOW",
  description: "Workflow automation platform",
  endpoint: "http://n8n:5678",
  status: "active",
  created_at: datetime()
});

MERGE (openwebui:Service {
  name: "OpenWebUI",
  type: "CHAT_INTERFACE",
  description: "AI chat interface",
  endpoint: "http://openwebui:8080",
  status: "active",
  created_at: datetime()
});

MERGE (lobechat:Service {
  name: "LobeChat",
  type: "CHAT_INTERFACE",
  description: "Advanced AI chat interface",
  endpoint: "http://lobechat:3210",
  status: "active",
  created_at: datetime()
});

MERGE (qdrant:Service {
  name: "Qdrant",
  type: "VECTOR_DATABASE",
  description: "Vector similarity search engine",
  endpoint: "http://qdrant:6333",
  status: "active",
  created_at: datetime()
});

MERGE (postgres:Service {
  name: "PostgreSQL",
  type: "DATABASE",
  description: "Relational database with vector support",
  endpoint: "postgres:5432",
  status: "active",
  created_at: datetime()
});

MERGE (redis:Service {
  name: "Redis",
  type: "CACHE",
  description: "In-memory cache and session store",
  endpoint: "redis:6379",
  status: "active",
  created_at: datetime()
});

MERGE (mongodb:Service {
  name: "MongoDB",
  type: "DOCUMENT_DATABASE",
  description: "Document-oriented database",
  endpoint: "mongo:27017",
  status: "active",
  created_at: datetime()
});

// Create AI Model Categories
MERGE (llm:ModelCategory {
  name: "Large Language Models",
  type: "LLM",
  description: "Text generation and understanding models"
});

MERGE (embedding:ModelCategory {
  name: "Embedding Models",
  type: "EMBEDDING",
  description: "Text to vector embedding models"
});

MERGE (vision:ModelCategory {
  name: "Vision Models",
  type: "VISION",
  description: "Image understanding and generation models"
});

// Create default AI models
MERGE (qwen:Model {
  id: "qwen2.5-coder:7b-instruct",
  name: "Qwen 2.5 Coder",
  provider: "Ollama",
  type: "LLM",
  context_length: 32768,
  cost_per_token: 0.0,
  status: "active",
  created_at: datetime()
});

MERGE (embed:Model {
  id: "mxbai-embed-large",
  name: "MxBai Embed Large",
  provider: "Ollama",
  type: "EMBEDDING",
  vector_size: 1024,
  cost_per_token: 0.0,
  status: "active",
  created_at: datetime()
});

// Create relationships between services and models
MATCH (litellm:Service {name: "LiteLLM"})
MATCH (qwen:Model {id: "qwen2.5-coder:7b-instruct"})
MERGE (litellm)-[:SERVES]->(qwen);

MATCH (litellm:Service {name: "LiteLLM"})
MATCH (embed:Model {id: "mxbai-embed-large"})
MERGE (litellm)-[:SERVES]->(embed);

// Create knowledge domains
MERGE (ai:Domain {
  name: "Artificial Intelligence",
  description: "AI, ML, and related technologies",
  created_at: datetime()
});

MERGE (dev:Domain {
  name: "Software Development",
  description: "Programming, architecture, and development practices",
  created_at: datetime()
});

MERGE (ops:Domain {
  name: "DevOps & Infrastructure",
  description: "Deployment, monitoring, and infrastructure management",
  created_at: datetime()
});

// Create system admin user
MERGE (admin:User {
  id: "system-admin",
  username: "admin",
  email: "admin@zoi.local",
  role: "administrator",
  created_at: datetime(),
  last_active: datetime()
});

// ==============================================
// UTILITY PROCEDURES (Custom functions)
// ==============================================

// Note: These would typically be implemented as APOC procedures
// For now, we'll create them as comments for future implementation

/*
// Procedure to find similar documents based on concepts
CALL zoi.findSimilarDocuments(documentId, limit) YIELD document, similarity

// Procedure to recommend models based on task type
CALL zoi.recommendModels(taskType, requirements) YIELD model, score

// Procedure to analyze workflow efficiency
CALL zoi.analyzeWorkflow(workflowId) YIELD metrics, suggestions

// Procedure to track model usage and costs
CALL zoi.trackModelUsage(modelId, timeRange) YIELD usage, cost
*/
