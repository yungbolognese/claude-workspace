# Discovery Plan: Finding Your Optimal Workflow

**Duration**: 4 weeks
**Status**: Week 1 (Not Started)
**Goal**: Understand what services to run, what to automate, and what constraints matter

## Why Discovery First?

Instead of setting up everything upfront, we're taking a **measured approach**:
- Your Mac mini M4 has constraints (16GB RAM, limited bandwidth)
- You don't know what automation you need yet
- Over-engineering wastes time
- Meta-agent will tell us what's repetitive

## The Plan

### Week 1: Baseline & LLM Testing

**Goals:**
- [ ] Measure current bandwidth usage
- [ ] Set up local LLM on Mac mini
- [ ] Test different model sizes
- [ ] Start meta-agent tracking
- [ ] Document daily workflow

**Tasks:**
1. **Install Ollama** on Mac mini
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Test Models** (track performance):
   ```bash
   # Try 3B model (fast)
   ollama pull llama3.2:3b
   ollama run llama3.2:3b "Explain what a closure is"

   # Try 7B model (balanced)
   ollama pull qwen2.5:7b
   ollama run qwen2.5:7b "Explain what a closure is"

   # Try 12B model (quality)
   ollama pull gemma2:12b-instruct-q4_K_M
   ollama run gemma2:12b-instruct-q4_K_M "Explain what a closure is"
   ```

3. **Monitor Resources**:
   ```bash
   # While running models, track:
   - Tokens per second
   - RAM usage (Activity Monitor)
   - Feels responsive or sluggish?
   ```

4. **Measure Bandwidth**:
   ```bash
   # Install bandwidth monitor
   brew install nettop

   # Run for a day, note typical usage
   nettop -m tcp -t external
   ```

5. **Start Meta-Agent**:
   ```bash
   cd claude-workspace/meta-agent
   python3 meta_agent.py
   # It starts tracking your activities
   ```

**Deliverables:**
- `docs/week-1.md` with findings
- Decision: Which LLM model to use daily
- Baseline bandwidth measurement
- List of repetitive tasks noticed

---

### Week 2: Network Services

**Goals:**
- [ ] Set up Pi-hole (measure bandwidth savings)
- [ ] Install Syncthing for file sync
- [ ] Set up remote access (Tailscale)
- [ ] Monitor Mac mini resource usage

**Tasks:**
1. **Pi-hole Setup**:
   ```bash
   # Run via Docker
   docker run -d \
     --name pihole \
     -p 53:53/tcp -p 53:53/udp \
     -p 80:80 \
     -e TZ="America/Los_Angeles" \
     pihole/pihole:latest
   ```
   - Configure devices to use Mac mini as DNS
   - Track bandwidth savings for 1 week

2. **Syncthing**:
   ```bash
   brew install syncthing
   syncthing
   # Access at http://localhost:8384
   ```
   - Sync a test folder between Mac mini and laptop
   - Compare to Dropbox performance

3. **Tailscale**:
   ```bash
   brew install tailscale
   sudo tailscale up
   ```
   - Test remote access to Mac mini from outside network
   - Test LLM access remotely

4. **Monitoring**:
   ```bash
   # Create monitoring dashboard
   ./monitoring/resources.sh
   # Run daily, save to logs
   ```

**Deliverables:**
- `docs/week-2.md` with findings
- Pi-hole bandwidth savings data
- Syncthing vs Dropbox comparison
- Resource usage patterns documented

---

### Week 3: Development Workflow

**Goals:**
- [ ] Integrate Claude Code with Mac mini LLM
- [ ] Create first skill that uses local resources
- [ ] Review meta-agent pattern detection
- [ ] Identify automation candidates

**Tasks:**
1. **Claude Code + Ollama**:
   ```bash
   # Test accessing Mac mini Ollama from laptop
   # (via Tailscale or local network)
   curl http://mac-mini.local:11434/api/generate -d '{
     "model": "qwen2.5:7b",
     "prompt": "Write a Python function to parse JSON"
   }'
   ```

