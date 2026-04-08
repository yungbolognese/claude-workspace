#!/usr/bin/env python3
"""
Incremental Pattern Detector for Claude Code Meta-Agent
Analyzes activity logs to detect repetitive patterns worthy of skill creation
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
from difflib import SequenceMatcher

class PatternDetector:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.patterns_dir = self.base_dir / "patterns"
        self.patterns_dir.mkdir(exist_ok=True)

        # Pattern thresholds (lightweight)
        self.SIMILARITY_THRESHOLD = 0.7  # 70% similarity
        self.MIN_OCCURRENCES = 3  # Detect after 3 similar actions

        # Load known patterns
        self.known_patterns = self._load_known_patterns()

    def _load_known_patterns(self) -> Dict[str, Any]:
        """Load previously detected patterns"""
        patterns_file = self.patterns_dir / "detected_patterns.json"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_patterns(self):
        """Persist detected patterns"""
        patterns_file = self.patterns_dir / "detected_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(self.known_patterns, f, indent=2)

    def _similarity(self, str1: str, str2: str) -> float:
        """Compute similarity between two strings (lightweight)"""
        return SequenceMatcher(None, str1, str2).ratio()

    def _load_recent_activities(self, days: int = 7) -> List[Dict[str, Any]]:
        """Load activities from recent session logs"""
        activities = []
        cutoff = datetime.now() - timedelta(days=days)

        for log_file in sorted(self.logs_dir.glob("session_*.jsonl"), reverse=True):
            # Parse timestamp from filename
            try:
                ts_str = log_file.stem.replace("session_", "")
                file_time = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                if file_time < cutoff:
                    break
            except:
                continue

            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        activities.append(json.loads(line))
                    except:
                        continue

        return activities

    def detect_command_patterns(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect repetitive command sequences"""
        command_activities = [a for a in activities if a["type"] == "command"]

        patterns = []
        grouped_commands = defaultdict(list)

        # Group similar command patterns
        for activity in command_activities:
            pattern = activity.get("pattern", "")
            if not pattern:
                continue

            # Find similar existing group
            found_group = False
            for existing_pattern in list(grouped_commands.keys()):
                if self._similarity(pattern, existing_pattern) >= self.SIMILARITY_THRESHOLD:
                    grouped_commands[existing_pattern].append(activity)
                    found_group = True
                    break

            if not found_group:
                grouped_commands[pattern].append(activity)

        # Identify patterns meeting threshold
        for pattern, occurrences in grouped_commands.items():
            if len(occurrences) >= self.MIN_OCCURRENCES:
                pattern_id = f"cmd_{abs(hash(pattern)) % 10000}"

                if pattern_id not in self.known_patterns:
                    patterns.append({
                        "id": pattern_id,
                        "type": "command_sequence",
                        "pattern": pattern,
                        "occurrences": len(occurrences),
                        "first_seen": occurrences[0]["timestamp"],
                        "last_seen": occurrences[-1]["timestamp"],
                        "examples": [o.get("commands", []) for o in occurrences[:3]],
                        "context": list(set(o.get("context", "") for o in occurrences if o.get("context")))
                    })

        return patterns

    def detect_code_patterns(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect repetitive code modification patterns"""
        code_activities = [a for a in activities if a["type"] == "code_edit"]

        patterns = []

        # Group by change type and file type
        grouped = defaultdict(list)
        for activity in code_activities:
            key = (activity.get("action"), activity.get("file_type"))
            grouped[key].append(activity)

        for (action, file_type), occurrences in grouped.items():
            if len(occurrences) >= self.MIN_OCCURRENCES:
                # Check for similar descriptions
                descriptions = [o.get("description", "") for o in occurrences]
                common_desc = self._find_common_substring(descriptions)

                pattern_id = f"code_{action}_{file_type}_{abs(hash(common_desc)) % 10000}"

                if pattern_id not in self.known_patterns:
                    patterns.append({
                        "id": pattern_id,
                        "type": "code_pattern",
                        "action": action,
                        "file_type": file_type,
                        "occurrences": len(occurrences),
                        "common_description": common_desc,
                        "first_seen": occurrences[0]["timestamp"],
                        "last_seen": occurrences[-1]["timestamp"],
                        "files": [o.get("target", "") for o in occurrences[:5]]
                    })

        return patterns

    def detect_project_patterns(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect repetitive project initialization patterns"""
        project_activities = [a for a in activities if a["type"] == "project_init"]

        patterns = []

        # Group by tech stack similarity
        tech_stacks = defaultdict(list)
        for activity in project_activities:
            stack = tuple(sorted(activity.get("tech_stack", [])))
            tech_stacks[stack].append(activity)

        for stack, occurrences in tech_stacks.items():
            if len(occurrences) >= self.MIN_OCCURRENCES:
                pattern_id = f"proj_{abs(hash(stack)) % 10000}"

                if pattern_id not in self.known_patterns:
                    patterns.append({
                        "id": pattern_id,
                        "type": "project_template",
                        "tech_stack": list(stack),
                        "occurrences": len(occurrences),
                        "first_seen": occurrences[0]["timestamp"],
                        "last_seen": occurrences[-1]["timestamp"],
                        "purposes": list(set(o.get("purpose", "") for o in occurrences if o.get("purpose")))
                    })

        return patterns

    def detect_research_patterns(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect repetitive research/learning patterns"""
        research_activities = [a for a in activities if a["type"] == "research"]

        patterns = []

        # Group by topic similarity
        topics = defaultdict(list)
        for activity in research_activities:
            topic = activity.get("topic", "")
            if not topic:
                continue

            # Find similar topics
            found = False
            for existing_topic in list(topics.keys()):
                if self._similarity(topic, existing_topic) >= self.SIMILARITY_THRESHOLD:
                    topics[existing_topic].append(activity)
                    found = True
                    break

            if not found:
                topics[topic].append(activity)

        for topic, occurrences in topics.items():
            if len(occurrences) >= self.MIN_OCCURRENCES:
                pattern_id = f"research_{abs(hash(topic)) % 10000}"

                if pattern_id not in self.known_patterns:
                    # Collect common sources
                    all_sources = []
                    for o in occurrences:
                        all_sources.extend(o.get("sources", []))
                    source_freq = Counter(all_sources)

                    patterns.append({
                        "id": pattern_id,
                        "type": "research_workflow",
                        "topic": topic,
                        "occurrences": len(occurrences),
                        "first_seen": occurrences[0]["timestamp"],
                        "last_seen": occurrences[-1]["timestamp"],
                        "common_sources": [s for s, c in source_freq.most_common(5)],
                        "outcomes": list(set(o.get("outcome", "") for o in occurrences if o.get("outcome")))
                    })

        return patterns

    def _find_common_substring(self, strings: List[str]) -> str:
        """Find longest common substring in a list of strings"""
        if not strings:
            return ""

        # Simple approach: find most common words
        words = []
        for s in strings:
            words.extend(s.lower().split())

        if not words:
            return ""

        common = Counter(words).most_common(3)
        return " ".join([w for w, c in common if c >= 2])

    def analyze(self) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Run full pattern analysis on recent activities.

        Returns:
            (new_patterns, stats)
        """
        activities = self._load_recent_activities()

        stats = {
            "total_activities": len(activities),
            "by_type": Counter(a["type"] for a in activities),
            "days_analyzed": 7
        }

        new_patterns = []

        # Detect each pattern type
        new_patterns.extend(self.detect_command_patterns(activities))
        new_patterns.extend(self.detect_code_patterns(activities))
        new_patterns.extend(self.detect_project_patterns(activities))
        new_patterns.extend(self.detect_research_patterns(activities))

        # Mark new patterns as known
        for pattern in new_patterns:
            self.known_patterns[pattern["id"]] = {
                "detected_at": datetime.now().isoformat(),
                **pattern
            }

        if new_patterns:
            self._save_patterns()

        return new_patterns, stats

if __name__ == "__main__":
    detector = PatternDetector()
    patterns, stats = detector.analyze()

    print("=== Pattern Detection Results ===")
    print(f"Analyzed {stats['total_activities']} activities")
    print(f"Found {len(patterns)} new patterns\n")

    for pattern in patterns:
        print(f"Pattern: {pattern['type']}")
        print(f"  ID: {pattern['id']}")
        print(f"  Occurrences: {pattern['occurrences']}")
        print()
