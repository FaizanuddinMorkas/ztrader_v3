# PostgreSQL + TimescaleDB Native Installation on EC2

## Overview

This guide shows how to install PostgreSQL 15 with TimescaleDB directly on Ubuntu EC2 (no Docker). This approach is:
- ✅ Simpler - no Docker overhead
- ✅ Better performance - native installation
- ✅ Easier to manage - standard PostgreSQL tools
- ✅ More stable - fewer moving parts

---

## Prerequisites

You should already have:
- EC2 instance running (Ubuntu 22.04, t2.micro)
- SSH access to the instance
- Security group allowing SSH from your IP

---

## Step-by-Step Installation

### 1. Connect to EC2

```bash
# On your local machine
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114
```

### 2. Update System

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget gnupg2 lsb-release
```

### 3. Install PostgreSQL 15

```bash
# Add PostgreSQL APT repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# Import repository signing key
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Update package list
sudo apt update

# Install PostgreSQL 15
sudo apt install -y postgresql-15 postgresql-contrib-15

# Verify installation
psql --version
```

### 4. Install TimescaleDB Extension

```bash
# Add TimescaleDB repository
echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | sudo tee /etc/apt/sources.list.d/timescaledb.list

# Import GPG key
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -

# Update and install
sudo apt update
sudo apt install -y timescaledb-2-postgresql-15

# Run TimescaleDB tuning script (optimizes PostgreSQL config)
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 5. Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Inside psql, run these commands:
```

```sql
-- Create database
CREATE DATABASE trading_db;

-- Create user with password
CREATE USER trading_user WITH PASSWORD 'YourSecurePassword123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;

-- Connect to the new database
\c trading_db

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO trading_user;

-- Verify TimescaleDB
\dx

-- Exit
\q
```

### 6. Configure Remote Access

```bash
# Edit PostgreSQL config to allow remote connections
sudo nano /etc/postgresql/15/main/postgresql.conf
```

**Find and modify this line:**
```conf
# Change from:
#listen_addresses = 'localhost'

# To:
listen_addresses = '*'
```

**Edit authentication config:**
```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

**Add this line at the end:**
```conf
# Allow connections from anywhere (we'll use SSH tunnel for security)
host    all             all             0.0.0.0/0               scram-sha-256
```

**Restart PostgreSQL:**
```bash
sudo systemctl restart postgresql

# Verify it's running
sudo systemctl status postgresql
```

### 7. Create Database Schema

```bash
# Create init script
cat > ~/init_database.sql <<'EOF'
-- Enable TimescaleDB extension (if not already done)
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
    interval VARCHAR(5) NOT NULL,
    CONSTRAINT ohlcv_pkey PRIMARY KEY (time, symbol, interval)
);

-- Convert to hypertable
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_interval ON ohlcv (interval);

-- Create signals table
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,
    strategy_name VARCHAR(50) NOT NULL,
    price NUMERIC(12, 4),
    confidence NUMERIC(3, 2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_time ON signals (time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals (symbol);

-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(10) NOT NULL,
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

-- Create positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    quantity NUMERIC(12, 4) NOT NULL,
    avg_price NUMERIC(12, 4) NOT NULL,
    current_price NUMERIC(12, 4),
    unrealized_pnl NUMERIC(12, 4),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create continuous aggregate for daily OHLCV
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

-- Add refresh policy
SELECT add_continuous_aggregate_policy('ohlcv_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Grant all permissions to trading_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO trading_user;

-- Success message
SELECT 'Database initialized successfully!' AS status;
EOF

# Run the initialization script
psql -U trading_user -d trading_db -f ~/init_database.sql

# Verify tables were created
psql -U trading_user -d trading_db -c "\dt"
```

---

## Local Connection via SSH Tunnel

### Method 1: Simple SSH Tunnel

```bash
# On your LOCAL machine
ssh -i ~/.ssh/trading-platform-key.pem -L 5432:localhost:5432 -N ubuntu@65.2.153.114
```

**In another terminal:**
```bash
# Connect with psql
psql -h localhost -p 5432 -U trading_user -d trading_db

# Or with Python
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='trading_db',
    user='trading_user',
    password='YourSecurePassword123!'
)
print('✅ Connected successfully!')
conn.close()
"
```

### Method 2: Create Tunnel Script

```bash
# On your LOCAL machine
cat > ~/connect-trading-db.sh <<'EOF'
#!/bin/bash
EC2_IP="65.2.153.114"
KEY_PATH="$HOME/.ssh/trading-platform-key.pem"

echo "🔌 Creating SSH tunnel to PostgreSQL..."
echo "Local: localhost:5432 → EC2:5432"
echo "Press Ctrl+C to close"
echo ""

ssh -i "$KEY_PATH" -L 5432:localhost:5432 -N ubuntu@$EC2_IP
EOF

chmod +x ~/connect-trading-db.sh

# Run it
~/connect-trading-db.sh
```

---

## Database Management

### Start/Stop/Restart PostgreSQL

