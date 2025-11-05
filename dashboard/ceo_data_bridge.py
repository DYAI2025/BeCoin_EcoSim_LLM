"""
CEO Discovery Data Bridge

Reads and formats CEO Discovery session data for API consumption.
This module bridges between the file-based discovery session storage
and the FastAPI endpoints that serve the dashboard.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CEODataBridge:
    """Reads and formats CEO Discovery session data for API consumption"""

    def __init__(self, discovery_sessions_path: str = "../.claude-flow/discovery-sessions"):
        """
        Initialize the data bridge.

        Args:
            discovery_sessions_path: Path to directory containing discovery session JSON files
        """
        self.sessions_path = Path(discovery_sessions_path)
        self._cache = {}
        self._cache_ttl = 30  # seconds

    def get_current_session(self) -> Dict:
        """
        Get the most recent discovery session.

        Returns:
            Dict containing session data or empty session if none found
        """
        try:
            if not self.sessions_path.exists():
                return self._empty_session()

            # Find most recent session file
            session_files = list(self.sessions_path.glob("discovery-*.json"))
            if not session_files:
                return self._empty_session()

            latest_file = max(session_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file) as f:
                data = json.load(f)

            return data

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading discovery session: {e}")
            return self._empty_session()

    def get_proposals(self, min_roi: float = 0.0, limit: int = 10) -> List[Dict]:
        """
        Get proposals filtered by ROI.

        Args:
            min_roi: Minimum ROI threshold (default: 0.0)
            limit: Maximum number of proposals to return (default: 10)

        Returns:
            List of proposal dicts sorted by ROI descending
        """
        session = self.get_current_session()
        proposals = session.get("proposals", [])

        # Filter by ROI
        filtered = [p for p in proposals if p.get("roi", 0) >= min_roi]

        # Sort by ROI descending
        filtered.sort(key=lambda p: p.get("roi", 0), reverse=True)

        return filtered[:limit]

    def get_patterns(self, pattern_type: Optional[str] = None) -> List[Dict]:
        """
        Get identified patterns, optionally filtered by type.

        Args:
            pattern_type: Filter by pattern type (e.g., 'repetitive', 'error', 'bottleneck')
                         If None, returns all patterns

        Returns:
            List of pattern dicts
        """
        session = self.get_current_session()
        patterns = session.get("patterns", [])

        if pattern_type:
            patterns = [p for p in patterns if p.get("type") == pattern_type]

        return patterns

    def get_pain_points(self) -> List[Dict]:
        """
        Get all identified pain points.

        Returns:
            List of pain point dicts
        """
        session = self.get_current_session()
        return session.get("pain_points", [])

    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        Get historical discovery sessions.

        Args:
            limit: Maximum number of sessions to return (default: 10)

        Returns:
            List of session summaries sorted by date descending
        """
        try:
            if not self.sessions_path.exists():
                return []

            session_files = sorted(
                self.sessions_path.glob("discovery-*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            sessions = []
            for session_file in session_files[:limit]:
                try:
                    with open(session_file) as f:
                        data = json.load(f)

                    # Create summary
                    summary = {
                        "session_id": data.get("session_id"),
                        "start_time": data.get("start_time"),
                        "status": data.get("status"),
                        "pattern_count": len(data.get("patterns", [])),
                        "proposal_count": len(data.get("proposals", []))
                    }
                    sessions.append(summary)

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Skipping invalid session file {session_file}: {e}")
                    continue

            return sessions

        except Exception as e:
            logger.error(f"Error reading session history: {e}")
            return []

    def _empty_session(self) -> Dict:
        """
        Return an empty/idle session structure.

        Returns:
            Dict with idle session structure
        """
        return {
            "session_id": None,
            "start_time": None,
            "status": "idle",
            "patterns": [],
            "pain_points": [],
            "proposals": []
        }
