#!/bin/bash
# monitor_job.sh - Wrapper to run commands and alert on failure
# Usage: ./monitor_job.sh "My Job Name" "/path/to/log.log" "actual command..."

JOB_NAME="$1"
LOG_FILE="$2"
shift 2
COMMAND="$@"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "---------------------------------------------------" >> "$LOG_FILE"
echo "START: $JOB_NAME at $(date)" >> "$LOG_FILE"

# Run command
eval "$COMMAND" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "END: $JOB_NAME at $(date) with Exit Code: $EXIT_CODE" >> "$LOG_FILE"

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ FAILURE DETECTED. Sending alert..." >> "$LOG_FILE"
    
    # Python notifier path (assuming standard structure)
    NOTIFIER_SCRIPT="$HOME/ztrader/scripts/utils/notify_error.py"
    PYTHON_EXEC="$HOME/ztrader/venv/bin/python"
    
    if [ -f "$NOTIFIER_SCRIPT" ]; then
        $PYTHON_EXEC "$NOTIFIER_SCRIPT" "$JOB_NAME" "$LOG_FILE" >> "$LOG_FILE" 2>&1
    else
        echo "Error: Notifier script not found at $NOTIFIER_SCRIPT" >> "$LOG_FILE"
    fi
fi

exit $EXIT_CODE
