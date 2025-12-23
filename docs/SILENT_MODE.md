# Silent Mode - Running Without Notifications

## Overview

The daily workflow and signal generation scripts now support a `--no-notify` flag that disables all Telegram notifications. This is useful for automated cron jobs where you don't want to receive notifications for every run.

## Usage

### Daily Signals Script

```bash
# Run with notifications (default)
python daily_signals_scored.py --sentiment

# Run without notifications
python daily_signals_scored.py --sentiment --no-notify

# Test mode (also disables notifications)
python daily_signals_scored.py --test
```

### Daily Workflow Script

```bash
# Run with notifications (default)
python scripts/daily_workflow.py

# Run without notifications
python scripts/daily_workflow.py --no-notify

# Skip sync and run without notifications
python scripts/daily_workflow.py --skip-sync --no-notify
```

## Behavior Comparison

| Flag | Signals Sent | Workflow Status Sent | Use Case |
|------|--------------|---------------------|----------|
| None (default) | ✅ Yes | ✅ Yes | Manual runs, testing |
| `--test` | ❌ No | ✅ Yes | Testing signal generation |
| `--no-notify` | ❌ No | ❌ No | Automated cron jobs |

## Setting Up Automated Runs on EC2

### 1. Deploy to EC2

```bash
./scripts/deploy_to_ec2.sh 65.2.153.114
```

### 2. SSH into EC2

```bash
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114
```

### 3. Set up Cron Job

```bash
cd ~/ztrader
./scripts/ec2_cron_setup.sh
```

This will configure a cron job that runs Monday-Friday at 7:00 PM IST (after market close).

### 4. Verify Cron Job

```bash
# View crontab
crontab -l

# Monitor logs
tail -f ~/ztrader/logs/daily_workflow.log
```

## Manual Testing

### Test Locally Without Notifications

```bash
# Test signal generation
python daily_signals_scored.py --symbols RELIANCE.NS --no-notify

# Test full workflow (skip sync for speed)
python scripts/daily_workflow.py --skip-sync --no-notify
```

### Test on EC2 Without Notifications

```bash
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114 \
  "cd ~/ztrader && source venv/bin/activate && python scripts/daily_workflow.py --skip-sync --no-notify"
```

## Cron Job Details

**Schedule**: Monday-Friday at 7:00 PM IST  
**Command**: `python scripts/daily_workflow.py --no-notify`  
**Log File**: `~/ztrader/logs/daily_workflow.log`

**Cron Expression**: `0 19 * * 1-5`
- `0` - Minute (0)
- `19` - Hour (7 PM)
- `*` - Day of month (any)
- `*` - Month (any)
- `1-5` - Day of week (Monday-Friday)

## Monitoring

### View Recent Logs

```bash
# Last 50 lines
tail -n 50 ~/ztrader/logs/daily_workflow.log

# Follow logs in real-time
tail -f ~/ztrader/logs/daily_workflow.log

# Search for errors
grep -i error ~/ztrader/logs/daily_workflow.log
```

### Check Cron Execution

```bash
# View cron logs (Ubuntu/Debian)
grep CRON /var/log/syslog | tail -20

# Check if workflow is running
ps aux | grep daily_workflow
```

## Best Practices

### For Automated Runs (Cron)
- ✅ Use `--no-notify` to avoid notification spam
- ✅ Log output to file for debugging
- ✅ Run after market close (7 PM IST)
- ✅ Run only on weekdays (Monday-Friday)

### For Manual Runs
- ✅ Enable notifications to see results immediately
- ✅ Use `--test` flag when testing changes
- ✅ Use `--skip-sync` to speed up testing

### For Debugging
- ✅ Check log files first
- ✅ Run manually with `--no-notify` to reproduce issues
- ✅ Use `--symbols RELIANCE.NS` to test single symbol

## Troubleshooting

### Cron Job Not Running

```bash
# Check crontab
crontab -l

# Check cron service
sudo systemctl status cron

# Check system logs
grep CRON /var/log/syslog | tail -20
```

### No Logs Generated

```bash
# Ensure logs directory exists
mkdir -p ~/ztrader/logs

# Check permissions
ls -la ~/ztrader/logs

# Run manually to test
cd ~/ztrader && source venv/bin/activate && python scripts/daily_workflow.py --no-notify
```

### Workflow Failing

```bash
# Check recent errors
tail -n 100 ~/ztrader/logs/daily_workflow.log | grep -i error

# Test database connection
cd ~/ztrader && source venv/bin/activate && python -c "from src.data.storage import InstrumentsDB; db = InstrumentsDB(); print(len(db.get_all_active()))"

# Test yfinance
cd ~/ztrader && source venv/bin/activate && python test_yfinance_comprehensive.py
```

## Environment Variables

The workflow requires these environment variables in `~/ztrader/.env`:

```bash
# Database (RDS)
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_NAME=trading_db
DB_USER=trading_user
DB_PASSWORD=your_password

# Telegram (optional with --no-notify)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Gemini AI (for sentiment analysis)
GEMINI_API_KEY=your_gemini_key
```

When using `--no-notify`, Telegram credentials are not required.
