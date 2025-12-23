#!/bin/bash

# Quick script to run migrations on EC2 database via SSH tunnel
# Assumes connect-postgres.sh is already running in another terminal

echo "========================================="
echo "Running Database Migrations on EC2"
echo "========================================="
echo ""
echo "Prerequisites:"
echo "  1. SSH tunnel must be active (./connect-postgres.sh)"
echo "  2. TimescaleDB extension must be installed"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Set database connection parameters for local tunnel
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=trading_db
export DB_USER=trading_user

# Run migrations
cd "$(dirname "$0")"
./database/run_migrations.sh
