#!/bin/bash
# Complete fix for PostgreSQL on EC2 t3.micro
# Run this on EC2 to fix "out of shared memory" errors

set -e

echo "========================================="
echo "Fixing PostgreSQL on EC2 t3.micro"
echo "========================================="
echo ""

# Find PostgreSQL config
PG_CONF=$(sudo -u postgres psql -t -P format=unaligned -c 'SHOW config_file;')
PG_DIR=$(dirname "$PG_CONF")

echo "PostgreSQL config: $PG_CONF"
echo ""

# Backup
sudo cp "$PG_CONF" "${PG_CONF}.backup"
echo "✓ Backed up config"

# Apply critical fix for "out of shared memory"
sudo tee "${PG_DIR}/conf.d/fix-memory.conf" > /dev/null <<'EOF'
# Fix for "out of shared memory" error
max_locks_per_transaction = 256

# Memory optimization for t3.micro (1GB RAM)
shared_buffers = 128MB
effective_cache_size = 512MB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 20

# Performance
random_page_cost = 1.1
effective_io_concurrency = 200
EOF

echo "✓ Applied configuration"

# Restart PostgreSQL
sudo systemctl restart postgresql
sleep 2

if sudo systemctl is-active --quiet postgresql; then
    echo "✓ PostgreSQL restarted successfully"
    echo ""
    echo "Configuration applied:"
    echo "  max_locks_per_transaction: 64 → 256"
    echo "  max_connections: 100 → 20"
    echo "  Memory optimized for 1GB RAM"
    echo ""
    echo "You can now run 75m candle generation!"
else
    echo "✗ PostgreSQL failed to restart"
    exit 1
fi
