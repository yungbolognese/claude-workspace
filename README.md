# Claude Workspace

Personal development workspace with AI-powered workflow optimization and local-first services.

## Overview

This workspace combines:
- **Meta-agent**: Detects patterns in your workflow and proposes automation
- **Skills**: Growing collection of reusable Claude Code skills
- **Services**: Self-hosted services running on Mac mini M4
- **Discovery**: Phased exploration of what works for your setup

## Current Phase: Discovery (Week 1-4)

We're in the **exploration phase** to understand:
- What services your Mac mini M4 16GB can handle
- What bandwidth constraints exist
- What workflows are actually repetitive
- What should be automated vs manual

See [DISCOVERY.md](docs/DISCOVERY.md) for the full plan.

## Repository Structure

```
claude-workspace/
├── meta-agent/           # Pattern detection system
│   ├── tracker.py       # Activity logging
│   ├── pattern_detector.py
│   ├── skill_proposer.py
│   └── meta_agent.py
│
├── skills/              # Claude Code skills collection
│   ├── github.md       # Git/GitHub operations
│   └── ...             # More skills as patterns emerge
│
├── services/            # Service configurations
│   ├── ollama/         # Local LLM setup
│   ├── syncthing/      # P2P file sync
│   ├── pihole/         # Network ad blocking
│   └── README.md       # Service documentation
│
├── monitoring/          # Resource monitoring scripts
│   ├── bandwidth.sh    # Track internet usage
│   ├── resources.sh    # Monitor RAM/CPU
│   └── services.sh     # Health checks
│
└── docs/               # Discovery documentation
    ├── DISCOVERY.md    # 4-week discovery plan
    ├── week-1.md       # Week 1 notes
    ├── week-2.md       # Week 2 notes
    ├── week-3.md       # Week 3 notes
    └── week-4.md       # Week 4 notes
```

## Quick Start

### Phase 1: Minimal Setup (Week 1)

**On Mac mini:**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a 7B model
ollama pull qwen2.5:7b

# 3. Test it
ollama run qwen2.5:7b "Hello!"

# 4. Clone this workspace
cd ~/Dropbox/Github
git clone git@github.com:yungbolognese/claude-workspace.git
```

**On laptop:**
```bash
# Access Mac mini LLM from Claude Code
# (Dropbox auto-syncs the workspace)
```

See [docs/DISCOVERY.md](docs/DISCOVERY.md) for detailed week-by-week plans.

## Tracking Progress

We track discovery progress using:
- **GitHub Issues**: Tasks and experiments to run
- **Weekly Docs**: Findings and decisions (in `docs/`)
- **Meta-agent Logs**: Automatic pattern detection

### Current Goals

See [DISCOVERY.md](docs/DISCOVERY.md#goals) for week-by-week goals.

## Hardware

**Mac mini M4 (Base Model):**
- 16GB RAM (not upgradeable)
- 256GB SSD
- M4 chip (10-core CPU, 10-core GPU)
- ~6-7W idle power
- Active cooling (24/7 capable)

**Constraints:**
- Limited internet bandwidth
- 16GB RAM limits concurrent services
- 256GB storage (upgradeable SSD)

## Principles

1. **Local-first**: Work happens locally, sync only when needed
2. **Measure before expanding**: Track bandwidth and resources before adding services
3. **Pattern-driven**: Let meta-agent detect what to automate
4. **Phased discovery**: Don't over-engineer, learn what works

## License

MIT

---

**Status**: 🔬 Discovery Phase (Week 1 of 4)
**Last Updated**: 2026-04-08
