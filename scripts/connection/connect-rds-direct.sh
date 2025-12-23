#!/bin/bash
# Direct RDS Connection Script
# This connects directly to RDS without SSH tunnel

set -e

# Configuration - UPDATE THESE VALUES
RDS_ENDPOINT="your-rds-endpoint.xxxxxxxxxxxx.region.rds.amazonaws.com"
RDS_PORT=5432
DB_NAME="your_database_name"
DB_USER="your_db_user"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Direct RDS Connection${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Validate configuration
if [[ "$RDS_ENDPOINT" == "your-rds-endpoint"* ]]; then
    echo -e "${RED}❌ Please update RDS configuration in the script${NC}"
    echo ""
    echo "Edit this file and set:"
    echo "  RDS_ENDPOINT - Your RDS endpoint hostname"
    echo "  RDS_PORT     - Your RDS port (default: 5432)"
    echo "  DB_NAME      - Your database name"
    echo "  DB_USER      - Your database user"
    echo ""
    echo "Find your RDS endpoint:"
    echo "  AWS Console → RDS → Databases → Your DB → Connectivity & security"
    echo ""
    exit 1
fi

echo -e "${BLUE}Testing RDS connectivity...${NC}"
echo ""

# Test network connectivity
if command -v nc &> /dev/null; then
    if nc -zv -w5 "$RDS_ENDPOINT" "$RDS_PORT" 2>&1 | grep -q "succeeded\|open"; then
        echo -e "${GREEN}✅ Network connection successful${NC}"
    else
        echo -e "${RED}❌ Cannot reach RDS endpoint${NC}"
        echo ""
        echo "Possible issues:"
        echo "  1. RDS security group doesn't allow your IP"
        echo "  2. RDS is not publicly accessible"
        echo "  3. Wrong endpoint or port"
        echo ""
        echo "Your current public IP:"
        curl -s ifconfig.me
        echo ""
        echo ""
        echo "Add this IP to RDS security group:"
        echo "  AWS Console → RDS → Your DB → VPC security group"
        echo "  Edit inbound rules → Add rule:"
        echo "    Type: PostgreSQL, Port: 5432, Source: My IP"
        echo ""
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  'nc' not found, skipping connectivity test${NC}"
fi

echo ""
echo -e "${BLUE}Connection Details:${NC}"
echo "  Host:     $RDS_ENDPOINT"
echo "  Port:     $RDS_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo ""
echo -e "${BLUE}Connection String:${NC}"
echo "  postgresql://$DB_USER:<password>@$RDS_ENDPOINT:$RDS_PORT/$DB_NAME"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if psql is available
if command -v psql &> /dev/null; then
    echo -e "${GREEN}Connecting with psql...${NC}"
    echo ""
    psql -h "$RDS_ENDPOINT" -p "$RDS_PORT" -U "$DB_USER" -d "$DB_NAME"
else
    echo -e "${YELLOW}⚠️  'psql' not found${NC}"
    echo ""
    echo "Install PostgreSQL client:"
    echo "  brew install postgresql"
    echo ""
    echo "Then connect manually:"
    echo "  psql -h $RDS_ENDPOINT -p $RDS_PORT -U $DB_USER -d $DB_NAME"
    echo ""
fi