2. **Create Local LLM Skill**:
   - Create `skills/ask-local.md`
   - Skill that queries Mac mini LLM
   - Compare response quality vs Claude API

3. **Meta-Agent Review**:
   ```bash
   cd meta-agent
   python3 meta_agent.py report
   ```
   - What patterns did it detect?
   - What skills did it propose?
   - Are the proposals valuable?

4. **Manual Pattern Review**:
   - What did you do repeatedly this week?
   - What annoyed you?
   - What could be automated?

**Deliverables:**
- `docs/week-3.md` with findings
- At least 1 new skill created
- Meta-agent report review
- List of automation candidates

---

### Week 4: Evaluate & Decide

**Goals:**
- [ ] Review all data collected
- [ ] Decide what services to keep
- [ ] Plan Phase 2 (if needed)
- [ ] Document learnings

**Tasks:**
1. **Data Review**:
   - Bandwidth usage: Before and after
   - Services actually used vs installed
   - Mac mini RAM patterns
   - LLM usage frequency

2. **Decision Matrix**:
   Create table for each service:

   | Service | Used? | Bandwidth | RAM | Value | Keep? |
   |---------|-------|-----------|-----|-------|-------|
   | Ollama (7B) | Daily | 0 | 6GB | High | ✅ |
   | Pi-hole | Yes | Saves 25% | 500MB | High | ✅ |
   | Syncthing | Rarely | Low | 200MB | Low | ❌ |
   | ... | ... | ... | ... | ... | ... |

3. **Meta-Agent Analysis**:
   ```bash
   # Generate final report
   python3 meta_agent.py analyze
   python3 meta_agent.py report > docs/meta-agent-month1.md
   ```

4. **Plan Phase 2**:
   Based on learnings:
   - What to add next?
   - What automation is worth building?
   - What should stay manual?
   - Do you need always-on automation?

**Deliverables:**
- `docs/week-4.md` with final analysis
- Decision on what services to keep
- Phase 2 plan (or decision not to expand)
- Updated README with actual setup

---

## Success Metrics

### Must Track:
- **Bandwidth usage** (before/after each service)
- **RAM usage** (avg/peak for each service)
- **Actually used** (honest assessment)
- **Time saved** (estimate for each automation)

### Questions to Answer:
1. Which LLM model is your daily driver?
2. Does local LLM save money vs API calls?
3. What's your actual bandwidth constraint?
4. What patterns did meta-agent detect?
5. What services should run 24/7 vs on-demand?
6. Is Mac mini worth keeping on 24/7?

## Weekly Template

Each week, create `docs/week-N.md` with:

```markdown
# Week N: [Focus Area]

**Date**: [Start] to [End]
**Status**: [In Progress / Complete]

## Goals
- [ ] Goal 1
- [ ] Goal 2

## What I Did
- Activity 1
- Activity 2

## Measurements
- Bandwidth: X MB/day
- RAM usage: Y GB avg
- Services running: [list]

## Observations
- What worked well
- What didn't work
- Surprises

## Decisions
- Decision 1: [reasoning]
- Decision 2: [reasoning]

## Next Week
- Focus on...
- Try...
```

## GitHub Integration

Track progress using:

### 1. Issues (Optional)
Create issues for each week:
- `Week 1: Baseline & LLM Testing`
- `Week 2: Network Services`
- `Week 3: Development Workflow`
- `Week 4: Evaluate & Decide`

### 2. Weekly Docs (Required)
Write findings in `docs/week-N.md`

### 3. Project Board (Optional)
Create GitHub Project with columns:
- To Test
- Testing
- Keeping
- Discarding

## After Discovery

Based on Week 4 analysis, you'll decide:
- **Minimal Setup**: Keep only what you actually use
- **Expand**: Add more services based on proven value
- **Automation**: Build automation for detected patterns
- **Always-On**: Decide what truly needs 24/7 operation

The meta-agent will have enough data by then to propose meaningful automations based on YOUR actual usage, not theoretical needs.

---

**Start Date**: TBD
**Expected Completion**: 4 weeks from start
**Current Phase**: Not Started
