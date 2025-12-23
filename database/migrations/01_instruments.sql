-- Migration 01: Create instruments table for Nifty 100 stocks
-- Purpose: Store trading symbols with metadata for NSE stocks

CREATE TABLE IF NOT EXISTS instruments (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'RELIANCE.NS', 'TCS.NS'
    name VARCHAR(100), -- Company name
    exchange VARCHAR(50) NOT NULL DEFAULT 'NSE',
    asset_type VARCHAR(20) NOT NULL DEFAULT 'stock',
    sector VARCHAR(50), -- e.g., 'Energy', 'IT', 'Banking'
    industry VARCHAR(100), -- e.g., 'Oil & Gas', 'Software Services'
    market_cap_category VARCHAR(20), -- 'Large Cap', 'Mid Cap', 'Small Cap'
    currency VARCHAR(10) DEFAULT 'INR',
    lot_size INTEGER DEFAULT 1,
    tick_size NUMERIC(20, 8) DEFAULT 0.05, -- NSE tick size is typically 0.05 INR
    is_active BOOLEAN DEFAULT true,
    is_nifty_50 BOOLEAN DEFAULT false,
    is_nifty_100 BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
CREATE INDEX IF NOT EXISTS idx_instruments_exchange ON instruments(exchange);
CREATE INDEX IF NOT EXISTS idx_instruments_active ON instruments(is_active);
CREATE INDEX IF NOT EXISTS idx_instruments_sector ON instruments(sector);
CREATE INDEX IF NOT EXISTS idx_instruments_nifty_100 ON instruments(is_nifty_100);

-- Add comment to table
COMMENT ON TABLE instruments IS 'Trading instruments/symbols with metadata for NSE Nifty 100 stocks';
COMMENT ON COLUMN instruments.symbol IS 'yfinance-compatible symbol format (e.g., RELIANCE.NS)';
COMMENT ON COLUMN instruments.is_nifty_50 IS 'Flag indicating if stock is part of Nifty 50 index';
COMMENT ON COLUMN instruments.is_nifty_100 IS 'Flag indicating if stock is part of Nifty 100 index';
