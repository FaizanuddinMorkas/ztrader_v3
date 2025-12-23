# Database Schema Documentation

## Overview

This directory contains the database schema and migrations for the algorithmic trading platform. The database uses **PostgreSQL with TimescaleDB** for efficient time-series data storage.

## Current Schema

### Tables Created

#### 1. `instruments`
**Purpose**: Store Nifty 100 trading symbols with metadata

**Columns**:
- `id`: Primary key
- `symbol`: Unique symbol in yfinance format (e.g., `RELIANCE.NS`, `TCS.NS`)
- `name`: Company name
- `exchange`: Stock exchange (default: `NSE`)
- `asset_type`: Type of asset (default: `stock`)
- `sector`: Business sector (e.g., `Energy`, `IT`, `Banking`)
- `industry`: Specific industry (e.g., `Oil & Gas`, `Software Services`)
- `market_cap_category`: Market capitalization category
- `currency`: Trading currency (default: `INR`)
- `lot_size`: Minimum trading lot size
- `tick_size`: Minimum price movement (default: `0.05` INR)
- `is_active`: Whether the instrument is actively traded
- `is_nifty_50`: Flag for Nifty 50 membership
- `is_nifty_100`: Flag for Nifty 100 membership
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

**Indexes**:
- `idx_instruments_symbol`: Fast lookup by symbol
- `idx_instruments_exchange`: Filter by exchange
- `idx_instruments_active`: Filter active instruments
- `idx_instruments_sector`: Filter by sector
- `idx_instruments_nifty_100`: Filter Nifty 100 stocks

---

#### 2. `ohlcv_data` (TimescaleDB Hypertable)
**Purpose**: Store multi-timeframe OHLCV (candlestick) historical data

**Columns**:
- `time`: Candle timestamp (opening time)
- `symbol`: Instrument symbol (e.g., `RELIANCE.NS`)
- `timeframe`: Candle timeframe (`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`)
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume
- `trades`: Number of trades (optional)

**Constraints**:
- Unique constraint on `(time, symbol, timeframe)` to prevent duplicates

**Indexes**:
- `idx_ohlcv_symbol_time`: Query by symbol and time
- `idx_ohlcv_timeframe_time`: Query by timeframe
- `idx_ohlcv_symbol_timeframe`: Query by symbol and timeframe (most common)

**TimescaleDB Features**:
- **Hypertable**: Automatic partitioning by time for efficient queries
- **Compression**: Data older than 7 days is automatically compressed
- **Compression segments**: Grouped by `symbol` and `timeframe`
- **Retention policy**: Optional (currently disabled, can delete data older than 2 years)

---

## Running Migrations

### Prerequisites
1. PostgreSQL installed and running
2. TimescaleDB extension installed
3. Database `trading_db` created
4. User `trading_user` with appropriate permissions

### Apply Migrations

```bash
# Set environment variables (optional, defaults shown)
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=trading_db
export DB_USER=trading_user

# Run all migrations
cd database
./run_migrations.sh
```

### Manual Migration

You can also apply migrations manually:

```bash
# Connect to database via SSH tunnel (if on EC2)
./connect-postgres.sh

# Then in psql:
\i database/migrations/01_instruments.sql
\i database/migrations/02_ohlcv_data.sql
```

---

## Verifying the Schema

### Check Tables
```sql
-- List all tables
\dt

-- Describe instruments table
\d instruments

-- Describe ohlcv_data table
\d ohlcv_data
```

### Check TimescaleDB Hypertables
```sql
-- List all hypertables
SELECT * FROM timescaledb_information.hypertables;

-- Check compression settings
SELECT * FROM timescaledb_information.compression_settings;
```

### Check Indexes
```sql
-- List indexes on ohlcv_data
\di ohlcv_data*

-- Or query directly
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'ohlcv_data';
```

---

## Common Queries

### Query Instruments
```sql
-- Get all active Nifty 100 stocks
SELECT symbol, name, sector 
FROM instruments 
WHERE is_active = true AND is_nifty_100 = true
ORDER BY symbol;

-- Get stocks by sector
SELECT symbol, name 
FROM instruments 
WHERE sector = 'Information Technology' AND is_active = true;
```

### Query OHLCV Data
```sql
-- Get latest 100 daily candles for RELIANCE
SELECT time, open, high, low, close, volume
FROM ohlcv_data
WHERE symbol = 'RELIANCE.NS' AND timeframe = '1d'
ORDER BY time DESC
LIMIT 100;

-- Get hourly data for last 7 days
SELECT time, close, volume
FROM ohlcv_data
WHERE symbol = 'TCS.NS' 
  AND timeframe = '1h'
  AND time > NOW() - INTERVAL '7 days'
ORDER BY time DESC;

-- Compare multiple timeframes at a specific time
SELECT timeframe, close
FROM ohlcv_data
WHERE symbol = 'INFY.NS' 
  AND time = '2024-01-15 09:30:00'
ORDER BY timeframe;
```

---

## Storage Optimization

### Compression
TimescaleDB automatically compresses data older than 7 days. This can save 90%+ storage space.

**Check compression stats**:
```sql
SELECT * FROM timescaledb_information.compressed_chunk_stats;
```

**Manual compression** (if needed):
```sql
SELECT compress_chunk(i) 
FROM show_chunks('ohlcv_data', older_than => INTERVAL '7 days') i;
```

### Retention Policy
Currently disabled. To enable automatic deletion of old data:

```sql
-- Delete data older than 2 years
SELECT add_retention_policy('ohlcv_data', INTERVAL '2 years');
```

---

## Next Steps

1. **Seed Nifty 100 data**: Populate `instruments` table with all Nifty 100 stocks
2. **Download historical data**: Use yfinance to fetch and populate `ohlcv_data`
3. **Create additional tables**: Signals, trades, positions, portfolio (as needed)

---

## Troubleshooting

### TimescaleDB extension not found
```sql
-- Install TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### Permission denied
```sql
-- Grant permissions to trading_user
GRANT ALL ON SCHEMA public TO trading_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO trading_user;
```

### Hypertable creation failed
Make sure TimescaleDB extension is installed before creating the `ohlcv_data` table.

---

## Schema Version
- **Version**: 1.0
- **Last Updated**: 2024-12-16
- **Tables**: 2 (instruments, ohlcv_data)
- **Hypertables**: 1 (ohlcv_data)
