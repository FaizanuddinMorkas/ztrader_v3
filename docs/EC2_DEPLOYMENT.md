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

## Setup Automated Daily Updates

```bash
# Edit crontab
crontab -e

# Add this line (runs at 4 PM IST daily)
0 16 * * * cd ~/ztrader && source venv/bin/activate && python sync_data.py --update >> logs/sync.log 2>&1
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
