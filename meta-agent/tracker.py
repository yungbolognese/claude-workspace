#!/usr/bin/env python3
"""
Lightweight Activity Tracker for Claude Code Meta-Agent
Logs Claude Code activities with minimal overhead using append-only JSON
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class ActivityTracker:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Current session log
        self.session_file = self.logs_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

        # Activity hash index for deduplication (in-memory, lightweight)
        self.activity_hashes = set()
        self._load_recent_hashes()

    def _load_recent_hashes(self):
        """Load hashes from last 7 days for lightweight deduplication"""
        index_file = self.logs_dir / "activity_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    cutoff = (datetime.now().timestamp() - 7 * 24 * 3600)
                    self.activity_hashes = {
                        h for h, ts in data.items()
                        if ts > cutoff
                    }
            except:
                self.activity_hashes = set()

    def _save_hash_index(self):
        """Persist activity hashes with timestamps"""
        index_file = self.logs_dir / "activity_index.json"
        data = {h: datetime.now().timestamp() for h in self.activity_hashes}
        with open(index_file, 'w') as f:
            json.dump(data, f)

    def _compute_hash(self, activity: Dict[str, Any]) -> str:
        """Compute lightweight hash of activity for deduplication"""
        # Hash based on type + key content only
        key_content = {
            "type": activity.get("type"),
            "action": activity.get("action"),
            "target": activity.get("target", ""),
            "pattern": activity.get("pattern", "")[:100]  # First 100 chars only
        }
        return hashlib.md5(json.dumps(key_content, sort_keys=True).encode()).hexdigest()

    def log_activity(self, activity_type: str, data: Dict[str, Any]) -> bool:
        """
        Log an activity. Returns True if this is a new pattern.

        Args:
            activity_type: One of 'command', 'code_edit', 'project_init', 'research'
            data: Activity-specific data
        """
        activity = {
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            **data
        }

        # Compute hash for deduplication
        activity_hash = self._compute_hash(activity)
        is_new = activity_hash not in self.activity_hashes

        # Always log to session file (for full history)
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(activity) + '\n')

        # Track hash if new
        if is_new:
            self.activity_hashes.add(activity_hash)
            if len(self.activity_hashes) % 50 == 0:  # Batch saves
                self._save_hash_index()

        return is_new

    def log_command_sequence(self, commands: List[str], context: str = ""):
        """Log a sequence of bash commands"""
        return self.log_activity("command", {
            "action": "sequence",
            "commands": commands,
            "context": context,
            "pattern": " && ".join(commands)
        })

    def log_code_change(self, file_path: str, change_type: str, description: str = ""):
        """Log a code modification pattern"""
        return self.log_activity("code_edit", {
            "action": change_type,
            "target": file_path,
            "description": description,
            "file_type": Path(file_path).suffix
        })

    def log_project_init(self, project_path: str, tech_stack: List[str], purpose: str = ""):
        """Log a new project initialization"""
        return self.log_activity("project_init", {
            "action": "create",
            "target": project_path,
            "tech_stack": tech_stack,
            "purpose": purpose
        })

    def log_research(self, topic: str, sources: List[str], outcome: str = ""):
        """Log a research/learning activity"""
        return self.log_activity("research", {
            "action": "lookup",
            "topic": topic,
            "sources": sources,
            "outcome": outcome
        })

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for current session"""
        stats = {
            "total_activities": 0,
            "by_type": {},
            "new_patterns": 0
        }

        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                for line in f:
                    activity = json.loads(line)
                    stats["total_activities"] += 1
                    atype = activity["type"]
                    stats["by_type"][atype] = stats["by_type"].get(atype, 0) + 1

        return stats

if __name__ == "__main__":
    # Simple CLI for manual logging
    import sys
    tracker = ActivityTracker()

    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            print(json.dumps(tracker.get_session_stats(), indent=2))
    else:
        print("Activity Tracker initialized")
        print(f"Session log: {tracker.session_file}")
