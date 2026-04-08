# Meta-Agent Activity Logging

Log an activity to the Claude Code Meta-Agent for pattern detection.

This command helps you manually log activities that the meta-agent should track:

**Log a command sequence:**
```python
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-meta-agent
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_command_sequence(
    ['git add .', 'git commit -m \"message\"', 'git push'],
    context='git workflow'
)
print('Logged command sequence')
"
```

**Log a code change:**
```python
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_code_change(
    file_path='/path/to/file.py',
    change_type='add_function',
    description='Added helper function'
)
print('Logged code change')
"
```

**Log project initialization:**
```python
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_project_init(
    project_path='/path/to/project',
    tech_stack=['python', 'fastapi', 'postgresql'],
    purpose='REST API'
)
print('Logged project init')
"
```

**Log research activity:**
```python
python3 -c "
from tracker import ActivityTracker
tracker = ActivityTracker()
tracker.log_research(
    topic='SwiftUI animations',
    sources=['apple docs', 'stack overflow'],
    outcome='learned spring animations'
)
print('Logged research')
"
```

Note: Most activities will be logged automatically when you use Claude Code. Manual logging is for when you want to explicitly track something.
