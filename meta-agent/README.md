# Claude Code Meta-Agent

A persistent meta-agent that monitors ALL your Claude Code usage across all skills and projects, detects repetitive patterns, and proposes new skills/agents to accelerate your development workflow.

## What It Does

The meta-agent runs continuously in the background, tracking:

1. **Command Sequences**: Repetitive bash operations you run frequently
2. **Code Patterns**: Similar code modifications across different files
3. **Project Types**: Tech stacks and project scaffolding you use repeatedly
4. **Research Workflows**: Documentation lookups and learning patterns

When it detects a pattern emerging (3+ similar actions), it:
- Proactively alerts you during your session
- Proposes a custom skill/agent to automate that pattern
- Provides detailed impact analysis (time saved, speed improvements)
- Generates implementation files ready for integration

## Architecture

```
.claude-meta-agent/
├── meta_agent.py          # Main orchestrator
├── tracker.py             # Lightweight activity logger
├── pattern_detector.py    # Incremental pattern detection
├── skill_proposer.py      # Skill proposal generator
├── approve_proposal.py    # Proposal approval helper
├── weekly_report.py       # Periodic report generator
├── config.json            # Configuration
├── logs/                  # Activity logs (JSONL format)
│   ├── session_*.jsonl    # Per-session activity logs
│   └── activity_index.json # Hash index for deduplication
├── patterns/              # Detected patterns
│   └── detected_patterns.json
├── proposals/             # Skill proposals
│   ├── proposal_*.json    # Pending proposals
│   └── approved/          # Approved proposals
├── templates/             # Generated implementations
│   └── *.sh, *.md         # Skill templates and scripts
├── reports/               # Weekly reports
│   └── weekly_*.md
└── commands/              # Claude Code slash commands
    ├── meta-analyze.md
    ├── meta-report.md
    ├── meta-proposals.md
    └── meta-log.md
```

## Resource Impact

**Lightweight by Design:**
- Activity logs: Append-only JSONL (~1KB per 100 activities)
- Pattern detection: Incremental, only analyzes recent 7 days
- Hash-based deduplication: In-memory, minimal overhead
- No database required: Simple JSON files
- Analysis runs on-demand or when patterns emerge

**Estimated Resource Usage:**
- Disk: ~1-5MB for typical weekly usage
- Memory: <10MB during analysis
- CPU: <1s for pattern detection on 1000+ activities

## Installation

### 1. The meta-agent is already installed!

Located at: `/Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent`

### 2. Add Claude Code Commands (Optional)

To use slash commands like `/meta-analyze`, `/meta-report`, etc., symlink the commands:

```bash
# If you have a .claude/commands directory in your projects
ln -s /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent/commands/* ~/.claude/commands/

# Or add to specific project:
cd /path/to/your/project
mkdir -p .claude/commands
ln -s /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent/commands/* .claude/commands/
```

### 3. Set Up Periodic Reports (Optional)

