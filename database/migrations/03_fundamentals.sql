-- Migration 03: Fundamentals table
-- Stores fundamental data from yfinance (PE ratio, market cap, etc.)
-- One row per symbol, updated daily

CREATE TABLE IF NOT EXISTS fundamentals (
    symbol TEXT PRIMARY KEY,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Price Metrics
    current_price NUMERIC,
    previous_close NUMERIC,
    open NUMERIC,
    day_low NUMERIC,
    day_high NUMERIC,
    fifty_two_week_low NUMERIC,
    fifty_two_week_high NUMERIC,
    fifty_day_average NUMERIC,
    two_hundred_day_average NUMERIC,
    
    -- Valuation Ratios
    market_cap BIGINT,
    enterprise_value BIGINT,
    trailing_pe NUMERIC,
    forward_pe NUMERIC,
    price_to_book NUMERIC,
    price_to_sales NUMERIC,
    peg_ratio NUMERIC,
    enterprise_to_revenue NUMERIC,
    enterprise_to_ebitda NUMERIC,
    
    -- Profitability Metrics
    profit_margins NUMERIC,
    gross_margins NUMERIC,
    ebitda_margins NUMERIC,
    operating_margins NUMERIC,
    return_on_equity NUMERIC,
    return_on_assets NUMERIC,
    
    -- Growth Metrics
    revenue_growth NUMERIC,
    earnings_growth NUMERIC,
    earnings_quarterly_growth NUMERIC,
    revenue_quarterly_growth NUMERIC,
    
    -- Financial Health
    total_cash BIGINT,
    total_debt BIGINT,
    total_revenue BIGINT,
    debt_to_equity NUMERIC,
    current_ratio NUMERIC,
    quick_ratio NUMERIC,
    book_value NUMERIC,
    revenue_per_share NUMERIC,
    total_cash_per_share NUMERIC,
    
    -- Dividends
    dividend_rate NUMERIC,
    dividend_yield NUMERIC,
    payout_ratio NUMERIC,
    five_year_avg_dividend_yield NUMERIC,
    
    -- Volume & Liquidity
    volume BIGINT,
    average_volume BIGINT,
    average_volume_10days BIGINT,
    bid NUMERIC,
    ask NUMERIC,
    bid_size INTEGER,
    ask_size INTEGER,
    
    -- Shares
    shares_outstanding BIGINT,
    float_shares BIGINT,
    shares_short BIGINT,
    short_ratio NUMERIC,
    short_percent_of_float NUMERIC,
    held_percent_insiders NUMERIC,
    held_percent_institutions NUMERIC,
    
    -- Analyst Data
    target_high_price NUMERIC,
    target_low_price NUMERIC,
    target_mean_price NUMERIC,
    target_median_price NUMERIC,
    recommendation_mean NUMERIC,
    recommendation_key TEXT,
    number_of_analyst_opinions INTEGER,
    
    -- Company Info
    sector TEXT,
    industry TEXT,
    beta NUMERIC,
    
    -- Store complete raw data as JSON for flexibility
    raw_data JSONB,
    
    FOREIGN KEY (symbol) REFERENCES instruments(symbol) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_fundamentals_updated ON fundamentals(updated_at);
CREATE INDEX IF NOT EXISTS idx_fundamentals_sector ON fundamentals(sector);
CREATE INDEX IF NOT EXISTS idx_fundamentals_industry ON fundamentals(industry);
CREATE INDEX IF NOT EXISTS idx_fundamentals_pe ON fundamentals(trailing_pe) WHERE trailing_pe IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_fundamentals_market_cap ON fundamentals(market_cap) WHERE market_cap IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_fundamentals_beta ON fundamentals(beta) WHERE beta IS NOT NULL;

-- Record migration
INSERT INTO schema_migrations (version, description) VALUES
    (3, 'Fundamentals table for yfinance data')
ON CONFLICT (version) DO NOTHING;
