#!/bin/bash
# Setup cron job for daily workflow on EC2
# Runs at 4:00 PM IST daily (after market close) on weekdays only

set -e

echo "Setting up daily workflow cron job..."
echo ""

# Define the cron entry
# Runs Monday-Friday at 7:00 PM IST
CRON_ENTRY="0 19 * * 1-5 cd ~/ztrader && source venv/bin/activate && python scripts/daily_workflow.py --no-notify >> logs/daily_workflow.log 2>&1"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "daily_workflow.py"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove old entry and add new one
    (crontab -l 2>/dev/null | grep -v "daily_workflow.py"; echo "$CRON_ENTRY") | crontab -
else
    echo "Adding new cron job..."
    # Add to existing crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
fi

echo ""
echo "✅ Cron job configured successfully!"
echo ""
echo "Schedule: Monday-Friday at 7:00 PM IST"
echo "Command: python scripts/daily_workflow.py --no-notify"
echo "Log file: ~/ztrader/logs/daily_workflow.log"
echo ""
echo "Current crontab:"
crontab -l
echo ""
echo "To view logs:"
echo "  tail -f ~/ztrader/logs/daily_workflow.log"
echo ""
echo "To manually run workflow:"
echo "  cd ~/ztrader && source venv/bin/activate && python scripts/daily_workflow.py --no-notify"
