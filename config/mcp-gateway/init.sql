-- MCP Gateway Database Initialization
-- This script sets up the initial database schema for MCP Context Forge Gateway

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- But we can set up additional configurations here

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance (these will be created by the application)
-- But we can prepare the database with optimal settings

-- Optimize PostgreSQL settings for MCP Gateway workload
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Create a user for the application (if needed)
-- The main user is created via POSTGRES_USER env var

-- Log successful initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- Create initial admin user token (this will be handled by the application)
-- But we can set up the database to be ready

COMMENT ON DATABASE mcp_gateway IS 'MCP Context Forge Gateway Database - Centralized tool management for Zoi AI system';
