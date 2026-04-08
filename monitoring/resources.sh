#!/bin/bash
# Resource Monitoring Script
# Tracks CPU, RAM, disk usage to understand Mac mini capacity

LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)
LOG_FILE="$LOG_DIR/resources-$DATE.log"

echo "=== Mac mini M4 Resources ===" | tee -a "$LOG_FILE"
echo "Timestamp: $DATE $TIME" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Memory
echo "Memory Usage:" | tee -a "$LOG_FILE"
vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f MB\n", "$1:", $2 * $size / 1048576);' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Memory Pressure
echo "Memory Pressure:" | tee -a "$LOG_FILE"
memory_pressure | grep "System-wide memory" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# CPU
echo "CPU Usage:" | tee -a "$LOG_FILE"
top -l 1 | grep "CPU usage" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Disk
echo "Disk Usage:" | tee -a "$LOG_FILE"
df -h / | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Top Processes by Memory
echo "Top 5 Processes (by Memory):" | tee -a "$LOG_FILE"
ps aux | sort -k 4 -r | head -6 | awk '{printf "%-20s %6s %6s %s\n", $1, $3"%", $4"%", $11}' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Ollama status (if running)
if pgrep -x "ollama" > /dev/null; then
    echo "Ollama Status: ✅ Running" | tee -a "$LOG_FILE"
    if command -v ollama &> /dev/null; then
        echo "Loaded Models:" | tee -a "$LOG_FILE"
        curl -s localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | tee -a "$LOG_FILE"
    fi
else
    echo "Ollama Status: ❌ Not Running" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "Logged to: $LOG_FILE"
