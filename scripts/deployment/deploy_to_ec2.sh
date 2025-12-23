#!/bin/bash
# Deploy trading platform to EC2

set -e  # Exit on error

# Configuration
EC2_USER="ubuntu"
EC2_HOST="$1"  # Pass EC2 IP as first argument
SSH_KEY="$2"   # Pass SSH key path as second argument
REMOTE_DIR="~/ztrader"
LOCAL_DIR="/Users/faizanuddinmorkas/Work/Personal/ztrader_new"

if [ -z "$EC2_HOST" ]; then
    echo "Usage: $0 <EC2_IP_ADDRESS> [SSH_KEY_PATH]"
    echo "Example: $0 54.123.45.67 ~/.ssh/my-key.pem"
    exit 1
fi

# Build SSH command with key if provided
SSH_CMD="ssh"
RSYNC_SSH="ssh"
if [ -n "$SSH_KEY" ]; then
    SSH_CMD="ssh -i $SSH_KEY"
    RSYNC_SSH="ssh -i $SSH_KEY"
    echo "Using SSH key: $SSH_KEY"
fi

echo "========================================="
echo "Deploying to EC2: $EC2_USER@$EC2_HOST"
echo "========================================="
echo

# Step 1: Create remote directory
echo "Step 1: Creating remote directory..."
$SSH_CMD "$EC2_USER@$EC2_HOST" "mkdir -p $REMOTE_DIR"

# Step 2: Transfer code
echo "Step 2: Transferring code..."
rsync -avz --progress \
    -e "$RSYNC_SSH" \
    --exclude='venv' \
    --exclude='logs' \
    --exclude='cache' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    "$LOCAL_DIR/" \
    "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"

echo
echo "Step 3: Setting up environment on EC2..."
$SSH_CMD "$EC2_USER@$EC2_HOST" << 'ENDSSH'
cd ~/ztrader

# Install Python and dependencies
echo "Installing Python packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install requirements
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Upgrade yfinance to v1.0 (fixes API issues)
echo "Upgrading yfinance to latest version..."
pip install --upgrade yfinance

echo
echo "✓ Environment setup complete!"
ENDSSH

# Step 4: Create .env.example template (don't touch existing .env)
echo
echo "Step 4: Creating .env.example template..."
$SSH_CMD "$EC2_USER@$EC2_HOST" << 'ENDSSH'
cd ~/ztrader

# Create .env.example as a template (never overwrite .env)
cat > .env.example << 'EOF'
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=trading_user
DB_PASSWORD=your_secure_password_here

# Data Configuration
DATA_CACHE_DIR=./cache
DATA_LOG_DIR=./logs

# Trading Configuration
DEFAULT_TIMEFRAMES=1m,5m,15m,1h,1d
YFINANCE_MAX_WORKERS=10

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
EOF

# Only create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env created from template (remember to update with your actual values!)"
else
    echo "✓ .env.example created (existing .env preserved)"
fi
ENDSSH

echo
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo
echo "Next steps:"
echo "1. SSH into EC2: ssh $EC2_USER@$EC2_HOST"
echo "2. Update DB password: nano ~/ztrader/.env"
echo "3. Activate venv: source ~/ztrader/venv/bin/activate"
echo "4. Seed database: python scripts/database/seed_nifty100.py"
echo "5. Run sync: python sync_data.py --timeframe 1d --full"
echo
echo "========================================="
