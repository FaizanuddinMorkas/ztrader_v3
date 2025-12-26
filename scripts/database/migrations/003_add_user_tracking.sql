-- Migration: Add User Tracking and Analytics
-- Description: Tables for Telegram user management, usage tracking, and analytics

-- ============================================================================
-- 1. Telegram Users Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS telegram_users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT false,  -- Requires admin approval
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE telegram_users IS 'Telegram bot users with approval workflow';
COMMENT ON COLUMN telegram_users.is_active IS 'User must be approved by admin to access bot features';

-- ============================================================================
-- 2. User Queries Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_queries (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES telegram_users(user_id) ON DELETE CASCADE,
    query_type VARCHAR(50) NOT NULL,  -- 'screen', 'analyze', 'chat'
    query_text TEXT,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE user_queries IS 'Log of all user queries for analytics and debugging';
COMMENT ON COLUMN user_queries.query_type IS 'Type of query: screen, analyze, or chat';
COMMENT ON COLUMN user_queries.response_time_ms IS 'Response time in milliseconds';

-- ============================================================================
-- 3. Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_telegram_users_active ON telegram_users(is_active);
CREATE INDEX IF NOT EXISTS idx_telegram_users_last_seen ON telegram_users(last_seen);

CREATE INDEX IF NOT EXISTS idx_user_queries_user_id ON user_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_user_queries_created_at ON user_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_user_queries_type ON user_queries(query_type);
CREATE INDEX IF NOT EXISTS idx_user_queries_success ON user_queries(success);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_user_queries_user_created ON user_queries(user_id, created_at DESC);

-- ============================================================================
-- 4. Materialized View for User Statistics
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS user_stats AS
SELECT 
    user_id,
    COUNT(*) as total_queries,
    COUNT(*) FILTER (WHERE query_type = 'screen') as screen_queries,
    COUNT(*) FILTER (WHERE query_type = 'analyze') as analyze_queries,
    COUNT(*) FILTER (WHERE query_type = 'chat') as chat_queries,
    AVG(response_time_ms) as avg_response_time,
    COUNT(*) FILTER (WHERE success = false) as failed_queries,
    MAX(created_at) as last_query_time,
    MIN(created_at) as first_query_time
FROM user_queries
GROUP BY user_id;

-- Add index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_stats_user_id ON user_stats(user_id);

-- Add comment
COMMENT ON MATERIALIZED VIEW user_stats IS 'Aggregated user statistics for quick access';

-- ============================================================================
-- 5. Function to Refresh User Stats
-- ============================================================================
CREATE OR REPLACE FUNCTION refresh_user_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_stats;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_user_stats() IS 'Refresh user statistics materialized view';

-- ============================================================================
-- 6. Trigger to Update last_seen
-- ============================================================================
CREATE OR REPLACE FUNCTION update_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE telegram_users 
    SET last_seen = NOW() 
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_last_seen
    AFTER INSERT ON user_queries
    FOR EACH ROW
    EXECUTE FUNCTION update_last_seen();

COMMENT ON FUNCTION update_last_seen() IS 'Automatically update user last_seen timestamp on query';

-- ============================================================================
-- 7. Helper Views
-- ============================================================================

-- View: Active users
CREATE OR REPLACE VIEW active_users AS
SELECT 
    user_id,
    username,
    first_name,
    last_name,
    first_seen,
    last_seen
FROM telegram_users
WHERE is_active = true
ORDER BY last_seen DESC;

COMMENT ON VIEW active_users IS 'List of approved active users';

-- View: Pending users (awaiting approval)
CREATE OR REPLACE VIEW pending_users AS
SELECT 
    user_id,
    username,
    first_name,
    last_name,
    first_seen
FROM telegram_users
WHERE is_active = false
ORDER BY first_seen DESC;

COMMENT ON VIEW pending_users IS 'List of users awaiting admin approval';

-- View: Recent activity
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    uq.id,
    uq.user_id,
    tu.username,
    tu.first_name,
    uq.query_type,
    uq.query_text,
    uq.response_time_ms,
    uq.success,
    uq.created_at
FROM user_queries uq
JOIN telegram_users tu ON uq.user_id = tu.user_id
WHERE uq.created_at > NOW() - INTERVAL '7 days'
ORDER BY uq.created_at DESC
LIMIT 100;

COMMENT ON VIEW recent_activity IS 'Recent user activity (last 7 days)';

-- ============================================================================
-- 8. Analytics Functions
-- ============================================================================

-- Function: Get Daily Active Users
CREATE OR REPLACE FUNCTION get_daily_active_users(days INTEGER DEFAULT 1)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(DISTINCT user_id)
        FROM user_queries
        WHERE created_at > NOW() - (days || ' days')::INTERVAL
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_daily_active_users(INTEGER) IS 'Get count of active users in last N days';

-- Function: Get user query count in last hour
CREATE OR REPLACE FUNCTION get_user_hourly_queries(p_user_id BIGINT)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM user_queries
        WHERE user_id = p_user_id
        AND created_at > NOW() - INTERVAL '1 hour'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_hourly_queries(BIGINT) IS 'Get user query count in last hour (for rate limiting)';

-- ============================================================================
-- 9. Sample Data (Optional - for testing)
-- ============================================================================

-- Uncomment to insert test admin user
-- INSERT INTO telegram_users (user_id, username, first_name, is_active)
-- VALUES (123456789, 'admin', 'Admin User', true)
-- ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Verify tables created
DO $$
BEGIN
    RAISE NOTICE 'Migration 003 completed successfully!';
    RAISE NOTICE 'Tables created: telegram_users, user_queries';
    RAISE NOTICE 'Materialized view created: user_stats';
    RAISE NOTICE 'Views created: active_users, pending_users, recent_activity';
    RAISE NOTICE 'Functions created: refresh_user_stats, get_daily_active_users, get_user_hourly_queries';
END $$;
