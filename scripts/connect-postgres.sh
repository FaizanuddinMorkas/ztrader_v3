#!/bin/bash
# EC2 PostgreSQL Connection via SSH Tunnel

set -e

# Configuration
EC2_USER="ubuntu"
EC2_HOST="65.2.153.114"
SSH_KEY="$HOME/.ssh/trading-platform-key.pem"
LOCAL_PORT=5432
REMOTE_PORT=5432
DB_USER="trading_user"
DB_NAME="trading_db"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 PostgreSQL SSH Tunnel Connection${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

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
    echo "  2. Use different port: LOCAL_PORT=5433 ./connect-postgres.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ SSH Key found${NC}"
echo -e "${GREEN}✅ Port $LOCAL_PORT available${NC}"
echo ""
echo "Creating SSH tunnel..."
echo "  Local:  localhost:$LOCAL_PORT"
echo "  Remote: $EC2_HOST:$REMOTE_PORT"
echo ""
echo -e "${BLUE}Connection Details:${NC}"
echo "  Host:     localhost"
echo "  Port:     $LOCAL_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo ""
echo -e "${YELLOW}Press Ctrl+C to close tunnel${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create SSH tunnel
ssh -i "$SSH_KEY" \
    -L $LOCAL_PORT:localhost:$REMOTE_PORT \
    -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    $EC2_USER@$EC2_HOST
