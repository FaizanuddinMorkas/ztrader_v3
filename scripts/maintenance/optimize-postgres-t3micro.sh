#!/bin/bash
# Optimize PostgreSQL for t3.micro (1GB RAM)
# This script configures PostgreSQL to run efficiently on limited resources

set -e

echo "========================================="
echo "PostgreSQL Optimization for t3.micro"
echo "========================================="
echo ""

# Detect PostgreSQL version and config path
PG_VERSION=$(psql --version | grep -oP '\d+' | head -1)
PG_CONF_DIR="/etc/postgresql/${PG_VERSION}/main"

if [ ! -d "$PG_CONF_DIR" ]; then
    echo "Searching for PostgreSQL config directory..."
    PG_CONF_DIR=$(sudo find /etc/postgresql -name "postgresql.conf" -type f 2>/dev/null | head -1 | xargs dirname)
    if [ -z "$PG_CONF_DIR" ]; then
        echo "✗ Could not find PostgreSQL config directory"
        exit 1
    fi
fi

echo "PostgreSQL config directory: $PG_CONF_DIR"
echo ""

# Backup original config
sudo cp "${PG_CONF_DIR}/postgresql.conf" "${PG_CONF_DIR}/postgresql.conf.backup"

# Apply optimized settings for t3.micro (1GB RAM)
sudo mkdir -p "${PG_CONF_DIR}/conf.d"
sudo tee "${PG_CONF_DIR}/conf.d/t3micro.conf" > /dev/null <<'EOF'
# Memory Settings (optimized for 1GB RAM)
shared_buffers = 128MB              # 25% of RAM (was default 128MB)
effective_cache_size = 512MB        # 50% of RAM
maintenance_work_mem = 64MB         # For VACUUM, CREATE INDEX
work_mem = 4MB                      # Per query operation (reduced from default)

# Connection Settings
max_connections = 20                # Reduced from default 100
superuser_reserved_connections = 3

# Write-Ahead Logging
wal_buffers = 4MB
min_wal_size = 80MB
max_wal_size = 1GB

# Query Planning
random_page_cost = 1.1              # For SSD storage
effective_io_concurrency = 200      # For SSD

# Background Writer
bgwriter_delay = 200ms
bgwriter_lru_maxpages = 100
bgwriter_lru_multiplier = 2.0

# Autovacuum (important for TimescaleDB)
autovacuum = on
autovacuum_max_workers = 2          # Reduced from default 3
autovacuum_naptime = 1min

# Logging (minimal to save resources)
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000   # Log slow queries (>1s)
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Lock Management
max_locks_per_transaction = 64      # Default, but important for TimescaleDB
max_pred_locks_per_transaction = 64

# Checkpoint Settings
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9
EOF

echo "✓ PostgreSQL configuration optimized"
echo ""

# Restart PostgreSQL
echo "Restarting PostgreSQL..."
sudo systemctl restart postgresql

# Check status
if sudo systemctl is-active --quiet postgresql; then
    echo "✓ PostgreSQL restarted successfully"
else
    echo "✗ PostgreSQL failed to start"
    echo "Check logs: sudo journalctl -u postgresql -n 50"
    exit 1
fi

echo ""
echo "========================================="
echo "Optimization Complete"
echo "========================================="
echo ""
echo "Key changes:"
echo "  - Reduced max_connections: 100 → 20"
echo "  - Reduced work_mem: 16MB → 4MB"
echo "  - Optimized for SSD storage"
echo "  - Enabled slow query logging (>1s)"
echo ""
echo "Monitor memory usage:"
echo "  free -h"
echo "  sudo systemctl status postgresql"
echo ""
