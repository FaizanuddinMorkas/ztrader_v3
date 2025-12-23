#!/bin/bash
# RDS Connection via EC2 SSH Tunnel

set -e

# Configuration
EC2_USER="ubuntu"
EC2_HOST="65.2.153.114"
SSH_KEY="$HOME/.ssh/trading-platform-key.pem"

# RDS Configuration
RDS_ENDPOINT="ztrader-rds.czu8qa80wiox.ap-south-1.rds.amazonaws.com"
RDS_PORT=5432
DB_NAME="postgres"
DB_USER="faizy"

# Local port to use (different from EC2 PostgreSQL)
LOCAL_PORT=5433

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 RDS SSH Tunnel Connection via EC2${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Validate configuration
if [[ "$RDS_ENDPOINT" == "your-rds-endpoint"* ]]; then
    echo -e "${RED}❌ Please update RDS_ENDPOINT in the script${NC}"
    echo ""
    echo "Edit this file and set:"
    echo "  RDS_ENDPOINT - Your RDS endpoint hostname"
    echo "  RDS_PORT     - Your RDS port (default: 5432)"
    echo "  DB_NAME      - Your database name"
    echo "  DB_USER      - Your database user"
    echo ""
    exit 1
fi

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${YELLOW}⚠️  SSH key not found: $SSH_KEY${NC}"
    exit 1
fi

# Check if local port is already in use
if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port $LOCAL_PORT is already in use!${NC}"
    echo ""
    echo "Options:"
    echo "  1. Kill existing process: lsof -ti:$LOCAL_PORT | xargs kill -9"
    echo "  2. Use different port: LOCAL_PORT=5434 ./connect-rds.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ SSH Key found${NC}"
echo -e "${GREEN}✅ Port $LOCAL_PORT available${NC}"
echo ""
echo "Creating SSH tunnel to RDS via EC2..."
echo "  Local:     localhost:$LOCAL_PORT"
echo "  EC2:       $EC2_HOST"
echo "  RDS:       $RDS_ENDPOINT:$RDS_PORT"
echo ""
echo -e "${BLUE}Connection Details:${NC}"
echo "  Host:     localhost"
echo "  Port:     $LOCAL_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo ""
echo -e "${BLUE}Connection String:${NC}"
echo "  postgresql://$DB_USER:<password>@localhost:$LOCAL_PORT/$DB_NAME"
echo ""
echo -e "${YELLOW}Press Ctrl+C to close tunnel${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create SSH tunnel
# -L local_port:rds_endpoint:rds_port
ssh -i "$SSH_KEY" \
    -L $LOCAL_PORT:$RDS_ENDPOINT:$RDS_PORT \
    -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    $EC2_USER@$EC2_HOST