```bash
# Check status
sudo systemctl status postgresql

# Start
sudo systemctl start postgresql

# Stop
sudo systemctl stop postgresql

# Restart
sudo systemctl restart postgresql

# Enable auto-start on boot
sudo systemctl enable postgresql
```

### Create Backup

```bash
# Manual backup
pg_dump -U trading_user -d trading_db -F c -f ~/backup_$(date +%Y%m%d).dump

# Or SQL format
pg_dump -U trading_user -d trading_db > ~/backup_$(date +%Y%m%d).sql
```

### Restore Backup

```bash
# From custom format
pg_restore -U trading_user -d trading_db ~/backup_20231216.dump

# From SQL format
psql -U trading_user -d trading_db < ~/backup_20231216.sql
```

### Automated Daily Backups

```bash
# Create backup script
cat > ~/backup_database.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/trading_db_$TIMESTAMP.sql.gz"

echo "📦 Creating backup..."
pg_dump -U trading_user trading_db | gzip > "$BACKUP_FILE"

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 7 backups
ls -t $BACKUP_DIR/trading_db_*.sql.gz | tail -n +8 | xargs -r rm

echo "🧹 Old backups cleaned"
EOF

chmod +x ~/backup_database.sh

# Test it
~/backup_database.sh

# Schedule daily at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * $HOME/backup_database.sh >> $HOME/backup.log 2>&1") | crontab -
```

---

## Performance Tuning

### Check Current Settings

```bash
sudo -u postgres psql -c "SHOW shared_buffers;"
sudo -u postgres psql -c "SHOW effective_cache_size;"
sudo -u postgres psql -c "SHOW maintenance_work_mem;"
```

### Optimize for t2.micro (1 GB RAM)

```bash
# Edit config
sudo nano /etc/postgresql/15/main/postgresql.conf
```

**Recommended settings for t2.micro:**
```conf
# Memory Settings
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 768MB        # 75% of RAM
maintenance_work_mem = 64MB
work_mem = 4MB

# Connection Settings
max_connections = 50

# WAL Settings
wal_buffers = 8MB
checkpoint_completion_target = 0.9

# Query Planner
random_page_cost = 1.1              # For SSD storage
effective_io_concurrency = 200

# Logging (for debugging)
log_min_duration_statement = 1000   # Log queries > 1 second
```

**Restart after changes:**
```bash
sudo systemctl restart postgresql
```

---

## Monitoring

### Check Database Size

```bash
psql -U trading_user -d trading_db -c "
SELECT 
    pg_size_pretty(pg_database_size('trading_db')) as db_size;
"
```

### Check Table Sizes

```bash
psql -U trading_user -d trading_db -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Check Active Connections

```bash
psql -U trading_user -d trading_db -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';
"
```

### View Slow Queries

```bash
psql -U trading_user -d trading_db -c "
SELECT 
    pid,
    now() - query_start as duration,
    query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;
"
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH
sudo ufw allow 22/tcp

# Don't expose PostgreSQL port directly
# (Use SSH tunnel instead)

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 2. Strong Password

```bash
# Change trading_user password
sudo -u postgres psql -c "ALTER USER trading_user WITH PASSWORD 'NewStrongPassword123!';"
```

### 3. Restrict pg_hba.conf (Optional - if using SSH tunnel only)

```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

**For maximum security (SSH tunnel only):**
```conf
# Only allow local connections
local   all             all                                     peer
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
```

---

## Troubleshooting

### PostgreSQL won't start

```bash
# Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Check service status
sudo systemctl status postgresql

# Check config syntax
sudo -u postgres /usr/lib/postgresql/15/bin/postgres -D /var/lib/postgresql/15/main --check
```

### Can't connect remotely

```bash
# Verify PostgreSQL is listening
sudo netstat -plnt | grep 5432

# Check if SSH tunnel is running (on local machine)
lsof -i :5432

# Test connection from EC2 itself
psql -U trading_user -d trading_db -h localhost
```

### Out of disk space

```bash
# Check disk usage
df -h

# Check PostgreSQL data directory
du -sh /var/lib/postgresql/15/main

# Clean old WAL files (if needed)
sudo -u postgres pg_archivecleanup /var/lib/postgresql/15/main/pg_wal 000000010000000000000001
```

---

## Quick Reference

### Common Commands

```bash
# Connect to database
psql -U trading_user -d trading_db

# List databases
psql -U postgres -l

# List tables
psql -U trading_user -d trading_db -c "\dt"

# Describe table
psql -U trading_user -d trading_db -c "\d ohlcv"

# Run SQL file
psql -U trading_user -d trading_db -f script.sql

# Export query results to CSV
psql -U trading_user -d trading_db -c "COPY (SELECT * FROM ohlcv LIMIT 100) TO STDOUT WITH CSV HEADER" > data.csv
```

---

## Next Steps

✅ PostgreSQL 15 installed natively  
✅ TimescaleDB extension enabled  
✅ Database schema created  
✅ SSH tunnel configured  
✅ Backups automated  

**Ready to build your Python trading application!** 🚀

See: [algo_trading_platform_research.md](./algo_trading_platform_research.md) for next steps.
