#!/bin/bash
# Wait for current 1d sync to complete, then sync remaining timeframes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$PROJECT_ROOT"

echo "========================================="
echo "Waiting for 1d sync to complete..."
echo "========================================="

# Wait for the current sync process to finish
# Check if sync_data.py is running
while pgrep -f "sync_data.py.*1d" > /dev/null; do
    echo "1d sync still running... ($(date +%H:%M:%S))"
    sleep 30
done

echo "✓ 1d sync completed!"
echo

# Now sync the remaining timeframes
REMAINING_TIMEFRAMES=("1h" "15m" "5m" "1m")

for tf in "${REMAINING_TIMEFRAMES[@]}"; do
    echo
    echo "========================================="
    echo "Syncing timeframe: $tf"
    echo "Started: $(date)"
    echo "========================================="
    
    python3 "$PROJECT_ROOT/sync_data.py" --timeframe "$tf" --full --workers 1
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully synced $tf"
    else
        echo "✗ Failed to sync $tf"
    fi
    
    # Delay between timeframes to avoid rate limiting
    echo "Waiting 60 seconds before next timeframe..."
    sleep 60
done

echo
echo "========================================="
echo "All timeframes synced!"
echo "Completed: $(date)"
echo "========================================="
