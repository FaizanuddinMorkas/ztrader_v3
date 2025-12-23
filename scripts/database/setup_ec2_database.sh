#!/bin/bash
# setup_timescale_and_tables.sh
# Run this script on your EC2 instance to complete database setup

set -e

echo "🚀 Setting up TimescaleDB and creating tables..."
echo ""

# Enable TimescaleDB extension
echo "1️⃣  Enabling TimescaleDB extension..."
sudo -u postgres psql -d trading_db << 'EOF'
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
\dx timescaledb
EOF

echo ""
echo "2️⃣  Creating tables..."

# Create tables as trading_user
psql -U trading_user -d trading_db << 'EOF'
-- Create OHLCV table
CREATE TABLE IF NOT EXISTS ohlcv (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open NUMERIC(12, 4),
    high NUMERIC(12, 4),
    low NUMERIC(12, 4),
    close NUMERIC(12, 4),
    volume BIGINT,
    interval VARCHAR(5) NOT NULL,
    CONSTRAINT ohlcv_pkey PRIMARY KEY (time, symbol, interval)
);

-- Convert to hypertable (TimescaleDB feature)
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_interval ON ohlcv (interval);

-- Create signals table
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,
    strategy_name VARCHAR(50) NOT NULL,
    price NUMERIC(12, 4),
    confidence NUMERIC(3, 2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_time ON signals (time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals (symbol);

-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity NUMERIC(12, 4) NOT NULL,
    price NUMERIC(12, 4) NOT NULL,
    commission NUMERIC(12, 4) DEFAULT 0,
    pnl NUMERIC(12, 4),
    strategy_name VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_time ON trades (time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol);

-- Create positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    quantity NUMERIC(12, 4) NOT NULL,
    avg_price NUMERIC(12, 4) NOT NULL,
    current_price NUMERIC(12, 4),
    unrealized_pnl NUMERIC(12, 4),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Show created tables
\dt

-- Show TimescaleDB hypertables
SELECT * FROM timescaledb_information.hypertables;

EOF

echo ""
echo "============================================================"
echo "✅ Setup complete!"
echo "============================================================"
echo ""
echo "Tables created:"
echo "  - ohlcv (TimescaleDB hypertable)"
echo "  - signals"
echo "  - trades"
echo "  - positions"
echo ""
echo "Next: Test from your Mac with ./test-connection.sh"
echo ""
