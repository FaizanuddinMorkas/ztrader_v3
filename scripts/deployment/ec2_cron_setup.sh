#!/bin/bash
# Setup Cron Jobs for ZTrader on EC2
# Run this script on the EC2 instance to configure scheduled tasks

echo "⏰ Setting up Cron Jobs for ZTrader..."

# Define the cron file content
# Note: EC2 is typically in UTC. Times below are converted from IST.
# IST is UTC + 5:30
# 9:30 AM IST  -> 04:00 UTC
# 11:45 AM IST -> 06:15 UTC
# 2:00 PM IST  -> 08:30 UTC

cat << EOF > ~/ztrader_cron
# ==================================================================
# ZTrader Scheduled Tasks
# ==================================================================

# 1. MORNING REPORT (9:30 AM IST / 4:00 AM UTC)
#    Sends Market Overview, Gainers, Losers, etc.
0 4 * * 1-5 bash ~/ztrader/scripts/deployment/monitor_job.sh "Morning Report" ~/ztrader/logs/report_morning.log "cd ~/ztrader && /home/ubuntu/ztrader/venv/bin/python scripts/telegram/send_market_reports.py"

# 2. MID-DAY REPORT (11:45 AM IST / 6:15 AM UTC)
#    Mid-session market update
15 6 * * 1-5 bash ~/ztrader/scripts/deployment/monitor_job.sh "Mid-Day Report" ~/ztrader/logs/report_midday.log "cd ~/ztrader && /home/ubuntu/ztrader/venv/bin/python scripts/telegram/send_market_reports.py"

# 3. AFTERNOON REPORT (2:00 PM IST / 8:30 AM UTC)
#    Post-lunch market pulse
30 8 * * 1-5 bash ~/ztrader/scripts/deployment/monitor_job.sh "Afternoon Report" ~/ztrader/logs/report_afternoon.log "cd ~/ztrader && /home/ubuntu/ztrader/venv/bin/python scripts/telegram/send_market_reports.py"

# 4. MARKET CLOSE REPORT (5:00 PM IST / 11:30 AM UTC)
#    End-of-day market summary (before daily sync)
30 11 * * 1-5 bash ~/ztrader/scripts/deployment/monitor_job.sh "Closing Report" ~/ztrader/logs/report_close.log "cd ~/ztrader && /home/ubuntu/ztrader/venv/bin/python scripts/telegram/send_market_reports.py"

# 5. DAILY WORKFLOW (6:00 PM IST / 12:30 PM UTC)
#    Syncs market data, generates signals, and notifies users
30 12 * * 1-5 bash ~/ztrader/scripts/deployment/monitor_job.sh "Daily Workflow" ~/ztrader/logs/daily_workflow.log "cd ~/ztrader && /home/ubuntu/ztrader/venv/bin/python scripts/daily_workflow.py"

# ==================================================================
EOF

# Install the new crontab
crontab ~/ztrader_cron
rm ~/ztrader_cron

echo "✅ Cron jobs installed successfully!"
echo ""
echo "Current Cron Schedule (crontab -l):"
echo "---------------------------------------------------"
crontab -l
echo "---------------------------------------------------"
echo "Logs will be written to ~/ztrader/logs/"
