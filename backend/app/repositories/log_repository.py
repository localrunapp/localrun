"""
Log Repository for LocalRun
Handles centralized logging with TinyDB storage and automatic TTL cleanup.
"""

from tinydb import TinyDB, Query
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class LogRepository:
    """
    Repository for log storage and retrieval using TinyDB.
    Supports multiple log categories with automatic 7-day TTL cleanup.
    """

    CATEGORIES = ["metrics", "websocket", "services", "backend", "agents"]
    LEVELS = ["info", "warning", "error"]
    TTL_DAYS = 7

    def __init__(self, db_path: str = "/app/database/logs.json"):
        """Initialize log repository with TinyDB storage."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(str(self.db_path))
        logger.info(f"LogRepository initialized with database at {self.db_path}")

    def log(
        self,
        category: str,
        level: str,
        message: str,
        server_id: Optional[str] = None,
        server_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a log entry.

        Args:
            category: Log category (metrics, websocket, services, backend)
            level: Log level (info, warning, error)
            message: Log message
            server_id: Optional server ID
            server_name: Optional server name
            metadata: Optional additional metadata

        Returns:
            Log entry ID
        """
        if category not in self.CATEGORIES:
            logger.warning(f"Invalid log category: {category}")
            category = "backend"

        if level not in self.LEVELS:
            logger.warning(f"Invalid log level: {level}")
            level = "info"

        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": category,
            "level": level,
            "server_id": server_id,
            "server_name": server_name,
            "message": message,
            "metadata": metadata or {},
        }

        self.db.insert(log_entry)

        # Cleanup old logs periodically (every 100 inserts)
        if len(self.db) % 100 == 0:
            self.cleanup_old_logs()

        return log_entry["id"]

    def get_logs(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        server_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get logs with optional filtering.

        Args:
            category: Filter by category
            level: Filter by level
            server_id: Filter by server ID
            limit: Maximum number of logs to return
            offset: Offset for pagination

        Returns:
            List of log entries
        """
        LogEntry = Query()
        query_conditions = []

        if category:
            query_conditions.append(LogEntry.category == category)
        if level:
            query_conditions.append(LogEntry.level == level)
        if server_id:
            query_conditions.append(LogEntry.server_id == server_id)

        if query_conditions:
            # Combine all conditions with AND
            combined_query = query_conditions[0]
            for condition in query_conditions[1:]:
                combined_query &= condition
            results = self.db.search(combined_query)
        else:
            results = self.db.all()

        # Sort by timestamp descending (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Apply pagination
        return results[offset : offset + limit]

    def get_recent_logs(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Get logs from the last N minutes.

        Args:
            minutes: Number of minutes to look back

        Returns:
            List of recent log entries
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        cutoff_str = cutoff.isoformat() + "Z"

        LogEntry = Query()
        results = self.db.search(LogEntry.timestamp >= cutoff_str)

        # Sort by timestamp descending
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return results

    def cleanup_old_logs(self) -> int:
        """
        Remove logs older than TTL_DAYS.

        Returns:
            Number of logs removed
        """
        cutoff = datetime.utcnow() - timedelta(days=self.TTL_DAYS)
        cutoff_str = cutoff.isoformat() + "Z"

        LogEntry = Query()
        removed = self.db.remove(LogEntry.timestamp < cutoff_str)

        if removed:
            logger.info(f"Cleaned up {len(removed)} old log entries")

        return len(removed) if removed else 0

    def get_logs_paginated(
        self,
        search: Optional[str] = None,
        categories: Optional[List[str]] = None,
        levels: Optional[List[str]] = None,
        server_id: Optional[str] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get logs with advanced filtering, search, sorting, and pagination.

        Args:
            search: Search term to find in message, server_name, category, level, or metadata
            categories: List of categories to filter by (OR logic)
            levels: List of levels to filter by (OR logic)
            server_id: Filter by specific server ID
            sort_by: Field to sort by (timestamp, category, level, server_name, message, server_id)
            sort_order: Sort order ('asc' or 'desc')
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with paginated results and metadata
        """
        LogEntry = Query()
        query_conditions = []

        # Build filter conditions
        if categories:
            # OR logic for categories
            category_conditions = [LogEntry.category == cat for cat in categories]
            if len(category_conditions) == 1:
                query_conditions.append(category_conditions[0])
            else:
                combined = category_conditions[0]
                for cond in category_conditions[1:]:
                    combined |= cond
                query_conditions.append(combined)

        if levels:
            # OR logic for levels
            level_conditions = [LogEntry.level == lvl for lvl in levels]
            if len(level_conditions) == 1:
                query_conditions.append(level_conditions[0])
            else:
                combined = level_conditions[0]
                for cond in level_conditions[1:]:
                    combined |= cond
                query_conditions.append(combined)

        if server_id:
            query_conditions.append(LogEntry.server_id == server_id)

        # Execute query with filters
        if query_conditions:
            combined_query = query_conditions[0]
            for condition in query_conditions[1:]:
                combined_query &= condition
            results = self.db.search(combined_query)
        else:
            results = self.db.all()

        # Apply search filter (cross-field search)
        if search:
            search_lower = search.lower()
            filtered_results = []
            
            for log in results:
                # Search in message
                if search_lower in log.get("message", "").lower():
                    filtered_results.append(log)
                    continue
                
                # Search in server_name
                server_name = log.get("server_name")
                if server_name and search_lower in server_name.lower():
                    filtered_results.append(log)
                    continue
                
                # Search in category
                if search_lower in log.get("category", "").lower():
                    filtered_results.append(log)
                    continue
                
                # Search in level
                if search_lower in log.get("level", "").lower():
                    filtered_results.append(log)
                    continue
                
                # Search in metadata (convert to string)
                metadata = log.get("metadata", {})
                if metadata:
                    metadata_str = str(metadata).lower()
                    if search_lower in metadata_str:
                        filtered_results.append(log)
                        continue
            
            results = filtered_results

        # Get total count before pagination
        total = len(results)

        # Apply sorting
        reverse = sort_order == "desc"
        
        # Handle None values in sorting
        def get_sort_key(log):
            value = log.get(sort_by)
            # Put None values at the end
            if value is None:
                return ("", "") if not reverse else ("zzz", "zzz")
            return (str(value).lower() if isinstance(value, str) else value, "")
        
        try:
            results.sort(key=get_sort_key, reverse=reverse)
        except Exception as e:
            logger.warning(f"Error sorting by {sort_by}: {e}. Falling back to timestamp sort.")
            results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        offset = (page - 1) * page_size
        
        # Get page items
        items = results[offset : offset + page_size]

        # Build response
        return {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "filters": {
                "search": search,
                "categories": categories,
                "levels": levels,
                "server_id": server_id,
                "sort_by": sort_by,
                "sort_order": sort_order,
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored logs.

        Returns:
            Dictionary with log statistics
        """
        all_logs = self.db.all()

        stats = {
            "total_logs": len(all_logs),
            "by_category": {},
            "by_level": {},
            "oldest_log": None,
            "newest_log": None,
        }

        # Count by category and level
        for log in all_logs:
            category = log.get("category", "unknown")
            level = log.get("level", "unknown")

            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

        # Get oldest and newest
        if all_logs:
            sorted_logs = sorted(all_logs, key=lambda x: x.get("timestamp", ""))
            stats["oldest_log"] = sorted_logs[0].get("timestamp")
            stats["newest_log"] = sorted_logs[-1].get("timestamp")

        return stats

    def clear_all_logs(self) -> int:
        """
        Clear all logs (use with caution).

        Returns:
            Number of logs removed
        """
        count = len(self.db)
        self.db.truncate()
        logger.warning(f"Cleared all {count} log entries")
        return count


# Global log repository instance
log_manager = LogRepository()

