-- Quick Migration Script
-- Run this in your psql session (via connect-postgres.sh)
-- Usage: \i database/quick_migrate.sql

\echo '========================================='
\echo 'Running Database Migrations'
\echo '========================================='
\echo ''

-- Step 1: Create migration tracking table
\echo '1. Creating migration tracking table...'
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64)
);
\echo '   ✓ Done'
\echo ''

-- Step 2: Create instruments table
\echo '2. Creating instruments table...'
CREATE TABLE IF NOT EXISTS instruments (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100),
    exchange VARCHAR(50) NOT NULL DEFAULT 'NSE',
    asset_type VARCHAR(20) NOT NULL DEFAULT 'stock',
    sector VARCHAR(50),
    industry VARCHAR(100),
    market_cap_category VARCHAR(20),
    currency VARCHAR(10) DEFAULT 'INR',
    lot_size INTEGER DEFAULT 1,
    tick_size NUMERIC(20, 8) DEFAULT 0.05,
    is_active BOOLEAN DEFAULT true,
    is_nifty_50 BOOLEAN DEFAULT false,
    is_nifty_100 BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
CREATE INDEX IF NOT EXISTS idx_instruments_exchange ON instruments(exchange);
CREATE INDEX IF NOT EXISTS idx_instruments_active ON instruments(is_active);
CREATE INDEX IF NOT EXISTS idx_instruments_sector ON instruments(sector);
CREATE INDEX IF NOT EXISTS idx_instruments_nifty_100 ON instruments(is_nifty_100);

-- Record migration
INSERT INTO schema_migrations (version, name) VALUES ('01', 'instruments')
ON CONFLICT (version) DO NOTHING;

\echo '   ✓ Done'
\echo ''

-- Step 3: Create OHLCV data table
\echo '3. Creating ohlcv_data hypertable...'
CREATE TABLE IF NOT EXISTS ohlcv_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(20, 8) NOT NULL,
    trades INTEGER,
    CONSTRAINT ohlcv_unique UNIQUE (time, symbol, timeframe)
);

-- Convert to hypertable
SELECT create_hypertable('ohlcv_data', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_timeframe_time ON ohlcv_data (timeframe, time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe ON ohlcv_data (symbol, timeframe, time DESC);

-- Enable compression
ALTER TABLE ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,timeframe',
    timescaledb.compress_orderby = 'time DESC'
);

-- Add compression policy
SELECT add_compression_policy('ohlcv_data', INTERVAL '7 days', if_not_exists => TRUE);

-- Record migration
INSERT INTO schema_migrations (version, name) VALUES ('02', 'ohlcv_data')
ON CONFLICT (version) DO NOTHING;

\echo '   ✓ Done'
\echo ''

-- Show results
\echo '========================================='
\echo 'Migration Summary'
\echo '========================================='
\echo ''

\echo 'Applied Migrations:'
SELECT version, name, applied_at FROM schema_migrations ORDER BY version;
\echo ''

\echo 'Database Tables:'
\dt
\echo ''

\echo 'TimescaleDB Hypertables:'
SELECT hypertable_schema, hypertable_name, num_dimensions 
FROM timescaledb_information.hypertables;
\echo ''

\echo '========================================='
\echo '✓ Migrations completed successfully!'
\echo '========================================='
