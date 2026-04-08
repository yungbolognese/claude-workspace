#!/usr/bin/env python3
"""
Claude Code Integration Helper
Call this from within Claude Code sessions to automatically log activities
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add meta-agent to path
sys.path.insert(0, str(Path(__file__).parent))

from tracker import ActivityTracker
from meta_agent import MetaAgent

class ClaudeCodeIntegration:
    """Helper class for integrating meta-agent with Claude Code sessions"""

    def __init__(self):
        self.tracker = ActivityTracker()
        self.meta_agent = MetaAgent()

    def log_bash_command(self, command: str, context: str = ""):
        """Log a single bash command"""
        return self.tracker.log_activity("command", {
            "action": "single",
            "commands": [command],
            "context": context,
            "pattern": command
        })

    def log_bash_sequence(self, commands: List[str], context: str = ""):
        """Log a sequence of bash commands"""
        alert = self.tracker.log_command_sequence(commands, context)

        # Check for proactive alerts
        if self.meta_agent.config["proactive_alerts"]:
            alert_data = self.meta_agent._check_proactive_alerts()
            if alert_data:
                self._show_proactive_alert(alert_data)

        return alert

    def log_file_edit(self, file_path: str, operation: str = "edit", description: str = ""):
        """Log a file edit operation"""
        change_types = {
            "create": "create_file",
            "edit": "modify_file",
            "delete": "delete_file",
            "refactor": "refactor_code",
            "add_function": "add_function",
            "add_class": "add_class",
            "fix_bug": "fix_bug"
        }

        change_type = change_types.get(operation, "modify_file")

        alert = self.tracker.log_code_change(file_path, change_type, description)

        if self.meta_agent.config["proactive_alerts"]:
            alert_data = self.meta_agent._check_proactive_alerts()
            if alert_data:
                self._show_proactive_alert(alert_data)

        return alert

    def log_multiple_edits(self, edits: List[Dict[str, str]]):
        """Log multiple file edits"""
        for edit in edits:
            self.log_file_edit(
                edit.get("file"),
                edit.get("operation", "edit"),
                edit.get("description", "")
            )

    def log_project_creation(self, project_path: str, tech_stack: List[str], purpose: str = ""):
        """Log a new project initialization"""
        alert = self.tracker.log_project_init(project_path, tech_stack, purpose)

        if self.meta_agent.config["proactive_alerts"]:
            alert_data = self.meta_agent._check_proactive_alerts()
            if alert_data:
                self._show_proactive_alert(alert_data)

        return alert

    def log_research_activity(self, topic: str, sources: List[str], outcome: str = ""):
        """Log a research/documentation lookup"""
        alert = self.tracker.log_research(topic, sources, outcome)

        if self.meta_agent.config["proactive_alerts"]:
            alert_data = self.meta_agent._check_proactive_alerts()
            if alert_data:
                self._show_proactive_alert(alert_data)

        return alert

    def _show_proactive_alert(self, alert_data: Dict[str, Any]):
        """Display a proactive alert to the user"""
        print("\n" + "="*60)
        print("🤖 META-AGENT PATTERN DETECTED!")
        print("="*60)

        proposals = alert_data.get("proposals", [])

        for proposal in proposals:
            print(f"\n📊 Skill Proposal: {proposal['name']}")
            print(f"   Type: {proposal['type'].replace('_', ' ').title()}")
            print(f"\n   Impact:")
            print(f"   • Used {proposal['impact']['historical_uses']} times already")
            print(f"   • Would save {proposal['impact']['time_saved_per_use_seconds']}s per use")
            print(f"   • Speed improvement: {proposal['impact']['speed_improvement']}")
            print(f"\n   Acceleration:")
            print(f"   • Creation: {proposal['acceleration']['creation']}")
            print(f"\n   Usage: {proposal['usage_example']}")
            print(f"   Proposal ID: {proposal['id']}")

        print("\n" + "-"*60)
        print("To review proposals: python3 meta_agent.py report")
        print("To approve: python3 approve_proposal.py <proposal-id>")
        print("="*60 + "\n")

    def check_for_patterns(self):
        """Manually check for new patterns"""
        return self.meta_agent._check_proactive_alerts()

    def generate_report(self):
        """Generate a full meta-agent report"""
        return self.meta_agent.generate_report("markdown")


# Convenience functions for direct import
_integration = None

def get_integration():
    global _integration
    if _integration is None:
        _integration = ClaudeCodeIntegration()
    return _integration

def log_command(command: str, context: str = ""):
    """Quick function to log a command"""
    return get_integration().log_bash_command(command, context)

def log_commands(commands: List[str], context: str = ""):
    """Quick function to log command sequence"""
    return get_integration().log_bash_sequence(commands, context)

def log_edit(file_path: str, operation: str = "edit", description: str = ""):
    """Quick function to log file edit"""
    return get_integration().log_file_edit(file_path, operation, description)

def log_project(project_path: str, tech_stack: List[str], purpose: str = ""):
    """Quick function to log project creation"""
    return get_integration().log_project_creation(project_path, tech_stack, purpose)

def log_research(topic: str, sources: List[str], outcome: str = ""):
    """Quick function to log research"""
    return get_integration().log_research_activity(topic, sources, outcome)

def check_patterns():
    """Check for patterns and show alerts"""
    return get_integration().check_for_patterns()

def meta_report():
    """Generate meta-agent report"""
    return get_integration().generate_report()


# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 integrate_claude.py command '<command>' [context]")
        print("  python3 integrate_claude.py edit '<file>' [operation] [description]")
        print("  python3 integrate_claude.py project '<path>' '<stack1,stack2>' [purpose]")
        print("  python3 integrate_claude.py research '<topic>' '<source1,source2>' [outcome]")
        print("  python3 integrate_claude.py check")
        sys.exit(1)

    integration = get_integration()
    action = sys.argv[1]

    if action == "command":
        cmd = sys.argv[2]
        ctx = sys.argv[3] if len(sys.argv) > 3 else ""
        integration.log_bash_command(cmd, ctx)
        print(f"Logged command: {cmd}")

    elif action == "edit":
        file = sys.argv[2]
        op = sys.argv[3] if len(sys.argv) > 3 else "edit"
        desc = sys.argv[4] if len(sys.argv) > 4 else ""
        integration.log_file_edit(file, op, desc)
        print(f"Logged edit: {file}")

    elif action == "project":
        path = sys.argv[2]
        stack = sys.argv[3].split(',')
        purpose = sys.argv[4] if len(sys.argv) > 4 else ""
        integration.log_project_creation(path, stack, purpose)
        print(f"Logged project: {path}")

    elif action == "research":
        topic = sys.argv[2]
        sources = sys.argv[3].split(',')
        outcome = sys.argv[4] if len(sys.argv) > 4 else ""
        integration.log_research_activity(topic, sources, outcome)
        print(f"Logged research: {topic}")

    elif action == "check":
        alert = integration.check_for_patterns()
        if alert:
            print("New patterns detected! Check output above.")
        else:
            print("No new patterns detected yet.")
