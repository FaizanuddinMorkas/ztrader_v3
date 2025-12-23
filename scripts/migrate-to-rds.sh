#!/bin/bash
# Migrate PostgreSQL database from EC2 to RDS
# This script dumps the EC2 database and restores it to RDS

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
EC2_HOST="localhost"
EC2_PORT=5432
EC2_USER="trading_user"
EC2_DB="trading_db"
EC2_PASSWORD="${EC2_PASSWORD:-}"  # Set via environment variable or will prompt

RDS_HOST="localhost"
RDS_PORT=5433
RDS_USER="faizy"
RDS_DB="trading_db"
RDS_PASSWORD="${RDS_PASSWORD:-}"  # Set via environment variable or will prompt

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="$BACKUP_DIR/ec2_trading_db_${TIMESTAMP}.dump"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     EC2 to RDS PostgreSQL Migration                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Prompt for passwords if not set
if [ -z "$EC2_PASSWORD" ]; then
    echo -n "Enter EC2 PostgreSQL password for user '$EC2_USER': "
    read -s EC2_PASSWORD
    echo ""
fi

if [ -z "$RDS_PASSWORD" ]; then
    echo -n "Enter RDS PostgreSQL password for user '$RDS_USER': "
    read -s RDS_PASSWORD
    echo ""
fi

echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Step 1: Verify connections
echo -e "${BLUE}[1/7] Verifying database connections...${NC}"
echo ""

# Check EC2 connection
echo "Testing EC2 PostgreSQL connection..."
if PGPASSWORD="$EC2_PASSWORD" psql -h "$EC2_HOST" -p "$EC2_PORT" -U "$EC2_USER" -d "$EC2_DB" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ EC2 PostgreSQL connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to EC2 PostgreSQL${NC}"
    echo ""
    echo "Make sure:"
    echo "  1. The EC2 tunnel is running: ./scripts/connect-postgres.sh"
    echo "  2. Password is correct"
    echo ""
    exit 1
fi

# Check RDS connection
echo "Testing RDS PostgreSQL connection..."
if PGPASSWORD="$RDS_PASSWORD" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "postgres" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ RDS PostgreSQL connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to RDS PostgreSQL${NC}"
    echo ""
    echo "Make sure:"
    echo "  1. The RDS tunnel is running: ./scripts/connect-rds.sh"
    echo "  2. Password is correct"
    echo ""
    exit 1
fi

echo ""

# Step 2: Get row counts from EC2
echo -e "${BLUE}[2/7] Checking EC2 database...${NC}"
echo ""

INSTRUMENTS_COUNT=$(PGPASSWORD="$EC2_PASSWORD" psql -h "$EC2_HOST" -p "$EC2_PORT" -U "$EC2_USER" -d "$EC2_DB" -t -c "SELECT COUNT(*) FROM instruments;" 2>/dev/null | xargs || echo "0")
OHLCV_COUNT=$(PGPASSWORD="$EC2_PASSWORD" psql -h "$EC2_HOST" -p "$EC2_PORT" -U "$EC2_USER" -d "$EC2_DB" -t -c "SELECT COUNT(*) FROM ohlcv_data;" 2>/dev/null | xargs || echo "0")

echo "  Instruments: $INSTRUMENTS_COUNT rows"
echo "  OHLCV Data:  $OHLCV_COUNT rows"
echo ""

if [ "$INSTRUMENTS_COUNT" = "0" ] && [ "$OHLCV_COUNT" = "0" ]; then
    echo -e "${YELLOW}⚠️  Warning: EC2 database appears to be empty${NC}"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled."
        exit 1
    fi
fi

# Step 3: Create database on RDS
echo -e "${BLUE}[3/7] Creating database on RDS...${NC}"
echo ""

# Check if database already exists
DB_EXISTS=$(PGPASSWORD="$RDS_PASSWORD" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "postgres" -t -c "SELECT 1 FROM pg_database WHERE datname='$RDS_DB';" | xargs || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}⚠️  Database '$RDS_DB' already exists on RDS${NC}"
    echo ""
    read -p "Drop and recreate? This will DELETE all existing data! (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dropping existing database..."
        PGPASSWORD="$RDS_PASSWORD" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "postgres" -c "DROP DATABASE $RDS_DB;"
        echo -e "${GREEN}✅ Database dropped${NC}"
    else
        echo "Migration cancelled."
        exit 1
    fi
