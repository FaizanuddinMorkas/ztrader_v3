-- Migration 02: Create OHLCV data table for multi-timeframe historical data
-- Purpose: Store candlestick data for all timeframes using TimescaleDB hypertable

CREATE TABLE IF NOT EXISTS ohlcv_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(20, 8) NOT NULL,
    trades INTEGER, -- Number of trades in this candle (if available from data source)
    CONSTRAINT ohlcv_unique UNIQUE (time, symbol, timeframe)
);

-- Convert to TimescaleDB hypertable
-- This enables time-series optimizations, compression, and efficient queries
SELECT create_hypertable('ohlcv_data', 'time', if_not_exists => TRUE);

-- Create indexes for common query patterns
-- Index 1: Query by symbol and time (most common)
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv_data (symbol, time DESC);

-- Index 2: Query by timeframe and time
CREATE INDEX IF NOT EXISTS idx_ohlcv_timeframe_time ON ohlcv_data (timeframe, time DESC);

-- Index 3: Query by symbol, timeframe, and time (very common for strategy backtesting)
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe ON ohlcv_data (symbol, timeframe, time DESC);

-- Enable compression for older data to save storage
-- Compress data older than 7 days
ALTER TABLE ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,timeframe',
    timescaledb.compress_orderby = 'time DESC'
);

-- Add compression policy: automatically compress data older than 7 days
SELECT add_compression_policy('ohlcv_data', INTERVAL '7 days', if_not_exists => TRUE);

-- Optional: Add retention policy to automatically delete very old data
-- Uncomment the line below to delete data older than 2 years
-- SELECT add_retention_policy('ohlcv_data', INTERVAL '2 years', if_not_exists => TRUE);

-- Add comments for documentation
COMMENT ON TABLE ohlcv_data IS 'Multi-timeframe OHLCV (candlestick) data for all instruments';
COMMENT ON COLUMN ohlcv_data.time IS 'Candle timestamp (opening time of the candle)';
COMMENT ON COLUMN ohlcv_data.timeframe IS 'Candle timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w';
COMMENT ON COLUMN ohlcv_data.trades IS 'Number of trades in this candle (optional, source-dependent)';
