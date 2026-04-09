# Next Steps: Connecting MacBook to Mac mini Ollama

**Status**: Ready to connect and test hybrid LLM strategy
**Current Phase**: Week 1 - Baseline & LLM Testing
**Last Updated**: 2026-04-08

## What We've Accomplished So Far

✅ Created unified `claude-workspace` repository
✅ Merged meta-agent + skills + services into one repo
✅ Set up 4-week discovery plan with documentation
✅ Created monitoring scripts (bandwidth, resources, services)
✅ Pushed to GitHub: https://github.com/yungbolognese/claude-workspace
✅ Installed GitHub CLI (can now create repos automatically!)
✅ You already have Ollama running on Mac mini

## Current Situation

- **Mac mini M4**: Ollama installed and running
- **MacBook Pro**: Primary development machine (where you are now)
- **Goal**: Connect MacBook to Mac mini's Ollama for hybrid LLM workflow

## Next Session: Connect to Local Ollama

### Step 1: Make Ollama Network-Accessible (On Mac mini)

Ollama currently only listens on localhost. Need to make it accessible from MacBook.

**On Mac mini, create LaunchAgent:**

```bash
# Create the plist file
cat > ~/Library/LaunchAgents/com.ollama.server.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OLLAMA_HOST</key>
        <string>0.0.0.0:11434</string>
        <key>OLLAMA_ORIGINS</key>
        <string>*</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ollama.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ollama.err</string>
</dict>
</plist>
EOF

# Stop current Ollama
killall ollama

# Load the LaunchAgent
launchctl load ~/Library/LaunchAgents/com.ollama.server.plist

# Verify it's listening on all interfaces
lsof -i :11434
```

### Step 2: Find Mac mini IP Address

```bash
# On Mac mini
ipconfig getifaddr en0
# Example output: 192.168.1.100
```

### Step 3: Test Connection from MacBook

```bash
# On MacBook Pro (replace with actual IP)
curl http://192.168.1.100:11434/api/tags

# Should show your installed models
```

### Step 4: Create Switch Scripts (On MacBook)

```bash
# On MacBook Pro
cat > ~/switch-llm.sh <<'EOF'
#!/bin/bash

# Use local Ollama (Mac mini)
function claude-local() {
    export ANTHROPIC_AUTH_TOKEN=ollama
    export ANTHROPIC_API_KEY=""
    export ANTHROPIC_BASE_URL=http://192.168.1.100:11434  # Update with your IP
    export ANTHROPIC_MODEL=qwen2.5:7b  # Update with your model
    echo "🏠 Using Ollama (Mac mini) - Model: $ANTHROPIC_MODEL"
}

# Use Claude API
function claude-api() {
    unset ANTHROPIC_BASE_URL
    export ANTHROPIC_AUTH_TOKEN=<your-claude-token>  # Add your token
    unset ANTHROPIC_MODEL
    echo "☁️  Using Claude API"
}

# Check current config
function claude-status() {
    echo "Base URL: ${ANTHROPIC_BASE_URL:-api.anthropic.com}"
    echo "Model: ${ANTHROPIC_MODEL:-claude-sonnet-4}"
    echo "Auth: ${ANTHROPIC_AUTH_TOKEN:0:10}..."
}

# Show this help
echo "Available commands:"
echo "  claude-local  - Use Ollama on Mac mini"
echo "  claude-api    - Use Claude API"
echo "  claude-status - Show current configuration"
EOF

chmod +x ~/switch-llm.sh

# Add to your shell profile
echo "source ~/switch-llm.sh" >> ~/.zshrc
source ~/.zshrc
```

### Step 5: Test Hybrid Workflow

```bash
# On MacBook Pro

# Start with local Ollama
claude-local
claude  # Launch Claude Code using Ollama

# Try a simple task
# Prompt: "Write a Python function to calculate fibonacci"

# Then switch to API for complex task
claude-api
claude  # Launch Claude Code using API

# Try a complex task
# Prompt: "Design a microservices architecture for an e-commerce platform"

# Compare quality and speed
```

### Step 6: Document Findings in Week 1

Create `docs/week-1.md` and track:
- [ ] Mac mini IP address
- [ ] Models you have installed
- [ ] Tokens/sec for each model
- [ ] Quality comparison (Ollama vs Claude) for different task types
- [ ] When you switched from Ollama to Claude (and why)
- [ ] Cost estimate based on actual usage

## The Hybrid Strategy

### Use Ollama (Mac mini) For:
- ✅ Simple code completion
- ✅ Boilerplate generation
- ✅ Quick refactoring within a file
- ✅ Writing simple tests
- ✅ Documentation generation
- ✅ Code formatting

**Pros**: Free, private, fast, offline
**Cons**: ~70-80% quality of Claude, limited context

### Use Claude API For:
- ✅ Architecture decisions
- ✅ Complex debugging
- ✅ Multi-file refactors
- ✅ Learning/explanations
- ✅ Critical production code
- ✅ When stuck on hard problems

**Pros**: Superior quality, better reasoning
**Cons**: Costs $50-100/month, requires internet

### Expected Savings:
- **Before**: $60-150/month (pure Claude API)
- **After**: $15-30/month (80% Ollama, 20% Claude)
- **Savings**: $45-120/month
- **Mac mini ROI**: 6-12 months

## Week 1 Goals (Updated)

- [x] Install Ollama on Mac mini (already done!)
- [ ] Make Ollama network-accessible
- [ ] Connect MacBook to Mac mini Ollama
- [ ] Test 3 task types on Ollama vs Claude
- [ ] Document quality differences
- [ ] Track actual usage patterns
- [ ] Decide on hybrid routing strategy
- [ ] Run baseline bandwidth measurements
- [ ] Run baseline resource measurements

## Questions to Answer This Week

1. What's your Mac mini's IP address?
2. What models do you have installed on Ollama?
3. For simple tasks, is Ollama quality acceptable?
4. For complex tasks, when do you need to switch to Claude?
5. What % of your work could realistically use Ollama?
6. How much would this save you per month?

## Resources for Reference

**Guides:**
- [Mac mini Ollama Network Access](https://medium.com/@szz185/how-to-make-ollama-accessible-on-the-local-network-with-a-mac-mini-m-4-15e2d5364fdc)
- [Hybrid Workflow Benchmarks](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark)
- [Claude Code + Ollama Integration](https://docs.ollama.com/integrations/claude-code)
- [Hybrid Strategy Guide](https://docs.bswen.com/blog/2026-03-23-hybrid-claude-local-llm-workflow/)

**Key Stats:**
- Mac mini 16GB can handle up to ~13B models
- Qwen 2.5 7B: ~28-35 tok/s (good daily driver)
- Ollama needs 0.14.3-rc1+ for Claude Code integration
- Hybrid approach can save 50-80% on API costs

## After Week 1

Once you've tested the connection and documented findings:
1. Create GitHub issue for Week 2
2. Meta-agent will analyze your usage patterns
3. Decide if hybrid approach is worth continuing
4. Potentially create a skill for automatic routing

## Files to Update

- `docs/week-1.md` - Your findings
- `services/ollama/README.md` - Add network setup steps
- `monitoring/services.sh` - Add Ollama remote check
- GitHub issue for Week 1 - Mark tasks complete

---

**Ready to resume?** Start with Step 1 on your Mac mini!

**Last session**: 2026-04-08 - Set up workspace, researched hybrid strategy
**Next session**: Connect MacBook to Mac mini Ollama and test
