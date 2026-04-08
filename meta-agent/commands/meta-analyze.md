# Meta-Agent Pattern Analysis

Run the Claude Code Meta-Agent to analyze recent activities and detect patterns worthy of skill creation.

Execute the following:

```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
python3 meta_agent.py analyze
```

Then:
1. Review the detected patterns
2. If new proposals were generated, run `/meta-report` to see detailed impact analysis
3. Consider approving promising proposals with `/meta-approve <proposal-id>`

The meta-agent tracks:
- Command sequences (repetitive bash operations)
- Code patterns (similar edits across files)
- Project types (tech stack combinations)
- Research patterns (documentation lookups)

All analysis is lightweight and incremental to minimize resource usage.