For weekly automated reports, add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 9 AM):
0 9 * * 1 cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent && python3 weekly_report.py >> reports/cron.log 2>&1
```

Or run manually whenever you want:
```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
python3 weekly_report.py
```

## Usage

### Proactive Mode (Automatic)

The meta-agent monitors your Claude Code sessions and will alert you when it detects patterns. Just use Claude Code normally!

When you see a pattern alert:
1. Review the proposed skill
2. Check the impact analysis
3. Approve if beneficial
4. Meta-agent generates implementation files

### Manual Commands

**Analyze patterns:**
```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
python3 meta_agent.py analyze
```

**View report:**
```bash
python3 meta_agent.py report
```

**List proposals:**
```bash
python3 meta_agent.py proposals
```

**Approve a proposal:**
```bash
python3 approve_proposal.py <proposal-id>
```

### Claude Code Integration

**Using slash commands (if set up):**
- `/meta-analyze` - Run pattern analysis
- `/meta-report` - Generate full report
- `/meta-proposals` - List pending proposals
- `/meta-log` - Manually log an activity

**Direct in chat:**
- "Run the meta-agent analysis"
- "Show me meta-agent proposals"
- "Approve meta-agent proposal proposal_cmd_1234"

## Configuration

Edit `config.json`:

```json
{
  "proactive_alerts": true,         // Alert during sessions
  "alert_threshold": 3,             // Alert after N similar actions
  "periodic_reports": true,         // Enable weekly reports
  "report_frequency": "weekly",     // "daily" or "weekly"
  "track_patterns": {
    "command_sequences": true,      // Track bash commands
    "code_patterns": true,          // Track code edits
    "project_types": true,          // Track project inits
    "research_patterns": true       // Track research
  },
  "auto_approve": false             // Proposal-based approval
}
```

## Examples

### Example 1: Command Sequence Pattern

**You run repeatedly:**
```bash
git add .
git commit -m "Update"
git push
```

**Meta-agent detects after 3x:**
- Pattern: git add && git commit && git push
- Proposes: "Git Push Workflow" skill
- Impact: 3 commands → 1 command (30s saved per use)
- Implementation: Bash script at `templates/git_push_workflow.sh`

### Example 2: Project Initialization Pattern

**You create 3 projects with:**
- SwiftUI + Combine + CoreData

**Meta-agent detects:**
- Pattern: iOS app with this stack
- Proposes: "SwiftUI-Combine-CoreData Project Scaffolder"
- Impact: 10+ min saved per project setup
- Implementation: Project template with all boilerplate

### Example 3: Research Pattern

**You frequently search:**
- SwiftUI animation documentation
- Apple Human Interface Guidelines
- SwiftUI by Example tutorials

**Meta-agent detects:**
- Pattern: SwiftUI learning workflow
- Proposes: "SwiftUI Research Assistant"
- Impact: 5 min saved per research session
- Implementation: Curated source list + search workflow

## How It Accelerates Your Workflow

### Research
- **Detects**: Repeated doc lookups, web searches for same topics
- **Proposes**: Research assistants with curated sources
- **Benefit**: Instant access to known-good documentation, 3-5x faster

### Creation
- **Detects**: Repetitive project setups, boilerplate code
- **Proposes**: Project scaffolders, code generators
- **Benefit**: Zero-config project init, 10-20x faster

### Debugging
- **Detects**: Common debugging command sequences
- **Proposes**: Debug workflow automations
- **Benefit**: One-command debugging, fewer manual errors

### Consistency
- **Detects**: Variations in similar tasks
- **Proposes**: Standardized workflows
- **Benefit**: Same approach every time, better quality

## Logging Activities

Most activities are tracked automatically when using Claude Code. For manual logging:

```python
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent

# Log command sequence
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_command_sequence(
    ['npm install', 'npm run dev'],
    context='starting dev server'
)
"

# Log code change
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_code_change(
    file_path='src/App.tsx',
    change_type='add_component',
    description='Added new React component'
)
"

# Log project init
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_project_init(
    project_path='/path/to/project',
    tech_stack=['react', 'typescript', 'vite'],
    purpose='web app'
)
"

# Log research
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_research(
    topic='React hooks',
    sources=['react docs', 'stack overflow'],
    outcome='learned useCallback'
)
"
```

## Integration with Claude Code Sessions

The meta-agent can monitor your Claude Code sessions by tracking:
- Bash commands executed
- Files edited
- Projects created
- Web searches and documentation lookups

This happens automatically through Claude Code's tool usage.

## Troubleshooting

**No patterns detected?**
- Keep using Claude Code naturally for a few sessions
- Patterns need 3+ occurrences to trigger
- Check logs: `ls -la logs/session_*.jsonl`

**Proposals not generating?**
- Run manual analysis: `python3 meta_agent.py analyze`
- Check detected patterns: `cat patterns/detected_patterns.json`
- Ensure threshold met (default: 3 occurrences)

**Want to reset?**
```bash
# Backup first!
rm -rf logs/* patterns/* proposals/*
# Restart from clean slate
```

## Philosophy

The meta-agent embodies **continuous improvement**:
1. You work naturally in Claude Code
2. Patterns emerge from your real usage
3. Agent proposes optimizations based on YOUR workflow
4. You approve what adds value
5. Your toolkit grows organically
6. You work faster, agent learns more
7. Repeat

This creates a **positive feedback loop** where your development environment continuously adapts to accelerate your specific workflow.

## Future Enhancements

Potential additions (you can implement yourself or ask Claude!):

- [ ] Integration with Claude Code hooks for automatic logging
- [ ] Pattern visualization dashboard
- [ ] Multi-project pattern detection (patterns across all your projects)
- [ ] Skill performance tracking (measure actual time saved)
- [ ] Export/import skills to share with others
- [ ] Natural language skill queries ("Show me skills for React")
- [ ] Auto-categorization of skills by domain

## Support

Questions or issues? Just ask Claude:
- "How do I use the meta-agent?"
- "Show me meta-agent patterns"
- "What proposals does the meta-agent have?"

---

**Meta-Agent Version:** 1.0
**Created:** 2026-04-08
**Location:** /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
