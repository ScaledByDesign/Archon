-- PostgreSQL Bootstrap Script
-- Creates additional extensions and configurations for Zoi services

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create additional schemas for organization
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant permissions
GRANT USAGE ON SCHEMA monitoring TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;

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

-- Bootstrap completion log
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- Log completion
\echo 'PostgreSQL bootstrap completed successfully!'
