# Meta-Agent Quick Start

Get started with the Claude Code Meta-Agent in 5 minutes!

## 1. Verify Installation

```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
python3 meta_agent.py
```

You should see:
```
Claude Code Meta-Agent
Base dir: /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
Proactive alerts: True
Last analysis: Never
```

## 2. Log Some Sample Activities

Let's simulate some activities to see how pattern detection works:

```bash
# Simulate a git workflow pattern (3 times to trigger detection)
for i in {1..3}; do
  python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_command_sequence(
    ['git add .', 'git commit -m \"Update\"', 'git push'],
    context='git workflow'
)
print('Logged git workflow #$i')
"
done

# Simulate SwiftUI project pattern
for i in {1..3}; do
  python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_project_init(
    project_path='/Users/danielchoe/Library/CloudStorage/Dropbox/Github/build/app$i',
    tech_stack=['swiftui', 'combine', 'coredata'],
    purpose='iOS app'
)
print('Logged SwiftUI project #$i')
"
done

# Simulate research pattern
for i in {1..3}; do
  python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_research(
    topic='SwiftUI animations',
    sources=['apple docs', 'swiftui by example'],
    outcome='learned animation modifiers'
)
print('Logged research #$i')
"
done
```

## 3. Run Pattern Analysis

```bash
python3 meta_agent.py analyze
```

You should see patterns detected:
```
Found 3 patterns
Generated 3 proposals
```

## 4. View Proposals

```bash
python3 meta_agent.py proposals
```

You'll see your pending proposals with impact estimates!

## 5. Generate Full Report

```bash
python3 meta_agent.py report
```

This shows:
- Session statistics
- All proposals with detailed impact analysis
- Total time savings estimate
- Usage examples

## 6. Approve a Proposal

```bash
# List proposals to get ID
python3 meta_agent.py proposals

# Approve one (replace with actual ID)
python3 approve_proposal.py proposal_cmd_1234
```

This generates implementation files in the `templates/` directory!

## 7. Use in Claude Code Sessions

Now just use Claude Code normally! The meta-agent will track your activities and alert you when patterns emerge.

**Tell Claude:**
- "Run the meta-agent analysis"
- "Show me what the meta-agent detected"
- "Generate a meta-agent report"

## Next Steps

1. **Add Slash Commands** (optional):
   ```bash
   # If you want /meta-analyze, /meta-report, etc.
   mkdir -p ~/.claude/commands
   ln -s /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent/commands/* ~/.claude/commands/
   ```

2. **Set Up Weekly Reports** (optional):
   ```bash
   # Add to crontab for automatic weekly analysis
   crontab -e
   # Add: 0 9 * * 1 cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent && python3 weekly_report.py
   ```

3. **Customize Configuration**:
   ```bash
   # Edit config.json to adjust thresholds and behavior
   vim config.json
   ```

## What's Happening Behind the Scenes

1. **Activity Tracking**: Every action is logged to JSONL files
2. **Hash Indexing**: Duplicates are detected with MD5 hashes
3. **Pattern Detection**: Similarities found with sequence matching
4. **Proposal Generation**: Impact analysis computed automatically
5. **Threshold Triggering**: Alerts when 3+ similar actions detected

## Verify It's Working

Check the logs:
```bash
ls -lh logs/
cat logs/session_*.jsonl | head
```

Check detected patterns:
```bash
cat patterns/detected_patterns.json
```

Check proposals:
```bash
ls proposals/
cat proposals/proposal_*.json
```

## Tips

- **Be Patient**: Patterns emerge naturally over time
- **Use Normally**: Don't force patterns, just work naturally
- **Review Proposals**: Not all patterns need skills, approve selectively
- **Resource Conscious**: The system is designed to be lightweight
- **Incremental**: Analysis only looks at recent 7 days

## Troubleshooting

**Import errors?**
```bash
# Ensure Python 3 is available
python3 --version

# All dependencies are standard library, no pip install needed!
```

**Permission errors?**
```bash
chmod +x *.py
```

**Want to start fresh?**
```bash
# Backup first!
mv logs logs.backup
mv patterns patterns.backup
mv proposals proposals.backup

# Create fresh directories
mkdir logs patterns proposals
```

## Success Indicators

You'll know it's working when:
- ✓ Activity logs are being created in `logs/`
- ✓ Pattern analysis finds similarities
- ✓ Proposals are generated with impact estimates
- ✓ Approving proposals creates implementation files
- ✓ You save time using the generated skills!

---

**Ready to go!** The meta-agent is now monitoring your Claude Code usage. Just work normally and let it discover optimization opportunities for you.
