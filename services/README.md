# Services Configuration

Self-hosted services running on Mac mini M4 for local-first development.

## Current Status

**Phase**: Discovery (Week 1-4)
**Running**: None (baseline measurement)

## Planned Services

### Week 1: LLM Testing
- [ ] **Ollama**: Local LLM inference (see [ollama/](ollama/))

### Week 2: Network Services
- [ ] **Pi-hole**: Network-wide ad blocking (see [pihole/](pihole/))
- [ ] **Syncthing**: P2P file synchronization (see [syncthing/](syncthing/))
- [ ] **Tailscale**: Secure remote access

### Week 3+: TBD
Based on discovery findings.

## Service Template

Each service directory contains:
```
service-name/
├── README.md          # Setup instructions
├── config/            # Configuration files
├── docker-compose.yml # Docker setup (if applicable)
└── notes.md           # Personal notes and learnings
```

## Resource Tracking

Track each service's impact:

| Service | RAM | Disk | Bandwidth | Value | Status |
|---------|-----|------|-----------|-------|--------|
| Ollama (7B) | ~6GB | 4GB | 0 | TBD | Testing |
| Pi-hole | ~500MB | 100MB | Saves BW | TBD | Not Started |
| Syncthing | ~200MB | Varies | P2P | TBD | Not Started |

Update this table weekly during discovery phase.

## Installation Order

1. **Week 1**: Ollama (local LLM)
2. **Week 2**: Pi-hole, Syncthing, Tailscale (network services)
3. **Week 3**: Based on meta-agent recommendations
4. **Week 4**: Evaluate and decide what to keep

## Bandwidth Considerations

Your internet bandwidth is limited. Services are categorized by bandwidth usage:

**Zero Bandwidth** (Local Only):
- ✅ Ollama (LLM)
- ✅ Local databases
- ✅ Git servers (Gitea)

**Saves Bandwidth**:
- ✅ Pi-hole (blocks ads/trackers)
- ✅ macOS Content Caching

**Low Bandwidth**:
- ⚠️ Syncthing (P2P, only when syncing)
- ⚠️ Tailscale (minimal overhead)
- ⚠️ Vaultwarden (password sync)

**High Bandwidth** (Avoid):
- ❌ Public-facing web servers
- ❌ Video streaming
- ❌ Continuous cloud backups

## Mac mini M4 Capacity

**Available Resources**:
- 16GB RAM (after macOS overhead: ~14GB usable)
- 256GB SSD (keep 50GB free: ~200GB usable)
- 6W idle power (~$2-3/month electricity)

**Rule of Thumb**:
- Keep total RAM usage under 12GB
- Leave headroom for interactive work
- Monitor with `./monitoring/resources.sh`

## Health Checks

Run service health checks:
```bash
./monitoring/services.sh
```

This shows which services are running and responding.

## Adding a New Service

1. Create directory: `mkdir service-name`
2. Add `service-name/README.md` with setup instructions
3. Test and monitor for 1 week
4. Document findings in `docs/week-N.md`
5. Decide: Keep or Remove

## Removing a Service

If a service isn't providing value:
1. Document why in `docs/week-N.md`
2. Stop the service
3. Uninstall completely (don't leave zombies)
4. Update this README

## Notes

- **Always measure before and after** adding a service
- **One service at a time** during discovery
- **Give each service a fair trial** (at least 1 week of actual use)
- **Be honest about usage** (installed ≠ used)

---

**Last Updated**: 2026-04-08
**Services Running**: 0
**Total RAM Used**: 0 GB
**Total Bandwidth Impact**: Baseline (measuring)
