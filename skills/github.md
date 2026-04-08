# GitHub Skill

Intelligent GitHub/git operations with smart workflows and safety features.

## Parse User Command

Extract the command and arguments from the user's request:

```
Pattern matching:
/github <command> [args...]
```

## Command Router

Based on the parsed command, execute the appropriate workflow below:

---

## HELP Command

If command is "help" [args]:
- If no args: Show complete command list with categories
- If args provided: Show detailed help for that specific command
- Include examples and common use cases

---

## COMMIT Command

If command is "commit" [message]:

### Step 1: Analyze Changes
Run in parallel:
```bash
git status
git diff
git diff --staged
```

### Step 2: Generate Commit Message
If no message provided:
- Analyze the diffs to understand what changed
- Check `git log --oneline -5` to match commit style
- Generate a clear, descriptive message that explains:
  - What changed (files/features)
  - Why it changed (purpose)
  - Impact (what it enables/fixes)
- Use imperative mood ("Add feature" not "Added feature")

If message provided:
- Use the provided message

### Step 3: Stage and Commit
```bash
# Add all untracked and modified files (excluding .gitignore)
git add .

# Commit with message
git commit -m "$(cat <<'EOF'
[Generated or provided commit message]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Show result
git status
git log -1 --stat
```

---

## SYNC Command

If command is "sync" [message]:

Full workflow: pull → commit → push

```bash
# Pull latest
git pull --rebase

# Commit (use commit workflow above)
[Run commit command]

# Push
git push

echo "✓ Fully synced with remote"
```

---

## PUSH Command

If command is "push" [branch] [flags]:

### Safety Check
```bash
current_branch=$(git branch --show-current)
if [[ "$current_branch" == "main" || "$current_branch" == "master" ]] && [[ "$flags" == *"--force"* ]]; then
  echo "⚠️  WARNING: Force push to $current_branch"
  echo "This will rewrite history. Are you sure?"
  # Require explicit confirmation
fi
```

### Execute Push
```bash
# Show what will be pushed
git log origin/$(git branch --show-current)..HEAD --oneline

# Push
git push ${branch:+origin $branch} $flags

echo "✓ Pushed to remote"
```

---

## PULL Command

If command is "pull" [remote] [branch]:

```bash
# Stash if there are changes
if [[ -n $(git status -s) ]]; then
  git stash push -m "Auto-stash before pull"
  stashed=true
fi

# Pull
git pull ${remote:-origin} ${branch:-$(git branch --show-current)}

# Pop stash if we stashed
if [[ "$stashed" == "true" ]]; then
  git stash pop
fi

echo "✓ Pulled latest changes"
```

---

## STATUS Command

If command is "status":

```bash
git status
echo ""
echo "Recent commits:"
git log --oneline -5
```

---

## DIFF Command

If command is "diff" [file] [flags]:

```bash
if [[ "$flags" == *"--staged"* ]]; then
  git diff --staged ${file}
else
  git diff ${file}
fi
```

---

## LOG Command

If command is "log" [flags] [count]:

```bash
# Parse flags
oneline=""
count="10"

if [[ "$flags" == *"--oneline"* ]]; then
  oneline="--oneline"
fi

if [[ "$flags" =~ -n[[:space:]]*([0-9]+) ]]; then
  count="${BASH_REMATCH[1]}"
fi

git log $oneline -$count
```

---

## BRANCH Command

If command is "branch" [name] [flags]:

```bash
if [[ "$flags" == "-l" ]]; then
  # List branches
  git branch -a
elif [[ "$flags" == "-d" ]]; then
  # Delete branch
  git branch -d $name
else
  # Create and switch to new branch
  git checkout -b $name
fi
```

---

## CHECKOUT Command

If command is "checkout" [target]:

```bash
# Check if it's a branch or file
if git rev-parse --verify "$target" >/dev/null 2>&1; then
  # It's a branch
  git checkout $target
else
  # It's a file
  git checkout -- $target
fi
```

---

## MERGE Command

If command is "merge" [branch] [flags]:

```bash
git merge $branch $flags
echo "✓ Merged $branch"
```

---

## PR Command (GitHub CLI)

If command is "pr" [subcommand] [args]:

Requires `gh` CLI installed.

### pr create
```bash
if [[ "$args" ]]; then
  gh pr create $args
else
  # Interactive: analyze changes and generate PR title/body
  title=$(generate from current branch name and commits)
  body=$(generate from git log and diffs)

  gh pr create --title "$title" --body "$(cat <<'EOF'
## Summary
[Generated summary of changes]

## Test Plan
- [ ] Tested locally
- [ ] All tests pass
- [ ] Ready for review

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
  )"
fi
```

### pr list
```bash
gh pr list
```

### pr view [number]
```bash
gh pr view ${number}
```

### pr merge [number]
```bash
gh pr merge ${number}
```

---

## ISSUE Command (GitHub CLI)

If command is "issue" [subcommand] [args]:

### issue create
```bash
if [[ "$args" ]]; then
  gh issue create $args
else
  # Interactive
  echo "Title: "
  echo "Description: "
  # Get input and create
fi
```

### issue list
```bash
gh issue list
```

### issue view [number]
```bash
gh issue view ${number}
```

### issue close [number]
```bash
gh issue close ${number}
```

---

## REPO Command

If command is "repo" [subcommand] [args]:

### repo view
```bash
gh repo view
```

### repo create [name]
```bash
gh repo create $name
```

### repo clone [url]
```bash
gh repo clone $url
```

---

## WORKFLOW Command

If command is "workflow" [subcommand] [args]:

### workflow list
```bash
gh workflow list
```

### workflow run [name]
```bash
gh workflow run $name
```

### workflow view [id]
```bash
gh run view $id
```

---

## INIT Command

If command is "init":

```bash
git init
echo "✓ Initialized git repository"
```

---

## CLONE Command

If command is "clone" [url] [directory]:

```bash
git clone $url ${directory}
echo "✓ Cloned repository"
```

---

## REMOTE Command

If command is "remote" [subcommand] [args]:

```bash
git remote $subcommand $args
```

---

## STASH Command

If command is "stash" [subcommand]:

```bash
if [[ "$subcommand" == "pop" ]]; then
  git stash pop
elif [[ "$subcommand" == "list" ]]; then
  git stash list
else
  git stash
fi
```

---

## RESET Command

If command is "reset" [target] [flags]:

```bash
git reset $flags $target
```

---

## REVERT Command

If command is "revert" [commit]:

```bash
git revert $commit
```

---

## TAG Command

If command is "tag" [name] [flags]:

```bash
if [[ "$flags" == "-l" ]]; then
  git tag -l
else
  git tag $name
fi
```

---

## Error Handling

For any command:
- Catch errors and provide helpful messages
- Suggest fixes for common issues
- Show relevant git/gh help if needed

## Output Format

Always provide:
- Clear success/failure indicators (✓/✗)
- Relevant command output
- Next steps or suggestions
- Warnings for potentially dangerous operations

---

Now execute the user's GitHub command.
