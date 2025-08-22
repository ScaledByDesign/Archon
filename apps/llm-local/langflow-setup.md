# 🌊 LangFlow Setup Guide

## Overview

LangFlow has been integrated into the Zoi AI stack as a visual AI workflow builder, replacing Flowise. LangFlow provides a more modern and flexible approach to building AI workflows with drag-and-drop components.

## Access

- **Local Development**: http://localhost:7070
- **Production**: http://langflow.zoi.local (with Authentik authentication)

## Features

- **Visual Workflow Builder**: Drag-and-drop interface for creating AI workflows
- **Component Library**: Extensive library of pre-built components
- **Custom Components**: Ability to create custom components
- **API Integration**: RESTful API for programmatic access
- **Database Persistence**: PostgreSQL backend for workflow storage
- **Redis Caching**: Enhanced performance with Redis caching

## Configuration

### Environment Variables

The LangFlow service is configured with the following environment variables:

- `LANGFLOW_HOST=0.0.0.0` - Host binding
- `LANGFLOW_PORT=7860` - Internal port
- `LANGFLOW_BACKEND_ONLY=false` - Enable full UI
- `LANGFLOW_DATABASE_URL` - PostgreSQL connection string
- `LANGFLOW_REDIS_URL` - Redis connection string
- `LANGFLOW_CACHE_TYPE=redis` - Use Redis for caching
- `LANGFLOW_LOG_LEVEL=INFO` - Logging level

### Database

LangFlow uses a dedicated PostgreSQL database (`langflow`) created automatically by the multi-database initialization script.

### Integration with Existing Services

LangFlow is integrated with:

- **LiteLLM**: Access to all configured AI models
- **Qdrant**: Vector database for RAG workflows
- **Redis**: Caching and session management
- **PostgreSQL**: Workflow and configuration persistence

## Getting Started

1. Start the LLM local stack:
   ```bash
   cd apps/llm-local
   docker-compose up -d
   ```

2. Access LangFlow at http://localhost:7070

3. Create your first workflow using the visual interface

4. Connect to LiteLLM models using the base URL: `http://litellm:4000/v1`

## Migration from Flowise

If you had existing Flowise workflows, you'll need to recreate them in LangFlow. The visual interface makes this process straightforward:

1. Review your existing Flowise configurations
2. Use LangFlow's component library to rebuild workflows
3. Test workflows with the integrated LiteLLM models
4. Save and deploy your new LangFlow workflows

## API Access

LangFlow provides a comprehensive API for programmatic access:

- **Base URL**: http://localhost:7070/api/v1
- **Documentation**: Available at http://localhost:7070/docs
- **Authentication**: Configured through environment variables

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running and the langflow database exists
2. **Redis Connection**: Verify Redis is accessible for caching
3. **Model Access**: Check LiteLLM connectivity for AI model access

### Logs

View LangFlow logs:
```bash
docker logs langflow
```

### Health Check

LangFlow includes a health check endpoint at `/health` for monitoring.
