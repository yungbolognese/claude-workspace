#!/usr/bin/env python3
"""
Claude Code Meta-Agent
Main orchestrator for pattern detection and skill proposal across all Claude Code usage
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from tracker import ActivityTracker
from pattern_detector import PatternDetector
from skill_proposer import SkillProposer


class MetaAgent:
    """
    Persistent meta-agent that monitors Claude Code usage and proposes optimizations
    """

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent
        self.base_dir = Path(base_dir)

        # Initialize components
        self.tracker = ActivityTracker(base_dir)
        self.detector = PatternDetector(base_dir)
        self.proposer = SkillProposer(base_dir)

        # Configuration
        self.config_file = self.base_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load or create configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)

        # Default configuration
        default_config = {
            "proactive_alerts": True,
            "alert_threshold": 3,  # Alert after 3 similar actions
            "periodic_reports": True,
            "report_frequency": "weekly",
            "track_patterns": {
                "command_sequences": True,
                "code_patterns": True,
                "project_types": True,
                "research_patterns": True
            },
            "auto_approve": False,  # Proposal-based by default
            "last_analysis": None,
            "last_report": None
        }

        self._save_config(default_config)
        return default_config

    def _save_config(self, config: Dict[str, Any] = None):
        """Save configuration"""
        if config is None:
            config = self.config

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def log_activity(self, activity_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Log an activity and check if proactive alert should trigger.

        Returns:
            Alert data if pattern detected, None otherwise
        """
        # Log the activity
        is_new = self.tracker.log_activity(activity_type, data)

        # Check if we should run proactive detection
        if self.config["proactive_alerts"] and is_new:
            return self._check_proactive_alerts()

        return None

    def _check_proactive_alerts(self) -> Optional[Dict[str, Any]]:
        """
        Check if any patterns have crossed the alert threshold.
        This is lightweight - only analyzes recent activities.
        """
        # Run incremental pattern detection
        new_patterns, stats = self.detector.analyze()

        if not new_patterns:
            return None

        # Generate proposals for new patterns
        proposals = []
        for pattern in new_patterns:
            if pattern["occurrences"] >= self.config["alert_threshold"]:
                proposal = self.proposer.generate_proposal(pattern)
                if proposal:
                    self.proposer.save_proposal(proposal)
                    proposals.append(proposal)

        if proposals:
            # Update last analysis time
            self.config["last_analysis"] = datetime.now().isoformat()
            self._save_config()

            return {
                "type": "proactive_alert",
                "timestamp": datetime.now().isoformat(),
                "proposals": proposals,
                "stats": stats
            }

        return None

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Run full pattern analysis (on-demand or periodic).

        Returns:
            Analysis report with patterns and proposals
        """
        patterns, stats = self.detector.analyze()

        proposals = []
        for pattern in patterns:
            proposal = self.proposer.generate_proposal(pattern)
            if proposal:
                self.proposer.save_proposal(proposal)
                proposals.append(proposal)

        # Update config
        self.config["last_analysis"] = datetime.now().isoformat()
        self._save_config()

        return {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "patterns_detected": len(patterns),
            "proposals_generated": len(proposals),
            "patterns": patterns,
            "proposals": proposals
        }

    def generate_report(self, format: str = "markdown") -> str:
        """Generate a comprehensive report of all patterns and proposals"""
        pending_proposals = self.proposer.load_pending_proposals()
        session_stats = self.tracker.get_session_stats()

        if format == "markdown":
            return self._generate_markdown_report(pending_proposals, session_stats)
        elif format == "json":
            return json.dumps({
                "proposals": pending_proposals,
                "session_stats": session_stats
            }, indent=2)
        else:
            return "Unsupported format"

    def _generate_markdown_report(self, proposals: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Generate markdown summary report"""
        report = f"""# Claude Code Meta-Agent Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Current Session Stats

- **Total Activities:** {stats['total_activities']}
- **By Type:** {', '.join(f"{k}: {v}" for k, v in stats.get('by_type', {}).items())}

## Pending Skill Proposals ({len(proposals)})

"""

        if not proposals:
            report += "*No pending proposals. Keep using Claude Code and patterns will be detected!*\n"
        else:
            for proposal in proposals:
                impact = proposal['impact']
                report += f"""### {proposal['name']}

**Type:** {proposal['type'].replace('_', ' ').title()}

**Impact:**
- Historical uses: {impact['historical_uses']}
- Time saved per use: {impact['time_saved_per_use_seconds']}s
- Speed improvement: {impact['speed_improvement']}

**Description:** {proposal['description']}

**Usage:** `{proposal['usage_example']}`

---

"""

        # Add summary statistics
        if proposals:
            total_potential_time = sum(
                p['impact']['historical_uses'] * p['impact']['time_saved_per_use_seconds']
                for p in proposals
            )
            report += f"""
## Summary

If all {len(proposals)} proposed skills had existed, you would have saved approximately **{total_potential_time}s ({total_potential_time // 60}min)** of development time.

"""

        report += """
---
*Meta-Agent actively monitoring your Claude Code usage*
"""

        return report

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific proposal by ID"""
        proposals = self.proposer.load_pending_proposals()
        for p in proposals:
            if p['id'] == proposal_id:
                return p
        return None

    def approve_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """
        Approve a proposal and generate implementation files.

        Returns:
            Implementation details and file paths
        """
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return {"error": "Proposal not found"}

        # Generate implementation based on proposal type
        if proposal['type'] == "command_skill":
            return self._implement_command_skill(proposal)
        elif proposal['type'] == "code_generator_skill":
            return self._implement_code_skill(proposal)
        elif proposal['type'] == "project_scaffolder":
            return self._implement_project_skill(proposal)
        elif proposal['type'] == "research_assistant":
            return self._implement_research_skill(proposal)

        return {"error": "Unknown proposal type"}

    def _implement_command_skill(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Implement a command sequence skill as a bash script"""
        script_content = proposal['implementation']['script_content']
        skill_name = proposal['name'].lower().replace(' ', '_')
        script_path = self.base_dir / "templates" / f"{skill_name}.sh"

        with open(script_path, 'w') as f:
            f.write(script_content)

        script_path.chmod(0o755)  # Make executable

        return {
            "status": "implemented",
            "type": "bash_script",
            "script_path": str(script_path),
            "usage": f"Run: {script_path}",
            "next_steps": "Add to Claude Code as a slash command or MCP tool"
        }

    def _implement_code_skill(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Implement a code pattern skill as a template"""
        template_content = f"""# {proposal['name']} Template

**Action:** {proposal['implementation']['action']}
**File Type:** {proposal['implementation']['file_type']}

## Pattern
{proposal['implementation']['template_suggestions']}

## Implementation
This template should be implemented as a Claude Code skill that generates
code following this pattern.
"""
        skill_name = proposal['name'].lower().replace(' ', '_')
        template_path = self.base_dir / "templates" / f"{skill_name}_template.md"

        with open(template_path, 'w') as f:
            f.write(template_content)

        return {
            "status": "template_created",
            "type": "code_template",
            "template_path": str(template_path),
            "next_steps": "Implement as Claude Code skill with template system"
        }

    def _implement_project_skill(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Implement a project scaffolder skill"""
        scaffold_content = f"""# {proposal['name']}

**Tech Stack:** {', '.join(proposal['implementation']['tech_stack'])}

## Project Structure
Create a project scaffolder for this tech stack.

## Components
{chr(10).join('- ' + c for c in proposal['implementation']['components'])}

## Usage
{proposal['usage_example']}
"""
        skill_name = proposal['name'].lower().replace(' ', '_')
        scaffold_path = self.base_dir / "templates" / f"{skill_name}_scaffold.md"

        with open(scaffold_path, 'w') as f:
            f.write(scaffold_content)

        return {
            "status": "template_created",
            "type": "project_scaffold",
            "template_path": str(scaffold_path),
            "next_steps": "Implement as Claude Code skill with project template"
        }

    def _implement_research_skill(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Implement a research assistant skill"""
        workflow_content = f"""# {proposal['name']}

**Topic:** {proposal['implementation']['topic']}

## Curated Sources
{chr(10).join('- ' + s for s in proposal['implementation']['curated_sources'])}

## Workflow
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(proposal['implementation']['workflow']))}

