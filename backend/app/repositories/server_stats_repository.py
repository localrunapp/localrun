"""
Server Stats Repository
Handles storage and retrieval of server statistics using TinyDB.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from tinydb import TinyDB, Query
import os


class ServerStatsRepository:
    """
    Manages stats storage per server using TinyDB.
    Retains 2 weeks of data with automatic rotation.
    """

    def __init__(self, data_dir: str = "database/stats"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.retention_days = 14

    def _get_db(self, server_id: str) -> TinyDB:
        """Get TinyDB instance for a specific server."""
        db_path = os.path.join(self.data_dir, f"{server_id}.json")
        return TinyDB(db_path)

    def add_stats(self, server_id: str, stats: Dict[str, Any]):
        """Add stats entry and clean old data."""
        db = self._get_db(server_id)

        # Add timestamp if not present
        if "timestamp" not in stats:
            stats["timestamp"] = datetime.utcnow().isoformat()

        # Insert new stats
        db.insert(stats)

        # Clean old data (older than retention period)
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        cutoff_str = cutoff.isoformat()

        StatsQuery = Query()
        db.remove(StatsQuery.timestamp < cutoff_str)

        db.close()

    def get_stats(self, server_id: str, hours: int = 168) -> List[Dict[str, Any]]:
        """Get stats for the last N hours (default 1 week)."""
        db = self._get_db(server_id)

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        StatsQuery = Query()
        results = db.search(StatsQuery.timestamp >= cutoff_str)

        db.close()

        # Sort by timestamp
        return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)

    def get_latest(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent stats entry."""
        db = self._get_db(server_id)
        all_stats = db.all()
        db.close()

        if not all_stats:
            return None

        # Return the most recent
        return max(all_stats, key=lambda x: x.get("timestamp", ""))


# Singleton instance
server_stats_repository = ServerStatsRepository()
