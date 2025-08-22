// MongoDB initialization script for multiple databases
// This script creates multiple databases with appropriate collections and indexes

// Connect to admin database first
db = db.getSiblingDB('admin');

// Define databases to create
const databases = [
  {
    name: 'rag_system',
    description: 'Main RAG system database for document processing and vector storage',
    collections: [
      {
        name: 'documents',
        indexes: [
          { key: { 'metadata.source': 1 }, name: 'source_idx' },
          { key: { 'metadata.created_at': -1 }, name: 'created_at_idx' },
          { key: { 'embeddings.vector_id': 1 }, name: 'vector_id_idx' }
        ]
      },
      {
        name: 'chunks',
        indexes: [
          { key: { 'document_id': 1 }, name: 'document_id_idx' },
          { key: { 'chunk_index': 1 }, name: 'chunk_index_idx' },
          { key: { 'metadata.page': 1 }, name: 'page_idx' }
        ]
      },
      {
        name: 'embeddings',
        indexes: [
          { key: { 'chunk_id': 1 }, name: 'chunk_id_idx' },
          { key: { 'model': 1 }, name: 'model_idx' },
          { key: { 'created_at': -1 }, name: 'created_at_idx' }
        ]
      },
      {
        name: 'conversations',
        indexes: [
          { key: { 'session_id': 1 }, name: 'session_id_idx' },
          { key: { 'user_id': 1 }, name: 'user_id_idx' },
          { key: { 'created_at': -1 }, name: 'created_at_idx' }
        ]
      },
      {
        name: 'queries',
        indexes: [
          { key: { 'conversation_id': 1 }, name: 'conversation_id_idx' },
          { key: { 'query_hash': 1 }, name: 'query_hash_idx' },
          { key: { 'timestamp': -1 }, name: 'timestamp_idx' }
        ]
      }
    ]
  },
  {
    name: 'authentik',
    description: 'Authentik authentication and authorization database',
    collections: [
      {
        name: 'sessions',
        indexes: [
          { key: { 'session_key': 1 }, name: 'session_key_idx', unique: true },
          { key: { 'expire_date': 1 }, name: 'expire_date_idx', expireAfterSeconds: 0 }
        ]
      },
      {
        name: 'users',
        indexes: [
          { key: { 'username': 1 }, name: 'username_idx', unique: true },
          { key: { 'email': 1 }, name: 'email_idx', unique: true }
        ]
      }
    ]
  },
  {
    name: 'n8n',
    description: 'n8n workflow automation database',
    collections: [
      {
        name: 'workflows',
        indexes: [
          { key: { 'name': 1 }, name: 'name_idx' },
          { key: { 'active': 1 }, name: 'active_idx' },
          { key: { 'updatedAt': -1 }, name: 'updated_at_idx' }
        ]
      },
      {
        name: 'executions',
        indexes: [
          { key: { 'workflowId': 1 }, name: 'workflow_id_idx' },
          { key: { 'startedAt': -1 }, name: 'started_at_idx' },
          { key: { 'status': 1 }, name: 'status_idx' }
        ]
      }
    ]
  },
  {
    name: 'litellm',
    description: 'LiteLLM proxy database for model management and logging',
    collections: [
      {
        name: 'requests',
        indexes: [
          { key: { 'model': 1 }, name: 'model_idx' },
          { key: { 'timestamp': -1 }, name: 'timestamp_idx' },
          { key: { 'user_id': 1 }, name: 'user_id_idx' },
          { key: { 'cost': 1 }, name: 'cost_idx' },
          { key: { 'status': 1 }, name: 'status_idx' }
        ]
      },
      {
        name: 'models',
        indexes: [
          { key: { 'model_name': 1 }, name: 'model_name_idx', unique: true },
          { key: { 'provider': 1 }, name: 'provider_idx' },
          { key: { 'active': 1 }, name: 'active_idx' }
        ]
      },
      {
        name: 'cost_tracking',
        indexes: [
          { key: { 'date': -1 }, name: 'date_idx' },
          { key: { 'model': 1, 'date': -1 }, name: 'model_date_idx' },
          { key: { 'user_id': 1, 'date': -1 }, name: 'user_date_idx' }
        ]
      }
    ]
  },
  {
    name: 'openwebui',
    description: 'OpenWebUI chat interface database',
    collections: [
      {
        name: 'chats',
        indexes: [
          { key: { 'user_id': 1 }, name: 'user_id_idx' },
          { key: { 'created_at': -1 }, name: 'created_at_idx' },
          { key: { 'title': 'text' }, name: 'title_text_idx' }
        ]
      },
      {
        name: 'messages',
        indexes: [
          { key: { 'chat_id': 1 }, name: 'chat_id_idx' },
          { key: { 'timestamp': -1 }, name: 'timestamp_idx' },
          { key: { 'role': 1 }, name: 'role_idx' }
        ]
      }
    ]
  },
  {
    name: 'lobechat',
    description: 'LobeChat interface database',
    collections: [
      {
        name: 'sessions',
        indexes: [
          { key: { 'user_id': 1 }, name: 'user_id_idx' },
          { key: { 'updated_at': -1 }, name: 'updated_at_idx' },
          { key: { 'agent_id': 1 }, name: 'agent_id_idx' }
        ]
      },
      {
        name: 'agents',
        indexes: [
          { key: { 'name': 1 }, name: 'name_idx' },
          { key: { 'created_by': 1 }, name: 'created_by_idx' },
          { key: { 'public': 1 }, name: 'public_idx' }
        ]
      }
    ]
  },
  {
    name: 'archon_mcp',
    description: 'Archon MCP knowledge management database',
    collections: [
      {
        name: 'knowledge_items',
        indexes: [
          { key: { 'type': 1 }, name: 'type_idx' },
          { key: { 'created_at': -1 }, name: 'created_at_idx' },
          { key: { 'tags': 1 }, name: 'tags_idx' },
          { key: { 'title': 'text', 'content': 'text' }, name: 'text_search_idx' }
        ]
      },
      {
        name: 'tasks',
        indexes: [
          { key: { 'status': 1 }, name: 'status_idx' },
          { key: { 'priority': 1 }, name: 'priority_idx' },
          { key: { 'due_date': 1 }, name: 'due_date_idx' },
          { key: { 'assigned_to': 1 }, name: 'assigned_to_idx' }
        ]
      }
    ]
  }
];