## Usage
{proposal['usage_example']}
"""
        skill_name = proposal['name'].lower().replace(' ', '_')
        workflow_path = self.base_dir / "templates" / f"{skill_name}_workflow.md"

        with open(workflow_path, 'w') as f:
            f.write(workflow_content)

        return {
            "status": "template_created",
            "type": "research_workflow",
            "template_path": str(workflow_path),
            "next_steps": "Implement as Claude Code agent with web search capabilities"
        }


if __name__ == "__main__":
    import sys

    agent = MetaAgent()

    if len(sys.argv) == 1:
        print("Claude Code Meta-Agent")
        print(f"Base dir: {agent.base_dir}")
        print(f"Proactive alerts: {agent.config['proactive_alerts']}")
        print(f"Last analysis: {agent.config.get('last_analysis', 'Never')}")

    elif sys.argv[1] == "analyze":
        print("Running pattern analysis...")
        result = agent.analyze_patterns()
        print(f"Found {result['patterns_detected']} patterns")
        print(f"Generated {result['proposals_generated']} proposals")

    elif sys.argv[1] == "report":
        format_type = sys.argv[2] if len(sys.argv) > 2 else "markdown"
        print(agent.generate_report(format_type))

    elif sys.argv[1] == "proposals":
        proposals = agent.proposer.load_pending_proposals()
        print(f"Pending proposals: {len(proposals)}")
        for p in proposals:
            print(f"\n{p['name']}")
            print(f"  ID: {p['id']}")
            print(f"  Type: {p['type']}")
            print(f"  Impact: {p['impact']['total_time_saved_estimate']}")
