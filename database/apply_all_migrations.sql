-- Run all migrations in order
-- Execute this file in your psql session

\echo '========================================='
\echo 'Running Database Migrations'
\echo '========================================='
\echo ''

-- Migration 00: Create tracking table
\echo 'Applying migration: 00_schema_migrations.sql'
\i database/migrations/00_schema_migrations.sql
\echo 'Done'
\echo ''

-- Migration 01: Create instruments table
\echo 'Applying migration: 01_instruments.sql'
\i database/migrations/01_instruments.sql
\echo 'Done'
\echo ''

-- Migration 02: Create ohlcv_data table
\echo 'Applying migration: 02_ohlcv_data.sql'
\i database/migrations/02_ohlcv_data.sql
\echo 'Done'
\echo ''

\echo '========================================='
\echo 'Migration Summary'
\echo '========================================='
\echo ''

-- Show migration history
\echo 'Migration History:'
SELECT version, name, applied_at FROM schema_migrations ORDER BY version;
\echo ''

-- Show created tables
\echo 'Database Tables:'
\dt
\echo ''

-- Show hypertables
\echo 'TimescaleDB Hypertables:'
SELECT hypertable_schema, hypertable_name, num_dimensions 
FROM timescaledb_information.hypertables;
\echo ''

\echo '========================================='
\echo 'Migrations completed successfully!'
\echo '========================================='
