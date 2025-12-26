# EC2 Deployment Quick Start

## Deploy in One Command

```bash
./scripts/deploy_to_ec2.sh <YOUR_EC2_IP>
```

Example:
```bash
./scripts/deploy_to_ec2.sh 54.123.45.67
```

## What the Script Does

1. ✅ Creates `~/ztrader` directory on EC2
2. ✅ Transfers all code (excludes venv, logs, cache)
3. ✅ Installs Python 3 and dependencies
4. ✅ Creates virtual environment
5. ✅ Installs all requirements
6. ✅ Creates `.env` file with localhost DB settings

## After Deployment

### 1. SSH into EC2
```bash
ssh ubuntu@<YOUR_EC2_IP>
```

### 2. Update Database Password
```bash
nano ~/ztrader/.env
# Update DB_PASSWORD with your actual password
```

### 3. Activate Virtual Environment
```bash
cd ~/ztrader
source venv/bin/activate
```

### 4. Seed Database (if not done)
```bash
python scripts/database/seed_nifty100.py
```

### 5. Run Data Sync
```bash
# Full download for daily data
python sync_data.py --timeframe 1d --full --workers 10

# This should complete in 5-10 minutes!
```

### 6. Check Progress
The sync will show real-time progress:
```
[1/66] RELIANCE.NS  1d - ✓  5797 rows | Progress: 1.5% | ETA: 8m 30s
[2/66] TCS.NS       1d - ✓  5797 rows | Progress: 3.0% | ETA: 8m 15s
...
```

## ⏰ Automated Job Management

### 1. Setup Automation
Run the setup script to install the full schedule (Reports + Workflow):
```bash
# On EC2
cd ~/ztrader
./scripts/deployment/ec2_cron_setup.sh
```

### 2. List Active Jobs
See what is currently scheduled to run:
```bash
crontab -l
```

### 3. Check Running Processes
See if any job is currently executing:
```bash
# Filter for python or monitoring wrapper
ps aux | grep -E "python|monitor_job"
```

### 4. Stop/Pause a Job
To disable a specific job:
1. Edit the schedule:
   ```bash
   crontab -e
   ```
2. Add a `#` at the start of the line to pause it.
   ```bash
   # 0 4 * * 1-5 bash ... (Paused)
   ```
3. Save and exit (`:wq` in vi/vim).

### 5. Kill a Stuck Job
If a job hangs, find its PID and kill it:
```bash
# 1. Find PID
ps aux | grep daily_workflow.py

# 2. Kill it
kill -9 <PID>
```

### 6. Logs & Errors
All jobs are monitored. Logs are in `~/ztrader/logs/`.
- **Success**: Output written to `report_*.log` or `daily_workflow.log`.
- **Failure**: Error alert sent to Telegram immediately.

To tail a log file in real-time:
```bash
tail -f ~/ztrader/logs/daily_workflow.log
```

## Troubleshooting

### If deployment fails
```bash
# Check SSH connection
ssh ubuntu@<YOUR_EC2_IP>

# Check if Python is installed
python3 --version

# Manually create directory
mkdir -p ~/ztrader
```

### If sync fails
```bash
# Check database connection
psql -h localhost -U trading_user -d trading_db

# Check .env file
cat ~/ztrader/.env

# Test with single symbol
python test_single.py
```

## Performance Comparison

| Location | Time for 66 symbols |
|----------|---------------------|
| Local (SSH tunnel) | ~60 minutes |
| EC2 (localhost) | ~5-10 minutes |

**10x faster on EC2!** 🚀

## Files Deployed

- `src/` - All application code
- `sync_data.py` - CLI sync tool
- `scripts/database/seed_nifty100.py` - Seed script
- `requirements.txt` - Dependencies
- `.env` - Environment config (created automatically)

## Next Steps

1. Run full sync for all timeframes
2. Set up cron jobs
3. Monitor logs
4. Enjoy fast data sync!
