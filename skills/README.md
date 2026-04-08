# Claude Code Skills Library

Global skills that can be used across all your Claude Code projects.

## Location

```
/Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-skills
```

## Available Skills

### /github - Intelligent Git/GitHub Operations

Complete git and GitHub workflow automation with smart commit messages, PR generation, and safety features.

**Usage:**
```
/github commit [message]          - Smart commit with auto-generated messages
/github sync [message]            - Pull, commit, push in one command
/github push [branch] [--force]   - Push with safety checks
/github pr create                 - Create PR with auto-generated content
/github help                      - Show all commands
```

[Full documentation](github.md)

## Setup

### Option 1: Link to Specific Project

```bash
cd /path/to/your/project
mkdir -p .claude/commands
ln -s /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-skills/github.md .claude/commands/
```

### Option 2: Global Installation (All Projects)

Create a symlink in your user Claude commands directory:

```bash
mkdir -p ~/.claude/commands
ln -s /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-skills/github.md ~/.claude/commands/
```

### Option 3: Use Directly in Claude Code

Just reference the skill in your conversation:
```
Please use the github skill to commit these changes
```

Claude Code can access skills via path reference.

## How It Works

Skills are markdown files that provide instructions to Claude Code on how to execute specific workflows.

Each skill:
- Defines a command interface
- Provides intelligent parsing of user requests
- Implements workflow logic with safety checks
- Handles errors gracefully
- Provides helpful output

## Creating New Skills

When the meta-agent detects patterns, it can propose new skills.

To create a skill manually:

1. Create `skillname.md` in this directory
2. Follow the pattern: command parsing → workflow execution → output
3. Include help documentation
4. Add entry to this README

## Skill Development Workflow

Using the meta-agent with the /github skill:

1. Work on projects naturally
2. Meta-agent detects patterns
3. Meta-agent proposes new skills
4. Approve and generate skill files
5. Use /github skill to commit new skills to this repo
6. New skills become available across all projects

This creates a positive feedback loop of continuous workflow improvement!

## Skills vs Slash Commands

**Skills** (this directory):
- Reusable across projects
- Stored centrally
- Version controlled
- Shared/portable

**Project Slash Commands** (`.claude/commands/`):
- Project-specific
- Local to one project
- Not shared

Use this skills library for general-purpose workflows you use frequently across projects.

## Updating Skills

Skills can be updated anytime:

```bash
cd /Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-skills

# Edit the skill
vim github.md

# Commit the update using the skill itself!
# In Claude Code:
/github commit "Update github skill with new feature"
```

## Contributing

As you discover useful patterns:

1. Create the skill in this directory
2. Document it in this README
3. Test it across projects
4. Commit and share!

---

**Version:** 1.0
**Location:** `/Users/danielchoe/Library/CloudStorage/Dropbox/Github/.claude-skills`