// Function to create database and collections
function createDatabase(dbConfig) {
  print(`Creating database: ${dbConfig.name}`);
  
  // Switch to the target database
  const targetDb = db.getSiblingDB(dbConfig.name);
  
  // Create collections with indexes
  dbConfig.collections.forEach(collection => {
    print(`  Creating collection: ${collection.name}`);
    
    // Create the collection
    targetDb.createCollection(collection.name);
    
    // Create indexes
    if (collection.indexes && collection.indexes.length > 0) {
      collection.indexes.forEach(index => {
        print(`    Creating index: ${index.name}`);
        try {
          targetDb[collection.name].createIndex(index.key, {
            name: index.name,
            unique: index.unique || false,
            expireAfterSeconds: index.expireAfterSeconds
          });
        } catch (error) {
          print(`    Warning: Could not create index ${index.name}: ${error.message}`);
        }
      });
    }
  });
  
  // Insert a metadata document to track database initialization
  targetDb.db_metadata.insertOne({
    database_name: dbConfig.name,
    description: dbConfig.description,
    initialized_at: new Date(),
    version: "1.0.0",
    collections: dbConfig.collections.map(c => c.name)
  });
  
  print(`Database ${dbConfig.name} created successfully`);
}

// Create all databases
print("Starting MongoDB multi-database initialization...");
databases.forEach(createDatabase);
print("MongoDB multi-database initialization completed!");

// Create a monitoring collection in admin database
db = db.getSiblingDB('admin');
db.database_init_log.insertOne({
  event: 'multi_database_init_completed',
  timestamp: new Date(),
  databases_created: databases.map(d => d.name),
  total_databases: databases.length
});

print("Initialization log created in admin database");
