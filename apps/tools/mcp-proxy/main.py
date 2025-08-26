#!/usr/bin/env python3
"""
Simple MCP Proxy Service

This service acts as a bridge between LobeChat and the Archon MCP server,
bypassing the MCP protocol session management issues by providing direct HTTP endpoints.
"""

import httpx
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Proxy Service",
    description="HTTP proxy for Archon MCP tools",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
ARCHON_SERVER_URL = "http://archon-server:7081"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-proxy"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-proxy"}

@app.get("/api/projects")
async def list_projects():
    """
    Get a simplified list of projects directly from Archon API
    This bypasses the MCP protocol entirely
    """
    try:
        logger.info("🚀 Fetching projects from Archon API")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ARCHON_SERVER_URL}/api/projects")
            
            if response.status_code == 200:
                projects = response.json()
                logger.info(f"✅ Retrieved {len(projects)} projects")
                
                # Create ultra-minimal project list
                minimal_projects = []
                for i, project in enumerate(projects[:5]):  # Limit to first 5
                    title = project.get("title", "")
                    if len(title) > 30:
                        title = title[:27] + "..."
                    
                    minimal_projects.append({
                        "id": project.get("id"),
                        "title": title,
                        "created_at": project.get("created_at", ""),
                        "pinned": project.get("pinned", False)
                    })
                
                result = {
                    "success": True,
                    "projects": minimal_projects,
                    "total_count": len(projects),
                    "showing": len(minimal_projects)
                }
                
                logger.info(f"✅ Returning {len(minimal_projects)} minimal projects")
                return result
                
            else:
                logger.error(f"❌ API request failed: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch projects: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"❌ Network error: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project by ID"""
    try:
        logger.info(f"🚀 Fetching project {project_id} from Archon API")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ARCHON_SERVER_URL}/api/projects/{project_id}")
            
            if response.status_code == 200:
                project = response.json()
                logger.info(f"✅ Retrieved project: {project.get('title', 'Unknown')}")
                
                # Return minimal project info
                result = {
                    "success": True,
                    "project": {
                        "id": project.get("id"),
                        "title": project.get("title"),
                        "description": project.get("description", "")[:200] + "..." if len(project.get("description", "")) > 200 else project.get("description", ""),
                        "created_at": project.get("created_at"),
                        "updated_at": project.get("updated_at"),
                        "pinned": project.get("pinned", False),
                        "status": project.get("status", "active")
                    }
                }
                
                return result
                
            else:
                logger.error(f"❌ Project not found: {project_id}")
                raise HTTPException(status_code=404, detail="Project not found")
                
    except httpx.RequestError as e:
        logger.error(f"❌ Network error: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
