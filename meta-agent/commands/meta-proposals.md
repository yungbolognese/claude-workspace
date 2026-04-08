# Meta-Agent Proposals

View all pending skill proposals detected by the Claude Code Meta-Agent.

Execute the following:

```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
python3 meta_agent.py proposals
```

This shows a quick list of all proposals with:
- Proposal ID (for approval)
- Skill name and type
- Impact estimate

To see full details for a specific proposal, run:

```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent/proposals
cat <proposal-id>.json
```

Or use `/meta-report` for a formatted summary of all proposals.

To approve a proposal and generate implementation files:
- Ask Claude: "Approve meta-agent proposal <proposal-id>"
- Or manually run: `python3 meta_agent.py approve <proposal-id>`
