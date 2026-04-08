#!/usr/bin/env python3
"""
Skill Proposal Generator for Claude Code Meta-Agent
Generates skill/agent proposals from detected patterns with impact analysis
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SkillProposer:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent
        self.base_dir = Path(base_dir)
        self.proposals_dir = self.base_dir / "proposals"
        self.templates_dir = self.base_dir / "templates"
        self.proposals_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

    def generate_proposal(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a skill proposal from a detected pattern.

        Returns:
            Proposal with skill definition, impact analysis, and implementation
        """
        pattern_type = pattern["type"]

        if pattern_type == "command_sequence":
            return self._propose_command_skill(pattern)
        elif pattern_type == "code_pattern":
            return self._propose_code_skill(pattern)
        elif pattern_type == "project_template":
            return self._propose_project_skill(pattern)
        elif pattern_type == "research_workflow":
            return self._propose_research_skill(pattern)
        else:
            return None

    def _propose_command_skill(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a skill for repetitive command sequences"""
        commands = pattern["examples"][0] if pattern["examples"] else []
        pattern_str = pattern["pattern"]

        # Estimate impact
        occurrences = pattern["occurrences"]
        avg_commands = len(commands)
        time_saved_per_use = avg_commands * 10  # ~10 sec per command saved

        skill_name = self._generate_skill_name(pattern_str)

        proposal = {
            "id": f"proposal_{pattern['id']}",
            "pattern_id": pattern["id"],
            "type": "command_skill",
            "name": skill_name,
            "description": f"Automates the command sequence: {pattern_str}",
            "detected_at": datetime.now().isoformat(),

            # Impact Analysis
            "impact": {
                "historical_uses": occurrences,
                "time_saved_per_use_seconds": time_saved_per_use,
                "total_time_saved_estimate": f"{occurrences * time_saved_per_use}s saved if had existed",
                "resource_cost": "Minimal - simple bash script",
                "speed_improvement": f"{avg_commands}x faster (single command vs {avg_commands} commands)"
            },

            # Acceleration Benefits
            "acceleration": {
                "research": "N/A - pure automation",
                "creation": f"Speeds up {pattern.get('context', ['development'])} by eliminating manual command sequences",
                "debugging": "Reduces errors from manually typing repetitive commands",
                "consistency": "Ensures same commands run in same order every time"
            },

            # Implementation
            "implementation": {
                "type": "bash_script",
                "commands": commands,
                "script_content": self._generate_bash_script(skill_name, commands),
                "integration": "Add as Claude Code slash command"
            },

            # Usage example
            "usage_example": f"/{skill_name.replace(' ', '-').lower()}",

            # Original pattern data
            "pattern": pattern
        }

        return proposal

    def _propose_code_skill(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a skill for repetitive code patterns"""
        action = pattern["action"]
        file_type = pattern["file_type"]
        occurrences = pattern["occurrences"]

        skill_name = f"{action.replace('_', ' ').title()} {file_type.upper()} Helper"

        proposal = {
            "id": f"proposal_{pattern['id']}",
            "pattern_id": pattern["id"],
            "type": "code_generator_skill",
            "name": skill_name,
            "description": f"Generates or modifies {file_type} files with common {action} pattern",
            "detected_at": datetime.now().isoformat(),

            # Impact Analysis
            "impact": {
                "historical_uses": occurrences,
                "time_saved_per_use_seconds": 120,  # ~2 min per boilerplate
                "total_time_saved_estimate": f"{occurrences * 120}s saved if had existed",
                "resource_cost": "Low - template-based generation",
                "speed_improvement": "5-10x faster than manual coding"
            },

            # Acceleration Benefits
            "acceleration": {
                "research": "Embeds best practices discovered from repeated use",
                "creation": f"Instantly generates {action} boilerplate for {file_type} files",
                "debugging": "Reduces bugs by using validated patterns",
                "consistency": "Ensures consistent code style and structure"
            },

            # Implementation
            "implementation": {
                "type": "code_template",
                "action": action,
                "file_type": file_type,
                "template_suggestions": pattern.get("common_description", ""),
                "integration": "Add as Claude Code skill with template system"
            },

            # Usage example
            "usage_example": f"Use skill to {action} {file_type} files with standard pattern",

            # Original pattern data
            "pattern": pattern
        }

        return proposal

    def _propose_project_skill(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a skill for project initialization patterns"""
        tech_stack = pattern["tech_stack"]
        occurrences = pattern["occurrences"]

        stack_name = "-".join(tech_stack[:3])  # First 3 for brevity
        skill_name = f"{stack_name.title()} Project Scaffolder"

        proposal = {
            "id": f"proposal_{pattern['id']}",
            "pattern_id": pattern["id"],
            "type": "project_scaffolder",
            "name": skill_name,
            "description": f"Scaffolds new project with {', '.join(tech_stack)} stack",
            "detected_at": datetime.now().isoformat(),

            # Impact Analysis
            "impact": {
                "historical_uses": occurrences,
                "time_saved_per_use_seconds": 600,  # ~10 min per project setup
                "total_time_saved_estimate": f"{occurrences * 600}s ({occurrences * 10}min) saved if had existed",
                "resource_cost": "Moderate - includes dependencies, config files",
                "speed_improvement": "20-30x faster than manual setup"
            },

            # Acceleration Benefits
            "acceleration": {
                "research": "Captures proven tech stack configuration from experience",
                "creation": "Instantly bootstrap new projects with zero-config setup",
                "debugging": "Pre-configured tooling reduces setup bugs",
                "consistency": "All projects follow same structure and conventions"
            },

            # Implementation
            "implementation": {
                "type": "project_template",
                "tech_stack": tech_stack,
                "purposes": pattern.get("purposes", []),
                "components": [
                    "Directory structure",
                    "Package.json / dependencies",
                    "Configuration files",
                    "Boilerplate code",
                    "README template"
                ],
                "integration": "Add as Claude Code skill with cookiecutter-style templates"
            },

            # Usage example
            "usage_example": f"/{stack_name.lower()}-init <project-name>",

            # Original pattern data
            "pattern": pattern
        }

        return proposal

    def _propose_research_skill(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a skill for research/learning patterns"""
        topic = pattern["topic"]
        sources = pattern.get("common_sources", [])
        occurrences = pattern["occurrences"]

        skill_name = f"{topic.title()} Research Assistant"

        proposal = {
            "id": f"proposal_{pattern['id']}",
            "pattern_id": pattern["id"],
            "type": "research_assistant",
            "name": skill_name,
            "description": f"Automates research workflow for {topic}",
            "detected_at": datetime.now().isoformat(),

            # Impact Analysis
            "impact": {
                "historical_uses": occurrences,
                "time_saved_per_use_seconds": 300,  # ~5 min per research session
                "total_time_saved_estimate": f"{occurrences * 300}s ({occurrences * 5}min) saved if had existed",
                "resource_cost": "Low - web searches and documentation lookups",
                "speed_improvement": "3-5x faster with curated sources"
            },

            # Acceleration Benefits
            "acceleration": {
                "research": f"Instantly finds relevant {topic} documentation from known-good sources",
                "creation": "Faster prototyping with quick access to examples and APIs",
                "debugging": "Quickly lookup error messages and solutions",
                "consistency": "Always searches the same high-quality sources"
            },

            # Implementation
            "implementation": {
                "type": "research_workflow",
                "topic": topic,
                "curated_sources": sources,
                "outcomes": pattern.get("outcomes", []),
                "workflow": [
                    "Search curated documentation sources",
                    "Extract relevant code examples",
                    "Summarize key findings",
                    "Provide next steps"
                ],
                "integration": "Add as Claude Code agent with web search and documentation access"
            },

            # Usage example
            "usage_example": f"/research-{topic.lower().replace(' ', '-')} <query>",

            # Original pattern data
            "pattern": pattern
        }

        return proposal

    def _generate_skill_name(self, pattern_str: str) -> str:
        """Generate a readable skill name from pattern"""
        # Extract key verbs and nouns
        words = pattern_str.split()
        if len(words) > 5:
            return f"{words[0].title()} Workflow"
        return " ".join(words[:3]).title()

    def _generate_bash_script(self, skill_name: str, commands: List[str]) -> str:
        """Generate bash script content for command skill"""
        script = f"""#!/bin/bash
# {skill_name}
# Auto-generated by Claude Code Meta-Agent

set -e  # Exit on error

"""
        for cmd in commands:
            script += f"{cmd}\n"

        script += '\necho "✓ {}" complete\n'.format(skill_name)
        return script

    def save_proposal(self, proposal: Dict[str, Any]):
        """Save proposal to disk"""
        proposal_file = self.proposals_dir / f"{proposal['id']}.json"
        with open(proposal_file, 'w') as f:
            json.dump(proposal, f, indent=2)

    def load_pending_proposals(self) -> List[Dict[str, Any]]:
        """Load all pending proposals"""
        proposals = []
        for proposal_file in self.proposals_dir.glob("proposal_*.json"):
            with open(proposal_file, 'r') as f:
                proposals.append(json.load(f))
        return proposals

    def generate_markdown_report(self, proposal: Dict[str, Any]) -> str:
        """Generate human-readable markdown report for a proposal"""
        report = f"""# Skill Proposal: {proposal['name']}

**Type:** {proposal['type'].replace('_', ' ').title()}
**Detected:** {proposal['detected_at']}

## Description
{proposal['description']}

## Impact Analysis

- **Historical Uses:** {proposal['impact']['historical_uses']} times
- **Time Saved Per Use:** {proposal['impact']['time_saved_per_use_seconds']}s
- **Total Time That Could Have Been Saved:** {proposal['impact']['total_time_saved_estimate']}
- **Resource Cost:** {proposal['impact']['resource_cost']}
- **Speed Improvement:** {proposal['impact']['speed_improvement']}

## Acceleration Benefits

### Research
{proposal['acceleration']['research']}

### Creation
{proposal['acceleration']['creation']}

### Debugging
{proposal['acceleration']['debugging']}

### Consistency
{proposal['acceleration']['consistency']}

## Implementation

**Type:** {proposal['implementation']['type']}
**Integration:** {proposal['implementation']['integration']}

## Usage Example
```
{proposal['usage_example']}
```

## Pattern Details
- **Pattern ID:** {proposal['pattern_id']}
- **Occurrences:** {proposal['pattern']['occurrences']}
- **First Seen:** {proposal['pattern']['first_seen']}
- **Last Seen:** {proposal['pattern']['last_seen']}

---
*Generated by Claude Code Meta-Agent*
"""
        return report

if __name__ == "__main__":
    import sys
    proposer = SkillProposer()

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        proposals = proposer.load_pending_proposals()
        print(f"Found {len(proposals)} pending proposals")
        for p in proposals:
            print(f"  - {p['name']} ({p['type']})")
