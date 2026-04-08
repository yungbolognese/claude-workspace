#!/bin/bash
# Bandwidth Monitoring Script
# Tracks network usage to understand internet constraints

LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"

DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/bandwidth-$DATE.log"

echo "=== Bandwidth Monitor ===" | tee -a "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check if nettop is available
if ! command -v nettop &> /dev/null; then
    echo "⚠️  nettop not found. Install with: brew install nettop" | tee -a "$LOG_FILE"
    exit 1
fi

# Current snapshot
echo "Current Network Activity:" | tee -a "$LOG_FILE"
nettop -m tcp -t external -l 1 -P | head -20 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Logged to: $LOG_FILE"

# Summary if previous day exists
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
if [ -f "$LOG_DIR/bandwidth-$YESTERDAY.log" ]; then
    echo ""
    echo "Tip: Compare with yesterday: diff $LOG_DIR/bandwidth-{$YESTERDAY,$DATE}.log"
fi
