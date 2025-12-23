#!/bin/bash

# Enhanced Database Schema Migration Runner with Tracking
# Purpose: Apply database migrations with version tracking to prevent duplicates

set -e  # Exit on error

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-trading_db}"
DB_USER="${DB_USER:-trading_user}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to execute SQL and capture output
execute_sql() {
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$1" 2>&1
}

# Function to execute SQL file
execute_sql_file() {
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$1" 2>&1
}

# Function to check if migration has been applied
is_migration_applied() {
    local version=$1
    local result=$(execute_sql "SELECT COUNT(*) FROM schema_migrations WHERE version = '$version';" 2>/dev/null || echo "0")
    result=$(echo "$result" | tr -d '[:space:]')
    [ "$result" = "1" ]
}

# Function to record migration
record_migration() {
    local version=$1
    local name=$2
    local checksum=$3
    execute_sql "INSERT INTO schema_migrations (version, name, checksum) VALUES ('$version', '$name', '$checksum');" > /dev/null
}

# Function to calculate MD5 checksum
get_checksum() {
    if command -v md5sum &> /dev/null; then
        md5sum "$1" | awk '{print $1}'
    elif command -v md5 &> /dev/null; then
        md5 -q "$1"
    else
        echo "unknown"
    fi
}

echo "========================================="
echo "Database Migration Runner (Enhanced)"
echo "========================================="
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "========================================="
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found${NC}"
    echo "Please install PostgreSQL client tools"
    echo ""
    echo "On macOS: brew install postgresql"
    echo "On Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# Test database connection
echo -e "${YELLOW}Testing database connection...${NC}"
if execute_sql "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Failed to connect to database${NC}"
    echo "Please check your connection parameters and ensure:"
    echo "  1. SSH tunnel is active (if connecting to remote DB)"
    echo "  2. Database credentials are correct"
    echo "  3. PGPASSWORD environment variable is set (if needed)"
    exit 1
fi

echo ""

# Check if TimescaleDB extension is installed
echo -e "${YELLOW}Checking TimescaleDB extension...${NC}"
if execute_sql "SELECT 1 FROM pg_extension WHERE extname = 'timescaledb';" | grep -q "1"; then
    echo -e "${GREEN}✓ TimescaleDB extension is installed${NC}"
else
    echo -e "${RED}✗ TimescaleDB extension not found${NC}"
    echo "Installing TimescaleDB extension..."
    if execute_sql "CREATE EXTENSION IF NOT EXISTS timescaledb;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ TimescaleDB extension installed${NC}"
    else
        echo -e "${RED}✗ Failed to install TimescaleDB extension${NC}"
        echo "Please install it manually: CREATE EXTENSION timescaledb;"
        exit 1
    fi
fi

echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MIGRATIONS_DIR="$SCRIPT_DIR/migrations"

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo -e "${RED}Error: Migrations directory not found: $MIGRATIONS_DIR${NC}"
    exit 1
fi

# Ensure schema_migrations table exists
echo -e "${YELLOW}Initializing migration tracking...${NC}"
if [ -f "$MIGRATIONS_DIR/00_schema_migrations.sql" ]; then
    execute_sql_file "$MIGRATIONS_DIR/00_schema_migrations.sql" > /dev/null 2>&1
    echo -e "${GREEN}✓ Migration tracking initialized${NC}"
else
    echo -e "${YELLOW}⚠ Migration tracking file not found, creating table manually...${NC}"
    execute_sql "CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(50) PRIMARY KEY,
        name VARCHAR(200),
        applied_at TIMESTAMPTZ DEFAULT NOW(),
        checksum VARCHAR(64)
    );" > /dev/null 2>&1
    echo -e "${GREEN}✓ Migration tracking table created${NC}"
fi

echo ""

# Count migrations
total_migrations=0
applied_migrations=0
skipped_migrations=0
new_migrations=0

# Run migrations in order
echo -e "${YELLOW}Scanning migrations...${NC}"
echo ""

for migration_file in "$MIGRATIONS_DIR"/*.sql; do
    if [ -f "$migration_file" ]; then
        filename=$(basename "$migration_file")
        
        # Skip the tracking table migration (already applied)
        if [ "$filename" = "00_schema_migrations.sql" ]; then
            continue
        fi
        
        # Extract version from filename (e.g., 01 from 01_instruments.sql)
        version=$(echo "$filename" | grep -o '^[0-9]\+')
        name=$(echo "$filename" | sed 's/^[0-9]*_//' | sed 's/\.sql$//')
        
        total_migrations=$((total_migrations + 1))
        
        # Check if migration has been applied
        if is_migration_applied "$version"; then
            echo -e "${BLUE}⊙ Skipping (already applied): $filename${NC}"
            skipped_migrations=$((skipped_migrations + 1))
            applied_migrations=$((applied_migrations + 1))
        else
            echo -e "${YELLOW}▶ Applying migration: $filename${NC}"
            
            # Calculate checksum
            checksum=$(get_checksum "$migration_file")
            
            # Apply migration
            if execute_sql_file "$migration_file" > /dev/null 2>&1; then
                # Record migration
                record_migration "$version" "$name" "$checksum"
                echo -e "${GREEN}✓ Successfully applied: $filename${NC}"
                new_migrations=$((new_migrations + 1))
                applied_migrations=$((applied_migrations + 1))
            else
                echo -e "${RED}✗ Failed to apply: $filename${NC}"
                echo "Error output:"
                execute_sql_file "$migration_file"
                exit 1
            fi
        fi
        echo ""
    fi
done

echo "========================================="
echo -e "${GREEN}Migration Summary${NC}"
echo "========================================="
echo "Total migrations found: $total_migrations"
echo "Already applied: $skipped_migrations"
echo "Newly applied: $new_migrations"
echo "Total applied: $applied_migrations"
echo "========================================="
echo ""

# Show migration history
if [ $applied_migrations -gt 0 ]; then
    echo -e "${YELLOW}Migration History:${NC}"
    execute_sql "SELECT version, name, applied_at FROM schema_migrations ORDER BY version;"
    echo ""
fi

# Show created tables
echo -e "${YELLOW}Database Tables:${NC}"
execute_sql "\dt"
echo ""

# Show hypertables
echo -e "${YELLOW}TimescaleDB Hypertables:${NC}"
execute_sql "SELECT hypertable_schema, hypertable_name, num_dimensions FROM timescaledb_information.hypertables;" || echo "No hypertables found"
echo ""

if [ $new_migrations -gt 0 ]; then
    echo -e "${GREEN}✓ $new_migrations new migration(s) applied successfully!${NC}"
else
    echo -e "${GREEN}✓ Database schema is up to date!${NC}"
fi
