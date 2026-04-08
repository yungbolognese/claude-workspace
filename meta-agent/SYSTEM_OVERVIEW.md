# Claude Code Meta-Agent System Overview

Complete technical documentation for the persistent meta-agent system.

## System Purpose

Monitor all Claude Code usage across all projects, detect repetitive patterns, and proactively propose skills/agents to accelerate development workflows.

## Location

```
/Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
```

This location ensures the meta-agent monitors ALL projects in your Github directory.

## Architecture

### Core Components

#### 1. Activity Tracker (`tracker.py`)
**Purpose**: Lightweight logging of Claude Code activities
**Features**:
- Append-only JSONL logs (minimal overhead)
- Hash-based deduplication (MD5, in-memory)
- Session-based logging
- 4 activity types: command, code_edit, project_init, research

**Data Flow**:
```
Activity → Hash Computation → Dedup Check → Log to JSONL → Index Update
```

**Files Generated**:
- `logs/session_YYYYMMDD_HHMMSS.jsonl` - Per-session logs
- `logs/activity_index.json` - Hash index (last 7 days)

#### 2. Pattern Detector (`pattern_detector.py`)
**Purpose**: Incremental pattern analysis
**Algorithm**:
- SequenceMatcher for string similarity (70% threshold)
- Grouping by similarity
- Threshold: 3+ occurrences for pattern

**Pattern Types**:
1. **Command Sequences**: Similar bash command chains
2. **Code Patterns**: Repetitive edits by type + file extension
3. **Project Templates**: Matching tech stacks
4. **Research Workflows**: Similar documentation lookups

