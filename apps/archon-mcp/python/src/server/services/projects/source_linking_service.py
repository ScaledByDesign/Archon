"""
Source Linking Service Module for Archon

This module provides centralized logic for managing project-source relationships,
handling both technical and business source associations.
"""

# Removed direct logging import - using unified config
from typing import Any

from src.server.utils import get_supabase_client

from ...config.logfire_config import get_logger
from ..cache_service import get_cache_service

logger = get_logger(__name__)


class SourceLinkingService:
    """Service class for managing project-source relationships"""

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client"""
        self.supabase_client = supabase_client or get_supabase_client()
        self._cache_service = None

    async def _get_cache_service(self):
        """Get cache service instance (lazy initialization)"""
        if self._cache_service is None:
            self._cache_service = await get_cache_service()
        return self._cache_service

    async def get_project_sources(self, project_id: str) -> tuple[bool, dict[str, list[str]]]:
        """
        Get all linked sources for a project, separated by type with Redis caching.

        Returns:
            Tuple of (success, {"technical_sources": [...], "business_sources": [...]})
        """
        try:
            # Try to get from cache first
            cache_service = await self._get_cache_service()
            cached_result = await cache_service.get("project_sources", project_id)

            if cached_result is not None:
                logger.debug(f"Project sources for {project_id} retrieved from cache")
                return True, cached_result

            # Cache miss - fetch from database
            logger.debug(f"Project sources for {project_id} cache miss - fetching from database")
            response = (
                self.supabase_client.table("archon_project_sources")
                .select("source_id, notes")
                .eq("project_id", project_id)
                .execute()
            )

            technical_sources = []
            business_sources = []

            for source_link in response.data:
                if source_link.get("notes") == "technical":
                    technical_sources.append(source_link["source_id"])
                elif source_link.get("notes") == "business":
                    business_sources.append(source_link["source_id"])

            result = {
                "technical_sources": technical_sources,
                "business_sources": business_sources,
            }

            # Cache the result
            await cache_service.set("project_sources", project_id, result)
            logger.debug(f"Cached project sources for {project_id}")

            return True, result
        except Exception as e:
            logger.error(f"Error getting project sources: {e}")
            return False, {
                "error": f"Failed to retrieve linked sources: {str(e)}",
                "technical_sources": [],
                "business_sources": [],
            }

    def update_project_sources(
        self,
        project_id: str,
        technical_sources: list[str] | None = None,
        business_sources: list[str] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Update project sources, replacing existing ones if provided.

        Returns:
            Tuple of (success, result_dict with counts)
        """
        result = {
            "technical_success": 0,
            "technical_failed": 0,
            "business_success": 0,
            "business_failed": 0,
        }

        try:
            # Update technical sources if provided
            if technical_sources is not None:
                # Remove existing technical sources
                self.supabase_client.table("archon_project_sources").delete().eq(
                    "project_id", project_id
                ).eq("notes", "technical").execute()

                # Add new technical sources
                for source_id in technical_sources:
                    try:
                        self.supabase_client.table("archon_project_sources").insert({
                            "project_id": project_id,
                            "source_id": source_id,
                            "notes": "technical",
                        }).execute()
                        result["technical_success"] += 1
                    except Exception as e:
                        result["technical_failed"] += 1
                        logger.warning(f"Failed to link technical source {source_id}: {e}")

            # Update business sources if provided
            if business_sources is not None:
                # Remove existing business sources
                self.supabase_client.table("archon_project_sources").delete().eq(
                    "project_id", project_id
                ).eq("notes", "business").execute()

                # Add new business sources
                for source_id in business_sources:
                    try:
                        self.supabase_client.table("archon_project_sources").insert({
                            "project_id": project_id,
                            "source_id": source_id,
                            "notes": "business",
                        }).execute()
                        result["business_success"] += 1
                    except Exception as e:
                        result["business_failed"] += 1
                        logger.warning(f"Failed to link business source {source_id}: {e}")

            # Overall success if no critical failures
            total_failed = result["technical_failed"] + result["business_failed"]

            return True, result

        except Exception as e:
            logger.error(f"Error updating project sources: {e}")
            return False, {"error": str(e), **result}

    async def format_project_with_sources(self, project: dict[str, Any]) -> dict[str, Any]:
        """
        Format a project dict with its linked sources included.
        Also handles datetime conversion for Socket.IO compatibility.

        Returns:
            Formatted project dict with technical_sources and business_sources
        """
        # Get linked sources (now async)
        try:
            success, sources = await self.get_project_sources(project["id"])
            if not success:
                logger.warning(f"Failed to get sources for project {project['id']}")
                sources = {"technical_sources": [], "business_sources": []}
        except Exception as e:
            logger.warning(f"Error getting sources for project {project['id']}: {e}")
            sources = {"technical_sources": [], "business_sources": []}

        # Ensure datetime objects are converted to strings
        created_at = project.get("created_at", "")
        updated_at = project.get("updated_at", "")
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()
        if hasattr(updated_at, "isoformat"):
            updated_at = updated_at.isoformat()

        return {
            "id": project["id"],
            "title": project["title"],
            "description": project.get("description", ""),
            "github_repo": project.get("github_repo"),
            "created_at": created_at,
            "updated_at": updated_at,
            "docs": project.get("docs", []),
            "features": project.get("features", []),
            "data": project.get("data", []),
            "technical_sources": sources["technical_sources"],
            "business_sources": sources["business_sources"],
            "pinned": project.get("pinned", False),
        }

    async def format_projects_with_sources(self, projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Format a list of projects with their linked sources.

        Returns:
            List of formatted project dicts
        """
        formatted_projects = []
        for project in projects:
            formatted_project = await self.format_project_with_sources(project)
            formatted_projects.append(formatted_project)
        return formatted_projects

    async def invalidate_project_sources_cache(self, project_id: str = None):
        """
        Invalidate project sources cache entries.

        Args:
            project_id: Specific project ID to invalidate, or None to invalidate all
        """
        try:
            cache_service = await self._get_cache_service()

            if project_id:
                # Invalidate specific project sources
                await cache_service.delete("project_sources", project_id)
                logger.debug(f"Invalidated project sources cache for {project_id}")
            else:
                # Invalidate all project sources cache
                await cache_service.invalidate_category("project_sources")
                logger.debug("Invalidated all project sources cache")

        except Exception as e:
            logger.warning(f"Failed to invalidate project sources cache: {e}")