fi

echo "Creating database '$RDS_DB'..."
PGPASSWORD="$RDS_PASSWORD" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "postgres" -c "CREATE DATABASE $RDS_DB;"
echo -e "${GREEN}✅ Database created${NC}"
echo ""

# Step 4: Install TimescaleDB extension
echo -e "${BLUE}[4/7] Installing TimescaleDB extension on RDS...${NC}"
echo ""

if PGPASSWORD="$RDS_PASSWORD" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -c "CREATE EXTENSION IF NOT EXISTS timescaledb;" 2>&1 | grep -q "ERROR"; then
    echo -e "${RED}❌ Failed to install TimescaleDB extension${NC}"
    echo ""
    echo "Your RDS instance may not support TimescaleDB."
    echo "You need to:"
    echo "  1. Use a compatible RDS PostgreSQL version"
    echo "  2. Or use a TimescaleDB-compatible service (e.g., Timescale Cloud)"
    echo ""
    read -p "Continue without TimescaleDB? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled."
        exit 1
    fi
else
    echo -e "${GREEN}✅ TimescaleDB extension installed${NC}"
fi
echo ""

# Step 5: Dump EC2 database
echo -e "${BLUE}[5/7] Dumping EC2 database...${NC}"
echo ""
echo "Dump file: $DUMP_FILE"
echo "This may take a while depending on data size..."
echo ""

PGPASSWORD="$EC2_PASSWORD" pg_dump \
    -h "$EC2_HOST" \
    -p "$EC2_PORT" \
    -U "$EC2_USER" \
    -d "$EC2_DB" \
    -F c \
    -f "$DUMP_FILE"

echo ""
echo -e "${GREEN}✅ Database dumped successfully${NC}"
echo "  Size: $(du -h "$DUMP_FILE" | cut -f1)"
echo ""

# Step 6: Restore to RDS
echo -e "${BLUE}[6/7] Restoring to RDS...${NC}"
echo ""
echo "This may take a while depending on data size..."
echo ""

PGPASSWORD="$RDS_PASSWORD" pg_restore \
    -h "$RDS_HOST" \
    -p "$RDS_PORT" \
    -U "$RDS_USER" \
    -d "$RDS_DB" \
    --no-owner \
    --no-acl \
    "$DUMP_FILE" 2>&1 | grep -v "WARNING" || true

echo ""
echo -e "${GREEN}✅ Database restored successfully${NC}"
echo ""

# Step 7: Verify migration
echo -e "${BLUE}[7/7] Verifying migration...${NC}"
echo ""

RDS_INSTRUMENTS_COUNT=$(PGPASSWORD="$RDS_PASSWORD" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -t -c "SELECT COUNT(*) FROM instruments;" 2>/dev/null | xargs || echo "0")
RDS_OHLCV_COUNT=$(PGPASSWORD="$RDS_PASSWORD" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -t -c "SELECT COUNT(*) FROM ohlcv_data;" 2>/dev/null | xargs || echo "0")

echo "EC2 Database:"
echo "  Instruments: $INSTRUMENTS_COUNT rows"
echo "  OHLCV Data:  $OHLCV_COUNT rows"
echo ""
echo "RDS Database:"
echo "  Instruments: $RDS_INSTRUMENTS_COUNT rows"
echo "  OHLCV Data:  $RDS_OHLCV_COUNT rows"
echo ""

if [ "$INSTRUMENTS_COUNT" = "$RDS_INSTRUMENTS_COUNT" ] && [ "$OHLCV_COUNT" = "$RDS_OHLCV_COUNT" ]; then
    echo -e "${GREEN}✅ Row counts match! Migration successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Row counts don't match${NC}"
    echo "Please investigate before using RDS database."
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Migration Complete!                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Backup saved to: $DUMP_FILE"
echo ""
echo "Next steps:"
echo "  1. Run verification script: ./scripts/verify-migration.sh"
echo "  2. Update application config to use RDS"
echo "  3. Test your application"
echo ""
echo "RDS Connection Details:"
echo "  Host: localhost"
echo "  Port: 5433"
echo "  Database: $RDS_DB"
echo "  User: $RDS_USER"
echo ""
