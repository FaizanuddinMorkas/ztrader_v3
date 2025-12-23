#!/bin/bash
# Automated multi-timeframe data sync
# This script will sync all timeframes sequentially

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$PROJECT_ROOT"

echo "========================================="
echo "Multi-Timeframe Data Sync"
echo "========================================="
echo "Project: $PROJECT_ROOT"
echo "Started: $(date)"
echo "========================================="
# Timeframes to sync (in order of priority)
TIMEFRAMES=("1d" "1h" "30m" "15m" "5m" "1m")

# Function to get period for timeframe
get_period() {
    case "$1" in
        "1d")  echo "1y" ;;      # Daily: 1 year
        "1h")  echo "6mo" ;;     # Hourly: 6 months
        "30m") echo "120d" ;;    # 30-min: 120 days
        "15m") echo "90d" ;;     # 15-min: 90 days
        "5m")  echo "60d" ;;     # 5-min: 60 days
        "1m")  echo "15d" ;;     # 1-min: 15 days
        *)     echo "1y" ;;      # Default
    esac
}

for tf in "${TIMEFRAMES[@]}"; do
    period=$(get_period "$tf")
    
    echo
    echo "========================================="
    echo "Syncing timeframe: $tf (period: $period)"
    echo "Started: $(date)"
    echo "========================================="
    
    python3 "$PROJECT_ROOT/sync_data.py" --timeframe "$tf" --period "$period" --full --workers 1
    
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✓ Successfully synced $tf"
    else
        echo "✗ Failed to sync $tf (exit code: $exit_code)"
        echo "Continuing with next timeframe..."
    fi
    
    echo "Completed: $(date)"
    echo
    
    # Add a small delay between timeframes
    sleep 5
done

echo
echo "========================================="
echo "All timeframes synced!"
echo "Completed: $(date)"
echo "========================================="
