-- Migration 00: Create schema_migrations tracking table
-- Purpose: Track which migrations have been applied to prevent duplicates

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64) -- MD5 hash of migration file for integrity check
);

-- Add comment
COMMENT ON TABLE schema_migrations IS 'Tracks applied database migrations to prevent duplicates';
COMMENT ON COLUMN schema_migrations.version IS 'Migration version number (e.g., 01, 02, 03)';
COMMENT ON COLUMN schema_migrations.name IS 'Descriptive name of the migration';
COMMENT ON COLUMN schema_migrations.checksum IS 'MD5 checksum of migration file for integrity verification';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at DESC);
