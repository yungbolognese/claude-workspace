#!/bin/bash
# Service Health Check Script
# Monitors which services are running and responding

LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"

DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/services-$DATE.log"

echo "=== Service Health Check ===" | tee -a "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check Ollama
echo "Ollama (LLM):" | tee -a "$LOG_FILE"
if curl -s localhost:11434/api/version &>/dev/null; then
    VERSION=$(curl -s localhost:11434/api/version 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo "  ✅ Running (version: $VERSION)" | tee -a "$LOG_FILE"
    MODELS=$(curl -s localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | wc -l)
    echo "  📦 Models loaded: $MODELS" | tee -a "$LOG_FILE"
else
    echo "  ❌ Not running" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Check Pi-hole
echo "Pi-hole (DNS/Ad Blocking):" | tee -a "$LOG_FILE"
if curl -s localhost/admin &>/dev/null; then
    echo "  ✅ Running" | tee -a "$LOG_FILE"
elif docker ps | grep -q pihole; then
    echo "  ✅ Running (Docker)" | tee -a "$LOG_FILE"
else
    echo "  ❌ Not running" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Check Syncthing
echo "Syncthing (File Sync):" | tee -a "$LOG_FILE"
if curl -s localhost:8384 &>/dev/null; then
    echo "  ✅ Running" | tee -a "$LOG_FILE"
else
    echo "  ❌ Not running" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Check Tailscale
echo "Tailscale (VPN/Remote Access):" | tee -a "$LOG_FILE"
if command -v tailscale &>/dev/null; then
    STATUS=$(tailscale status --json 2>/dev/null | grep -o '"BackendState":"[^"]*"' | cut -d'"' -f4)
    if [ "$STATUS" = "Running" ]; then
        echo "  ✅ Running" | tee -a "$LOG_FILE"
        IP=$(tailscale ip 2>/dev/null | head -1)
        echo "  🌐 IP: $IP" | tee -a "$LOG_FILE"
    else
        echo "  ⚠️  Installed but not running" | tee -a "$LOG_FILE"
    fi
else
    echo "  ❌ Not installed" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Docker containers
echo "Docker Containers:" | tee -a "$LOG_FILE"
if command -v docker &>/dev/null; then
    RUNNING=$(docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | tail -n +2)
    if [ -n "$RUNNING" ]; then
        echo "$RUNNING" | awk '{printf "  ✅ %-20s %s\n", $1, $2" "$3}' | tee -a "$LOG_FILE"
    else
        echo "  📦 No containers running" | tee -a "$LOG_FILE"
    fi
else
    echo "  ❌ Docker not installed" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "Logged to: $LOG_FILE"
