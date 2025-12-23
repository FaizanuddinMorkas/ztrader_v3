# Complete Guide: Deploy Trading Platform on AWS EC2 Free Tier

## Overview

This guide walks you through deploying a complete Python algorithmic trading platform on AWS EC2 free tier using Docker. Everything will run on a single EC2 instance:
- PostgreSQL + TimescaleDB (in Docker)
- Python Trading Application (in Docker)
- All accessible locally via SSH tunnel

**Cost**: FREE for 12 months (AWS Free Tier)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [AWS EC2 Setup](#2-aws-ec2-setup)
3. [Server Configuration](#3-server-configuration)
4. [Docker Installation](#4-docker-installation)
5. [Database Deployment](#5-database-deployment)
6. [Application Deployment](#6-application-deployment)
7. [Local Connection Setup](#7-local-connection-setup)
8. [Monitoring & Maintenance](#8-monitoring--maintenance)

---

## 1. Prerequisites

### On Your Local Machine

```bash
# macOS - Install required tools
brew install awscli

# Verify installation
aws --version
```

### AWS Account Setup

1. **Create AWS Account**: https://aws.amazon.com/free/
2. **Configure AWS CLI**:
   ```bash
   aws configure
   # Enter your:
   # - AWS Access Key ID
   # - AWS Secret Access Key
   # - Default region (e.g., us-east-1)
   # - Default output format: json
   ```

---

## 2. AWS EC2 Setup

### Step 1: Launch EC2 Instance

#### Option A: Using AWS Console (Beginner-Friendly)

1. **Go to EC2 Dashboard**: https://console.aws.amazon.com/ec2/
2. **Click "Launch Instance"**
3. **Configure Instance**:
   - **Name**: `trading-platform-server`
   - **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance Type**: `t2.micro` (1 vCPU, 1 GB RAM - Free tier)
   - **Key Pair**: Create new key pair
     - Name: `trading-platform-key`
     - Type: RSA
     - Format: `.pem`
     - **Download and save** `trading-platform-key.pem`
   - **Network Settings**:
     - ✅ Allow SSH traffic from: My IP
     - ✅ Allow HTTP traffic (optional)
     - ✅ Allow HTTPS traffic (optional)
   - **Storage**: 30 GB gp3 (Free tier allows up to 30 GB)
4. **Click "Launch Instance"**

#### Option B: Using AWS CLI (Advanced)

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name trading-platform-key \
  --query 'KeyMaterial' \
  --output text > trading-platform-key.pem

# Set permissions
chmod 400 trading-platform-key.pem

# Create security group
aws ec2 create-security-group \
  --group-name trading-platform-sg \
  --description "Security group for trading platform"

# Get your IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress \
  --group-name trading-platform-sg \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t2.micro \
  --key-name trading-platform-key \
  --security-groups trading-platform-sg \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=trading-platform-server}]'
```

### Step 2: Get Instance Details

```bash
# Get instance public IP
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=trading-platform-server" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text

# Save this IP address - you'll need it!
export EC2_IP="your-instance-public-ip"
```

### Step 3: Connect to EC2 Instance

```bash
# Move key to ~/.ssh directory
mv trading-platform-key.pem ~/.ssh/
chmod 400 ~/.ssh/trading-platform-key.pem

# SSH into instance
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@$EC2_IP

ssh -i ~/.ssh/trading-platform-key.pem ubuntu@$65.2.153.114

# You should now be connected to your EC2 instance!
```

---

## 3. Server Configuration

### Run these commands on your EC2 instance:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
  curl \
  wget \
  git \
  vim \
  htop \
  net-tools

# Set timezone to UTC (recommended for trading)
sudo timedatectl set-timezone UTC

# Verify
date
```

---

## 4. Docker Installation

### Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group (avoid using sudo)
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# IMPORTANT: Log out and log back in for group changes to take effect
exit
```

```bash
# SSH back in
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@$EC2_IP

# Verify docker works without sudo
docker ps
```

---

## 5. Database Deployment

### Step 1: Create Project Directory

```bash
# Create project structure
mkdir -p ~/trading-platform/{database,app,logs,backups}
cd ~/trading-platform
```

### Step 2: Create Docker Compose File

```bash
# Create docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  # PostgreSQL + TimescaleDB
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: trading-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-SecurePassword123!}
      TIMESCALEDB_TELEMETRY: off
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backups:/backups
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading_user -d trading_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - trading-network

  # Trading Application (we'll add this later)
  # trading-app:
  #   build: ./app
  #   container_name: trading-app
  #   restart: unless-stopped
  #   depends_on:
  #     - postgres
  #   environment:
  #     DATABASE_URL: postgresql://trading_user:${DB_PASSWORD:-SecurePassword123!}@postgres:5432/trading_db
  #     ENVIRONMENT: production
  #   volumes:
  #     - ./app:/app
  #     - ./logs:/app/logs
  #   networks:
  #     - trading-network

volumes:
  postgres-data:
    driver: local

networks:
  trading-network:
    driver: bridge
EOF
```

### Step 3: Create Database Initialization Script

```bash
# Create init.sql
cat > database/init.sql <<'EOF'
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create OHLCV table for market data
CREATE TABLE IF NOT EXISTS ohlcv (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open NUMERIC(12, 4),
    high NUMERIC(12, 4),
    low NUMERIC(12, 4),
    close NUMERIC(12, 4),
    volume BIGINT,
    interval VARCHAR(5) NOT NULL,  -- '1m', '5m', '1h', '1d'
    CONSTRAINT ohlcv_pkey PRIMARY KEY (time, symbol, interval)
);

-- Convert to hypertable (TimescaleDB feature for time-series optimization)
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_interval ON ohlcv (interval);

-- Create table for trading signals
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL', 'HOLD'
    strategy_name VARCHAR(50) NOT NULL,
    price NUMERIC(12, 4),
    confidence NUMERIC(3, 2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_time ON signals (time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals (symbol);
CREATE INDEX IF NOT EXISTS idx_signals_strategy ON signals (strategy_name);

-- Create table for executed trades
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL'
    quantity NUMERIC(12, 4) NOT NULL,
    price NUMERIC(12, 4) NOT NULL,
    commission NUMERIC(12, 4) DEFAULT 0,
    pnl NUMERIC(12, 4),
    strategy_name VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_time ON trades (time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol);

-- Create table for portfolio positions
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    quantity NUMERIC(12, 4) NOT NULL,
    avg_price NUMERIC(12, 4) NOT NULL,
    current_price NUMERIC(12, 4),
    unrealized_pnl NUMERIC(12, 4),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create continuous aggregate for daily OHLCV from minute data
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    symbol,
    interval,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume
FROM ohlcv
GROUP BY day, symbol, interval;

-- Add refresh policy (refresh every hour)
SELECT add_continuous_aggregate_policy('ohlcv_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Database initialized successfully!';
    RAISE NOTICE '✅ TimescaleDB extension enabled';
    RAISE NOTICE '✅ Tables created: ohlcv, signals, trades, positions';
    RAISE NOTICE '✅ Continuous aggregate created: ohlcv_daily';
END $$;
EOF
```

### Step 4: Create Environment File

```bash
# Create .env file for sensitive data
cat > .env <<'EOF'
# Database Configuration
DB_PASSWORD=YourSecurePasswordHere123!

# Change this to a strong password!
# Example: $(openssl rand -base64 32)
EOF

# Secure the .env file
chmod 600 .env
```

### Step 5: Start Database

```bash
# Start PostgreSQL + TimescaleDB
docker-compose up -d postgres

# Check logs
docker-compose logs -f postgres

# Wait for "database system is ready to accept connections"
# Press Ctrl+C to exit logs

# Verify database is running
docker ps

# Test connection
docker exec -it trading-db psql -U trading_user -d trading_db -c "\dx"

# You should see TimescaleDB extension listed
```

---

## 6. Application Deployment

### Step 1: Create Application Structure

```bash
cd ~/trading-platform/app

# Create directory structure
mkdir -p {config,data,strategies,indicators,backtesting,risk,execution,monitoring,tests}

# Create __init__.py files
touch {config,data,strategies,indicators,backtesting,risk,execution,monitoring,tests}/__init__.py
```

### Step 2: Create Dockerfile

```bash
cat > Dockerfile <<'EOF'
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Run application
CMD ["python", "main.py"]
EOF
```

### Step 3: Create requirements.txt

```bash
cat > requirements.txt <<'EOF'
# Data & Analysis
pandas==2.1.4
numpy==1.26.2
yfinance==0.2.33

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# Technical Analysis
pandas-ta==0.3.14b0
ta-lib==0.4.28

# Backtesting
backtrader==1.9.78.123

# Notifications
python-telegram-bot==20.7

# Utilities
python-dotenv==1.0.0
requests==2.31.0
schedule==1.2.1

# Logging & Monitoring
loguru==0.7.2
EOF
```

### Step 4: Update Docker Compose

```bash
# Update docker-compose.yml to include the app
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: trading-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-SecurePassword123!}
      TIMESCALEDB_TELEMETRY: off
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backups:/backups
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading_user -d trading_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - trading-network

  trading-app:
    build: ./app
    container_name: trading-app
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://trading_user:${DB_PASSWORD:-SecurePassword123!}@postgres:5432/trading_db
      ENVIRONMENT: production
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: trading_db
      DB_USER: trading_user
      DB_PASSWORD: ${DB_PASSWORD:-SecurePassword123!}
    volumes:
      - ./app:/app
      - ./logs:/app/logs
    networks:
      - trading-network

volumes:
  postgres-data:
    driver: local

networks:
  trading-network:
    driver: bridge
EOF
```

---

## 7. Local Connection Setup

### Method 1: SSH Tunnel (Recommended)

```bash
# On your LOCAL machine, create a tunnel script
cat > ~/connect-trading-db.sh <<'EOF'
#!/bin/bash
# Replace with your EC2 IP
EC2_IP="your-ec2-ip-here"
KEY_PATH="$HOME/.ssh/trading-platform-key.pem"

echo "🔌 Creating SSH tunnel to trading database..."
echo "Local port 5432 → EC2:5432"
echo "Press Ctrl+C to close tunnel"
echo ""

ssh -i "$KEY_PATH" \
    -L 5432:localhost:5432 \
    -N \
    ubuntu@$EC2_IP
EOF

chmod +x ~/connect-trading-db.sh

# Run the tunnel
~/connect-trading-db.sh
```

**In another terminal, connect:**

```bash
# Install PostgreSQL client (if not already installed)
brew install postgresql@15

# Connect to database
psql -h localhost -p 5432 -U trading_user -d trading_db
```

### Method 2: Python Connection

```python
# test_connection.py
import psycopg2
from sqlalchemy import create_engine, text

# Connection via SSH tunnel
DATABASE_URL = "postgresql://trading_user:YourPassword@localhost:5432/trading_db"

# Test with psycopg2
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    print("✅ Connected:", cursor.fetchone()[0])
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")

# Test with SQLAlchemy
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM ohlcv;"))
        print(f"✅ OHLCV records: {result.fetchone()[0]}")
except Exception as e:
    print(f"❌ Query failed: {e}")
```

---

## 8. Monitoring & Maintenance

### Check Container Status

```bash
# SSH into EC2
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@$EC2_IP

# Check running containers
docker ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f postgres
docker-compose logs -f trading-app

# Check resource usage
docker stats
```

### Database Backup

```bash
# Create backup script
cat > ~/trading-platform/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/trading-platform/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

echo "📦 Creating database backup..."

docker exec trading-db pg_dump -U trading_user trading_db | gzip > "$BACKUP_FILE"

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 7 backups
ls -t $BACKUP_DIR/backup_*.sql.gz | tail -n +8 | xargs -r rm

echo "🧹 Old backups cleaned up"
EOF

chmod +x ~/trading-platform/backup.sh

# Run backup manually
~/trading-platform/backup.sh

# Or schedule with cron (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/trading-platform/backup.sh") | crontab -
```

### Restore from Backup

```bash
# List backups
ls -lh ~/trading-platform/backups/

# Restore
gunzip < ~/trading-platform/backups/backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i trading-db psql -U trading_user -d trading_db
```

### System Monitoring

```bash
# Check disk space
df -h

# Check memory
free -h

# Check CPU
htop

# Check Docker disk usage
docker system df
```

---

## 9. Security Best Practices

### Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw enable

# Verify
sudo ufw status
```

### Update Security Group (AWS Console)

1. Go to EC2 → Security Groups
2. Select your security group
3. Edit Inbound Rules:
   - **SSH (22)**: Your IP only (not 0.0.0.0/0)
   - Remove any other open ports

### Regular Updates

```bash
# Update system packages weekly
sudo apt update && sudo apt upgrade -y

# Update Docker images monthly
cd ~/trading-platform
docker-compose pull
docker-compose up -d
```

---

## 10. Cost Optimization

### Free Tier Limits

- **EC2**: 750 hours/month of t2.micro (enough for 1 instance 24/7)
- **EBS**: 30 GB storage
- **Data Transfer**: 15 GB outbound per month

### Tips to Stay Free

1. **Use only 1 t2.micro instance**
2. **Keep storage under 30 GB**
3. **Monitor data transfer** (use CloudWatch)
4. **Stop instance when not needed**:
   ```bash
   # Stop instance (data persists)
   aws ec2 stop-instances --instance-ids i-xxxxx
   
   # Start instance
   aws ec2 start-instances --instance-ids i-xxxxx
   ```

---

## 11. Quick Reference Commands

### SSH Connection
```bash
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@$EC2_IP
```

### Start/Stop Services
```bash
cd ~/trading-platform
docker-compose up -d      # Start all services
docker-compose down       # Stop all services
docker-compose restart    # Restart all services
```

### View Logs
```bash
docker-compose logs -f postgres
docker-compose logs -f trading-app
```

### Database Access
```bash
# From EC2
docker exec -it trading-db psql -U trading_user -d trading_db

# From local (with tunnel)
psql -h localhost -p 5432 -U trading_user -d trading_db
```

---

## Next Steps

1. ✅ EC2 instance running
2. ✅ Docker installed
3. ✅ Database deployed
4. ✅ Local connection established
5. 🔄 **Next**: Build your trading application
6. 🔄 **Next**: Implement strategies
7. 🔄 **Next**: Set up monitoring

**Ready to start building your trading platform!** 🚀
