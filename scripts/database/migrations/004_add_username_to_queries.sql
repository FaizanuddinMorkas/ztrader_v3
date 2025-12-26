-- Migration: Add username to user_queries table
-- Description: Store username directly in queries for easier analytics

-- Add username column
ALTER TABLE user_queries 
ADD COLUMN IF NOT EXISTS username VARCHAR(255);

-- Add index for username searches
CREATE INDEX IF NOT EXISTS idx_user_queries_username ON user_queries(username);

-- Backfill existing data
UPDATE user_queries uq
SET username = tu.username
FROM telegram_users tu
WHERE uq.user_id = tu.user_id
AND uq.username IS NULL;

-- Add comment
COMMENT ON COLUMN user_queries.username IS 'Telegram username for easier analytics (denormalized from telegram_users)';

-- Verify
DO $$
BEGIN
    RAISE NOTICE 'Migration 004 completed successfully!';
    RAISE NOTICE 'Added username column to user_queries table';
END $$;
