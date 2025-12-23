# Data Synchronization Guide

## Overview

The data sync system provides tools to download and maintain OHLCV (candlestick) data for Nifty 100 stocks.

## Components

### 1. DataSync Class (`src/data/sync.py`)
Core synchronization engine with features:
- Parallel downloads using ThreadPoolExecutor
- Incremental updates (only new data)
- Full downloads (complete history)
- Sync status tracking
- Progress reporting

### 2. CLI Tool (`sync_data.py`)
Command-line interface for data synchronization.

### 3. Seed Script (`scripts/database/seed_nifty100.py`)
Populates instruments table with Nifty 100 stocks.

---

## Quick Start

### Step 1: Seed Nifty 100 Stocks
```bash
python scripts/database/seed_nifty100.py
```

This will insert 65+ Nifty 100 stocks into the `instruments` table with sector/industry information.

### Step 2: Download Historical Data

**Full download (first time)**:
```bash
python sync_data.py --full
```

**Incremental update (daily)**:
```bash
python sync_data.py --update
```

**Sync specific timeframe**:
```bash
python sync_data.py --timeframe 1d --full
```

### Step 3: Check Sync Status
```bash
python sync_data.py --status
```

---

## Usage Examples

### Full Download
Downloads complete history for all configured timeframes:
```bash
# All timeframes (1m, 5m, 15m, 1h, 1d)
python sync_data.py --full

# Specific timeframe only
python sync_data.py --timeframe 1d --full

# With custom workers
python sync_data.py --full --workers 10
```

### Incremental Update
Downloads only new data since last sync:
```bash
# Update all timeframes
python sync_data.py --update

# Update specific timeframe
python sync_data.py --timeframe 1h --update
```

### Check Status
View current sync status:
```bash
python sync_data.py --status
```

Output shows:
- Summary by timeframe
- Symbols needing update
- Oldest data points

---

## Python API

### Using DataSync Class

```python
from src.data.sync import DataSync

# Initialize
sync = DataSync(max_workers=5)

# Full download for all symbols
results = sync.sync_all_symbols(full_download=True)

# Incremental update
results = sync.sync_all_symbols(full_download=False)

# Sync specific timeframe
results = sync.sync_timeframe('1d', full_download=True)

# Check sync status
status_df = sync.get_sync_status()
print(status_df)

# Sync single symbol
result = sync.sync_symbol('RELIANCE.NS', '1d', full_download=True)
```

---

## Configuration

### Timeframes
Default timeframes (in `src/config/settings.py`):
- `1m` - 1 minute (last 7 days only due to yfinance limit)
- `5m` - 5 minutes
- `15m` - 15 minutes
- `1h` - 1 hour
- `1d` - Daily

### Download Periods
Automatically determined based on timeframe:
- `1m`: 7 days (yfinance limit)
- `5m`, `15m`, `30m`: 60 days
- `1h`: 2 years
- `1d`, `1w`: Maximum available

### Parallel Workers
Default: 5 workers (configurable via `--workers` flag or `DataConfig.YFINANCE_MAX_WORKERS`)

---

## Sync Schedule Recommendations

### Initial Setup
```bash
# 1. Seed instruments
python scripts/database/seed_nifty100.py

# 2. Download daily data (fastest, most important)
python sync_data.py --timeframe 1d --full

# 3. Download hourly data
python sync_data.py --timeframe 1h --full

# 4. Download intraday data (optional)
python sync_data.py --timeframe 15m --full
```

### Daily Maintenance
```bash
# Run once per day (after market close)
python sync_data.py --update
```

### Intraday Updates
```bash
# Run every hour during market hours
python sync_data.py --timeframe 1m --update
python sync_data.py --timeframe 5m --update
```

---

## Troubleshooting

### Rate Limiting
If you encounter rate limiting from yfinance:
- Reduce `--workers` count
- Add delays between syncs
- Sync one timeframe at a time

### Missing Data
Check sync status:
```bash
python sync_data.py --status
```

Re-download specific symbol:
```python
from src.data.sync import DataSync
sync = DataSync()
sync.sync_symbol('RELIANCE.NS', '1d', full_download=True)
```

### Database Connection
Ensure SSH tunnel is active:
```bash
./scripts/connect-postgres.sh
```

---

## Performance

### Typical Download Times
- **Daily data (1d)**: ~2-3 minutes for 100 symbols
- **Hourly data (1h)**: ~5-10 minutes for 100 symbols
- **Intraday data (5m, 15m)**: ~10-15 minutes for 100 symbols

### Storage Requirements
Approximate storage per symbol per timeframe:
- `1d`: ~5 KB per year
- `1h`: ~50 KB per year
- `15m`: ~200 KB per year
- `5m`: ~600 KB per year
- `1m`: ~3 MB per week

For 100 symbols:
- Daily (10 years): ~5 MB
- Hourly (2 years): ~10 MB
- 15-min (60 days): ~1.2 GB
- 5-min (60 days): ~3.6 GB

---

## Files Reference

- [DataSync Class](file:///Users/faizanuddinmorkas/Work/Personal/ztrader_new/src/data/sync.py)
- [CLI Tool](file:///Users/faizanuddinmorkas/Work/Personal/ztrader_new/sync_data.py)
- [Seed Script](file:///Users/faizanuddinmorkas/Work/Personal/ztrader_new/scripts/database/seed_nifty100.py)
- [Configuration](file:///Users/faizanuddinmorkas/Work/Personal/ztrader_new/src/config/settings.py)
