-- PostgreSQL Bootstrap Script
-- Creates additional extensions and configurations for Zoi services

-- Core extensions for UUID generation and text processing
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- JSON/JSONB extensions for modern app data
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Full-text search for chat/content applications
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Vector similarity for AI/ML workloads
CREATE EXTENSION IF NOT EXISTS "vector";

-- Crypto functions for authentication systems
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create additional schemas for organization
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS shared;

-- Grant permissions
GRANT USAGE ON SCHEMA monitoring TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;
GRANT USAGE ON SCHEMA shared TO postgres;

-- Performance tuning for AI/ML workloads
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Create a view for database sizes (useful for monitoring)
CREATE OR REPLACE VIEW monitoring.database_sizes AS
SELECT 
    datname as database_name,
    pg_size_pretty(pg_database_size(datname)) as size,
    pg_database_size(datname) as size_bytes
FROM pg_database 
WHERE datistemplate = false
ORDER BY pg_database_size(datname) DESC;

-- Create a view for active connections
CREATE OR REPLACE VIEW monitoring.active_connections AS
SELECT 
    datname as database,
    usename as username,
    client_addr,
    state,
    query_start,
    now() - query_start as duration
FROM pg_stat_activity 
WHERE state != 'idle'
ORDER BY query_start;

-- Create shared utility functions for Zoi services
CREATE OR REPLACE FUNCTION shared.generate_api_key(length INTEGER DEFAULT 32)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(gen_random_bytes(length), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Vector similarity search function
CREATE OR REPLACE FUNCTION shared.cosine_similarity(a vector, b vector)
RETURNS FLOAT AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql;

-- Create a shared embeddings table for cross-service use
CREATE TABLE IF NOT EXISTS shared.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL,
    content_id TEXT NOT NULL,
    content_text TEXT,
    embedding vector(1536), -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_service ON shared.embeddings(service_name);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_id ON shared.embeddings(content_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON shared.embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata ON shared.embeddings USING gin(metadata);

-- Create function to clean old session data (useful for auth services)
CREATE OR REPLACE FUNCTION shared.cleanup_old_sessions(days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- This is a template - each service can customize for their session tables
    -- DELETE FROM authentik_sessions WHERE created_at < NOW() - INTERVAL '%s days', days;
    -- GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN 0; -- Placeholder
END;
$$ LANGUAGE plpgsql;

-- Vector similarity search function
CREATE OR REPLACE FUNCTION shared.similarity_search(
    query_embedding vector(1536),
    service_filter TEXT DEFAULT NULL,
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    service_name TEXT,
    content_id TEXT,
    content_text TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.service_name,
        e.content_id,
        e.content_text,
        shared.cosine_similarity(e.embedding, query_embedding) as similarity,
        e.metadata
    FROM shared.embeddings e
    WHERE
        (service_filter IS NULL OR e.service_name = service_filter)
        AND shared.cosine_similarity(e.embedding, query_embedding) >= similarity_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to upsert embeddings
CREATE OR REPLACE FUNCTION shared.upsert_embedding(
    p_service_name TEXT,
    p_content_id TEXT,
    p_content_text TEXT,
    p_embedding vector(1536),
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    result_id UUID;
BEGIN
    INSERT INTO shared.embeddings (service_name, content_id, content_text, embedding, metadata)
    VALUES (p_service_name, p_content_id, p_content_text, p_embedding, p_metadata)
    ON CONFLICT (service_name, content_id)
    DO UPDATE SET
        content_text = EXCLUDED.content_text,
        embedding = EXCLUDED.embedding,
        metadata = EXCLUDED.metadata,
        updated_at = NOW()
    RETURNING id INTO result_id;

    RETURN result_id;
END;
$$ LANGUAGE plpgsql;

-- Add unique constraint for service + content_id
ALTER TABLE shared.embeddings ADD CONSTRAINT unique_service_content
    UNIQUE (service_name, content_id);

-- Create monitoring function for database health
CREATE OR REPLACE FUNCTION monitoring.health_check()
RETURNS TABLE(
    metric TEXT,
    value TEXT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'active_connections'::TEXT,
        COUNT(*)::TEXT,
        CASE WHEN COUNT(*) < 50 THEN 'OK' ELSE 'WARNING' END
    FROM pg_stat_activity
    WHERE state = 'active'

    UNION ALL

    SELECT
        'database_size_mb'::TEXT,
        ROUND(SUM(pg_database_size(datname))/1024/1024)::TEXT,
        'OK'::TEXT
    FROM pg_database
    WHERE datistemplate = false;
END;
$$ LANGUAGE plpgsql;

-- Log completion
\echo 'PostgreSQL bootstrap completed successfully!'
\echo 'Extensions: uuid-ossp, pg_trgm, unaccent, btree_gin, btree_gist, vector, pgcrypto'
\echo 'Schemas: monitoring, analytics, shared'
\echo 'Vector embeddings table created with similarity search functions'
\echo 'Performance tuning applied for AI/ML workloads'
\echo 'Ready for vector similarity search and embeddings storage!'
