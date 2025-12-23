#!/bin/bash
# Verify migration from EC2 to RDS
# Compares row counts and schema between EC2 and RDS databases

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

RDS_HOST="localhost"
RDS_PORT=5433
RDS_USER="faizy"
RDS_DB="trading_db"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Migration Verification                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verify connections
echo -e "${BLUE}[1/4] Verifying connections...${NC}"
echo ""

if ! PGPASSWORD="${EC2_PASSWORD:-}" psql -h "$EC2_HOST" -p "$EC2_PORT" -U "$EC2_USER" -d "$EC2_DB" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to EC2 PostgreSQL${NC}"
    echo "Make sure the EC2 tunnel is running: ./scripts/connect-postgres.sh"
    exit 1
fi

if ! PGPASSWORD="${RDS_PASSWORD:-}" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to RDS PostgreSQL${NC}"
    echo "Make sure the RDS tunnel is running: ./scripts/connect-rds.sh"
    exit 1
fi

echo -e "${GREEN}✅ Both connections successful${NC}"
echo ""

# Compare row counts
echo -e "${BLUE}[2/4] Comparing row counts...${NC}"
echo ""

# Instruments table
EC2_INSTRUMENTS=$(PGPASSWORD="${EC2_PASSWORD:-}" psql -h "$EC2_HOST" -p "$EC2_PORT" -U "$EC2_USER" -d "$EC2_DB" -t -c "SELECT COUNT(*) FROM instruments;" 2>/dev/null | xargs || echo "0")
RDS_INSTRUMENTS=$(PGPASSWORD="${RDS_PASSWORD:-}" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -t -c "SELECT COUNT(*) FROM instruments;" 2>/dev/null | xargs || echo "0")

echo "Instruments table:"
echo "  EC2: $EC2_INSTRUMENTS rows"
echo "  RDS: $RDS_INSTRUMENTS rows"

if [ "$EC2_INSTRUMENTS" = "$RDS_INSTRUMENTS" ]; then
    echo -e "  ${GREEN}✅ Match${NC}"
else
    echo -e "  ${RED}❌ Mismatch${NC}"
fi
echo ""

# OHLCV data table
EC2_OHLCV=$(PGPASSWORD="${EC2_PASSWORD:-}" psql -h "$EC2_HOST" -p "$EC2_PORT" -U "$EC2_USER" -d "$EC2_DB" -t -c "SELECT COUNT(*) FROM ohlcv_data;" 2>/dev/null | xargs || echo "0")
RDS_OHLCV=$(PGPASSWORD="${RDS_PASSWORD:-}" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -t -c "SELECT COUNT(*) FROM ohlcv_data;" 2>/dev/null | xargs || echo "0")

echo "OHLCV data table:"
echo "  EC2: $EC2_OHLCV rows"
echo "  RDS: $RDS_OHLCV rows"

if [ "$EC2_OHLCV" = "$RDS_OHLCV" ]; then
    echo -e "  ${GREEN}✅ Match${NC}"
else
    echo -e "  ${RED}❌ Mismatch${NC}"
fi
echo ""

# Check TimescaleDB hypertables
echo -e "${BLUE}[3/4] Checking TimescaleDB hypertables...${NC}"
echo ""

RDS_HYPERTABLES=$(PGPASSWORD="${RDS_PASSWORD:-}" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -t -c "SELECT COUNT(*) FROM timescaledb_information.hypertables WHERE hypertable_name='ohlcv_data';" 2>/dev/null | xargs || echo "0")

if [ "$RDS_HYPERTABLES" = "1" ]; then
    echo -e "${GREEN}✅ ohlcv_data is a hypertable on RDS${NC}"
else
    echo -e "${YELLOW}⚠️  ohlcv_data is NOT a hypertable on RDS${NC}"
    echo "TimescaleDB may not be installed or hypertable not created."
fi
echo ""

# Sample data comparison
echo -e "${BLUE}[4/4] Comparing sample data...${NC}"
echo ""

echo "Top 5 symbols by data count (EC2):"
PGPASSWORD="${EC2_PASSWORD:-}" psql -h "$EC2_HOST" -p "$EC2_PORT" -U "$EC2_USER" -d "$EC2_DB" -c "SELECT symbol, COUNT(*) as count FROM ohlcv_data GROUP BY symbol ORDER BY count DESC LIMIT 5;" 2>/dev/null || echo "No data"
echo ""

echo "Top 5 symbols by data count (RDS):"
PGPASSWORD="${RDS_PASSWORD:-}" psql -h "$RDS_HOST" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DB" -c "SELECT symbol, COUNT(*) as count FROM ohlcv_data GROUP BY symbol ORDER BY count DESC LIMIT 5;" 2>/dev/null || echo "No data"
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Verification Summary                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

ALL_MATCH=true

if [ "$EC2_INSTRUMENTS" != "$RDS_INSTRUMENTS" ]; then
    ALL_MATCH=false
fi

if [ "$EC2_OHLCV" != "$RDS_OHLCV" ]; then
    ALL_MATCH=false
fi

if [ "$ALL_MATCH" = true ]; then
    echo -e "${GREEN}✅ All row counts match!${NC}"
    echo -e "${GREEN}✅ Migration appears successful!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Update your application config to use RDS"
    echo "  2. Test your application thoroughly"
    echo "  3. Once confirmed, you can stop the EC2 PostgreSQL"
else
    echo -e "${RED}❌ Some row counts don't match${NC}"
    echo ""
    echo "Please investigate before using RDS database."
    echo "Check migration logs for errors."
fi
echo ""
