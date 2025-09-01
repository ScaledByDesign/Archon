#!/bin/bash
set -e

echo "=== Refact Server with PostgreSQL Integration ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "${REFACT_DATABASE_HOST:-postgres}" -p "${REFACT_DATABASE_PORT:-5432}" -U "${REFACT_DATABASE_USER:-postgres}"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
until redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "✅ Redis is ready!"

# Create necessary directories
mkdir -p "${REFACT_PERM_DIR}/logs"
mkdir -p "${REFACT_PERM_DIR}/models"
mkdir -p "${REFACT_PERM_DIR}/cache"

# Set up database connection environment variables for Refact
export DATABASE_URL="postgresql://${REFACT_DATABASE_USER:-postgres}:${REFACT_DATABASE_PASSWORD:-litellm_password123}@${REFACT_DATABASE_HOST:-postgres}:${REFACT_DATABASE_PORT:-5432}/${REFACT_DATABASE_NAME:-refact}"

# Initialize database schema if needed
echo "Initializing Refact database schema..."
python3 -c "
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.environ.get('REFACT_DATABASE_HOST', 'postgres'),
    port=os.environ.get('REFACT_DATABASE_PORT', '5432'),
    user=os.environ.get('REFACT_DATABASE_USER', 'postgres'),
    password=os.environ.get('REFACT_DATABASE_PASSWORD', 'litellm_password123'),
    database=os.environ.get('REFACT_DATABASE_NAME', 'refact')
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

# Create Refact-specific tables
print('Creating Refact database schema...')

# Users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE,
        api_key VARCHAR(255) UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
''')

# Models table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS models (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        model_type VARCHAR(100) NOT NULL,
        config JSONB DEFAULT '{}',
        status VARCHAR(50) DEFAULT 'inactive',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
''')

# Chat sessions table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id INTEGER REFERENCES users(id),
        title VARCHAR(500),
        messages JSONB DEFAULT '[]',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
''')

# Code completions table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS code_completions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id INTEGER REFERENCES users(id),
        file_path VARCHAR(1000),
        language VARCHAR(100),
        context_before TEXT,
        context_after TEXT,
        completion TEXT,
        accepted BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
''')

# Embeddings table for code search
cursor.execute('''
    CREATE TABLE IF NOT EXISTS code_embeddings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        file_path VARCHAR(1000) NOT NULL,
        content_hash VARCHAR(64) NOT NULL,
        content TEXT,
        embedding vector(1536),
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
''')

# Create indexes
cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_completions_user_id ON code_completions(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_completions_file_path ON code_completions(file_path)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_embeddings_file_path ON code_embeddings(file_path)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_embeddings_content_hash ON code_embeddings(content_hash)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_embeddings_vector ON code_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')

# Insert default admin user if not exists
cursor.execute('''
    INSERT INTO users (username, email, api_key)
    VALUES ('admin', 'admin@refact.local', %s)
    ON CONFLICT (username) DO NOTHING
''', (os.environ.get('REFACT_ADMIN_TOKEN', 'refact-admin-token-change-me'),))

print('✅ Refact database schema initialized successfully!')

cursor.close()
conn.close()
"

# Set up configuration for PostgreSQL backend
echo "Configuring Refact for PostgreSQL backend..."

# Create configuration file
cat > "${REFACT_PERM_DIR}/refact_config.json" << EOF
{
    "database": {
        "type": "postgresql",
        "host": "${REFACT_DATABASE_HOST:-postgres}",
        "port": ${REFACT_DATABASE_PORT:-5432},
        "database": "${REFACT_DATABASE_NAME:-refact}",
        "user": "${REFACT_DATABASE_USER:-postgres}",
        "password": "${REFACT_DATABASE_PASSWORD:-litellm_password123}"
    },
    "redis": {
        "host": "${REDIS_HOST:-redis}",
        "port": ${REDIS_PORT:-6379}
    },
    "litellm": {
        "base_url": "${LITELLM_BASE_URL:-http://litellm:4000}",
        "api_key": "${LITELLM_API_KEY:-sk-wqn0xwq_vha4MVM2yzw}"
    },
    "models_path": "${MODELS_PATH:-/models}",
    "admin_token": "${REFACT_ADMIN_TOKEN:-refact-admin-token-change-me}"
}
EOF

echo "✅ Refact configuration created at ${REFACT_PERM_DIR}/refact_config.json"

# Start the Refact server
echo "Starting Refact server with PostgreSQL backend..."
exec python -m self_hosting_machinery.watchdog.docker_watchdog