**Performance**:
- Only analyzes last 7 days
- Incremental (doesn't reprocess known patterns)
- ~1s for 1000+ activities

#### 3. Skill Proposer (`skill_proposer.py`)
**Purpose**: Generate skill proposals from patterns
**Generates**:
- Detailed impact analysis
- Time savings estimates
- Speed improvement metrics
- Acceleration benefits breakdown
- Usage examples
- Implementation templates

**Impact Calculation**:
- Command skills: `num_commands * 10s` per use
- Code skills: `~120s` per use (boilerplate savings)
- Project skills: `~600s` per use (10 min setup)
- Research skills: `~300s` per use (5 min lookup)

#### 4. Meta-Agent Orchestrator (`meta_agent.py`)
**Purpose**: Main coordinator
**Responsibilities**:
- Configuration management
- Proactive alert triggering
- Pattern analysis orchestration
- Proposal approval and implementation
- Report generation

**Configuration** (`config.json`):
```json
{
  "proactive_alerts": true,
  "alert_threshold": 3,
  "periodic_reports": true,
  "report_frequency": "weekly",
  "track_patterns": {
    "command_sequences": true,
    "code_patterns": true,
    "project_types": true,
    "research_patterns": true
  },
  "auto_approve": false
}
```

#### 5. Claude Code Integration (`integrate_claude.py`)
**Purpose**: Interface for Claude Code sessions
**Features**:
- Convenience functions for logging
- Proactive alert display
- Direct imports for in-session use
- CLI interface

**Usage in Claude Code**:
```python
from integrate_claude import log_commands, check_patterns

log_commands(['git add .', 'git commit', 'git push'])
check_patterns()  # Triggers alerts if threshold met
```

#### 6. Approval Helper (`approve_proposal.py`)
**Purpose**: Streamline proposal approval
**Actions**:
1. Load proposal
2. Show summary
3. Request confirmation
4. Generate implementation files
5. Move to approved/

#### 7. Weekly Reporter (`weekly_report.py`)
**Purpose**: Periodic analysis and reporting
**Features**:
- Checks last report date
- Runs full analysis
- Generates markdown report
- Saves to reports/
- Can be cron scheduled

### Data Flow

```
┌─────────────────────────────────────────────┐
│         Claude Code Session                 │
│  (User works on projects naturally)         │
└─────────────┬───────────────────────────────┘
              │
              ▼
      ┌───────────────┐
      │    tracker.py  │ ◄── Logs activities
      └───────┬────────┘
              │
              ▼
        logs/*.jsonl
              │
              ▼
┌─────────────────────────────────────────────┐
│          pattern_detector.py                │
│  Analyzes recent activities (7 days)        │
│  Detects patterns (3+ similar actions)      │
└─────────────┬───────────────────────────────┘
              │
              ▼
      patterns/*.json
              │
              ▼
┌─────────────────────────────────────────────┐
│         skill_proposer.py                   │
│  Generates proposals with impact analysis   │
└─────────────┬───────────────────────────────┘
              │
              ▼
     proposals/*.json
              │
              ├──────► Proactive Alert
              │        (During session)
              │
              └──────► Periodic Report
                       (Weekly/on-demand)
              │
              ▼
       User Reviews
              │
              ├──► Approve ──► Implementation
              │                  (templates/)
              │
              └──► Dismiss
```

## Resource Profile

### Disk Usage
- **Logs**: ~10KB per 100 activities
- **Patterns**: ~5KB per 10 patterns
- **Proposals**: ~3KB per proposal
- **Total**: ~1-5MB typical weekly usage

### Memory
- **Activity Tracker**: ~2MB (hash index)
- **Pattern Detector**: ~5MB (during analysis)
- **Total**: <10MB

### CPU
- **Logging**: <1ms per activity
- **Pattern Detection**: ~1s per 1000 activities
- **Proposal Generation**: ~100ms per pattern

### I/O
- **Logging**: Append-only writes (fast)
- **Analysis**: Read last 7 days of logs
- **Reports**: Single write per report

**Conclusion**: Extremely lightweight, negligible impact on system performance.

## Workflow Modes

### 1. Proactive Mode (Default)
- Monitors every activity
- Triggers alert at threshold (3+ similar actions)
- Displays proposals during session
- Minimal interruption (only when patterns emerge)

### 2. Periodic Mode
- Silent monitoring
- Weekly analysis and report
- Email/file report
- No interruptions

### 3. On-Demand Mode
- Manual trigger only
- User runs analysis when desired
- Full control over timing

## Usage Patterns

### For Individual Developer
1. Work normally in Claude Code
2. Meta-agent tracks in background
3. Alert appears after 3+ similar actions
4. Review proposal
5. Approve valuable ones
6. Use generated skills
7. Continue with faster workflow

### For Team
1. Share `.claude-meta-agent` directory
2. All team members' patterns aggregate
3. Common workflows identified faster
4. Approved skills shared across team
5. Consistent practices emerge

## Integration Points

### Claude Code Sessions
```python
# Import in any Claude Code session
import sys
sys.path.append('/Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent')
from integrate_claude import *

# Use throughout session
log_edit('file.py', 'add_function')
check_patterns()
```

### Slash Commands
- `/meta-analyze` - Run analysis
- `/meta-report` - View proposals
- `/meta-proposals` - List pending
- `/meta-log` - Manual logging

### CLI
```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent

# Analysis
python3 meta_agent.py analyze

# Reporting
python3 meta_agent.py report

# Approval
python3 approve_proposal.py <id>

# Weekly
python3 weekly_report.py
```

## Pattern Detection Details

### Command Sequences
**Detection**:
- Groups commands with 70%+ similarity
- Joins with `&&` for pattern matching
- Tracks execution context

**Example**:
```
Pattern: "git add . && git commit -m 'message' && git push"
Occurrences: 5
→ Proposal: Git workflow automation
```

### Code Patterns
**Detection**:
- Groups by (action_type, file_extension)
- Finds common description terms
- Tracks affected files

**Example**:
```
Action: add_function
File Type: .tsx
Occurrences: 7
Common: "react component"
→ Proposal: React component generator
```

### Project Templates
**Detection**:
- Groups by sorted tech stack tuple
- Tracks project purposes
- Detects initialization patterns

**Example**:
```
Tech Stack: [swiftui, combine, coredata]
Occurrences: 3
→ Proposal: iOS project scaffolder
```

### Research Workflows
**Detection**:
- Groups by topic similarity
- Tracks common sources
- Aggregates outcomes

**Example**:
```
Topic: "SwiftUI animations"
Sources: [apple docs, hackingwithswift]
Occurrences: 4
→ Proposal: SwiftUI research assistant
```

## Proposal Lifecycle

```
Detection → Proposal → Review → Approval → Implementation → Usage
    ↓          ↓          ↓          ↓            ↓           ↓
 Pattern    Impact    Display    Generate      Install     Track
  JSON      Analysis   Alert     Files         Skill       Saves
```

### Proposal States
1. **Pending**: Detected, awaiting review (`proposals/*.json`)
2. **Approved**: Approved, implemented (`proposals/approved/*.json`)
3. **Active**: In use (tracked via usage patterns)

## Security & Privacy

### Data Stored
- Command patterns (not full commands with secrets)
- File paths (relative when possible)
- Code change types (not full code)
- Research topics (not credentials)

### Not Stored
- Actual code contents
- Secrets or credentials
- Personal data
- File contents

### Access Control
- All files in user directory
- No network transmission
- Local analysis only
- User approval required for implementation

## Extending the System

### Adding New Pattern Types

1. **Define Pattern in Detector**:
```python
# In pattern_detector.py
def detect_new_pattern(self, activities):
    # Your detection logic
    return patterns
```

2. **Add Proposal Generator**:
```python
# In skill_proposer.py
def _propose_new_skill(self, pattern):
    # Your proposal logic
    return proposal
```

3. **Update Tracker** (if needed):
```python
# In tracker.py
def log_new_activity(self, data):
    return self.log_activity("new_type", data)
```

### Custom Impact Metrics

Edit `skill_proposer.py` impact calculation:
```python
def _calculate_impact(self, pattern):
    # Custom calculation
    time_saved = your_formula(pattern)
    return {"time_saved_per_use_seconds": time_saved}
```

### Integration with External Tools

Add to `integrate_claude.py`:
```python
def log_from_external(data):
    # Parse external tool data
    # Log to meta-agent
    pass
```

## Troubleshooting

### No Patterns Detected
- Check: `ls logs/*.jsonl` - Are activities being logged?
- Check: `python3 tracker.py stats` - Session statistics
- Ensure: 3+ similar activities exist

### Alerts Not Showing
- Check: `config.json` - `proactive_alerts: true`?
- Check: Alert threshold met (default: 3)?
- Run: `python3 meta_agent.py analyze` manually

### Performance Issues
- Check: Log rotation (keep last 7 days only)
- Check: Hash index size (`logs/activity_index.json`)
- Reduce: Analysis frequency if needed

## Maintenance

### Regular Tasks

**Weekly**:
- Review proposals: `python3 meta_agent.py report`
- Approve valuable skills
- Check disk usage: `du -sh logs/`

**Monthly**:
- Archive old logs: `mv logs/*.jsonl logs/archive/`
- Review approved skills - still useful?
- Update thresholds if needed

**Quarterly**:
- Measure actual time savings
- Adjust impact formulas based on reality
- Share successful skills with team

### Cleanup

```bash
# Rotate old logs (keep 30 days)
find logs/ -name "session_*.jsonl" -mtime +30 -delete

# Archive approved proposals
mv proposals/approved/* proposals/archive/

# Reset if needed
rm -rf logs/* patterns/* proposals/*
```

## Success Metrics

Track these to measure value:

1. **Patterns Detected**: How many per week?
2. **Proposals Generated**: How many valuable?
3. **Approval Rate**: What % approved?
4. **Time Saved**: Actual vs estimated?
5. **Skills Created**: How many in use?
6. **Developer Satisfaction**: Faster workflow?

## Summary

The meta-agent is a **lightweight, proactive system** that:
- ✓ Monitors ALL Claude Code usage
- ✓ Detects repetitive patterns automatically
- ✓ Proposes skills with detailed impact analysis
- ✓ Minimal resource overhead (<10MB RAM, <5MB disk)
- ✓ Generates ready-to-use implementations
- ✓ Accelerates research, creation, and debugging
- ✓ Continuously improves YOUR specific workflow

**Result**: Development environment that learns from you and gets faster over time.

---

**Version**: 1.0
**Created**: 2026-04-08
**Status**: Active
**Location**: `/Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent`
