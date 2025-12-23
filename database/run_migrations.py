#!/usr/bin/env python3
"""
Enhanced Database Migration Runner with Tracking
Runs SQL migrations and tracks applied versions
"""

import os
import sys
import hashlib
from pathlib import Path
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")
    print("Install with: pip install python-dotenv")

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'trading_db'),
    'user': os.getenv('DB_USER', 'trading_user'),
}

# Add password only if provided
if os.getenv('DB_PASSWORD') or os.getenv('PGPASSWORD'):
    DB_CONFIG['password'] = os.getenv('DB_PASSWORD') or os.getenv('PGPASSWORD')

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_color(message, color):
    """Print colored message"""
    print(f"{color}{message}{Colors.NC}")

def get_file_checksum(filepath):
    """Calculate MD5 checksum of file"""
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

def create_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print_color(f"✗ Failed to connect to database: {e}", Colors.RED)
        sys.exit(1)

def ensure_tracking_table(conn):
    """Ensure schema_migrations table exists"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200),
                applied_at TIMESTAMPTZ DEFAULT NOW(),
                checksum VARCHAR(64)
            );
        """)
        conn.commit()

def is_migration_applied(conn, version):
    """Check if migration has been applied"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE version = %s",
            (version,)
        )
        return cur.fetchone()[0] > 0

def record_migration(conn, version, name, checksum):
    """Record applied migration"""
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO schema_migrations (version, name, checksum) 
               VALUES (%s, %s, %s)""",
            (version, name, checksum)
        )
        conn.commit()

def apply_migration(conn, filepath):
    """Apply a single migration file"""
    with open(filepath, 'r') as f:
        sql_content = f.read()
    
    with conn.cursor() as cur:
        cur.execute(sql_content)
        conn.commit()

def main():
    print("=" * 50)
    print("Database Migration Runner (Python)")
    print("=" * 50)
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Port: {DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")
    print("=" * 50)
    print()

    # Connect to database
    print_color("Testing database connection...", Colors.YELLOW)
    conn = create_connection()
    print_color("✓ Database connection successful", Colors.GREEN)
    print()

    # Check TimescaleDB
    print_color("Checking TimescaleDB extension...", Colors.YELLOW)
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
        if cur.fetchone():
            print_color("✓ TimescaleDB extension is installed", Colors.GREEN)
        else:
            print_color("✗ TimescaleDB extension not found", Colors.RED)
            print("Installing TimescaleDB extension...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
            conn.commit()
            print_color("✓ TimescaleDB extension installed", Colors.GREEN)
    print()

    # Initialize tracking
    print_color("Initializing migration tracking...", Colors.YELLOW)
    ensure_tracking_table(conn)
    print_color("✓ Migration tracking initialized", Colors.GREEN)
    print()

    # Find migrations directory
    script_dir = Path(__file__).parent
    migrations_dir = script_dir / 'migrations'
    
    if not migrations_dir.exists():
        print_color(f"✗ Migrations directory not found: {migrations_dir}", Colors.RED)
        sys.exit(1)

    # Scan and apply migrations
    print_color("Scanning migrations...", Colors.YELLOW)
    print()

    migration_files = sorted(migrations_dir.glob('*.sql'))
    total_migrations = 0
    skipped_migrations = 0
    new_migrations = 0

    for migration_file in migration_files:
        filename = migration_file.name
        
        # Skip tracking table migration (already applied)
        if filename == '00_schema_migrations.sql':
            continue
        
        # Extract version and name
        version = filename.split('_')[0]
        name = filename.replace(f'{version}_', '').replace('.sql', '')
        
        total_migrations += 1
        
        # Check if already applied
        if is_migration_applied(conn, version):
            print_color(f"⊙ Skipping (already applied): {filename}", Colors.BLUE)
            skipped_migrations += 1
        else:
            print_color(f"▶ Applying migration: {filename}", Colors.YELLOW)
            
            try:
                # Calculate checksum
                checksum = get_file_checksum(migration_file)
                
                # Apply migration
                apply_migration(conn, migration_file)
                
                # Record migration
                record_migration(conn, version, name, checksum)
                
                print_color(f"✓ Successfully applied: {filename}", Colors.GREEN)
                new_migrations += 1
            except Exception as e:
                print_color(f"✗ Failed to apply: {filename}", Colors.RED)
                print(f"Error: {e}")
                conn.rollback()
                sys.exit(1)
        
        print()

    # Summary
    print("=" * 50)
    print_color("Migration Summary", Colors.GREEN)
    print("=" * 50)
    print(f"Total migrations found: {total_migrations}")
    print(f"Already applied: {skipped_migrations}")
    print(f"Newly applied: {new_migrations}")
    print(f"Total applied: {skipped_migrations + new_migrations}")
    print("=" * 50)
    print()

    # Show migration history
    if total_migrations > 0:
        print_color("Migration History:", Colors.YELLOW)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT version, name, applied_at 
                FROM schema_migrations 
                ORDER BY version
            """)
            for row in cur.fetchall():
                print(f"  {row[0]} | {row[1]} | {row[2]}")
        print()

    # Show tables
    print_color("Database Tables:", Colors.YELLOW)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        for row in cur.fetchall():
            print(f"  - {row[0]}")
    print()

    # Show hypertables
    print_color("TimescaleDB Hypertables:", Colors.YELLOW)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT hypertable_schema, hypertable_name, num_dimensions 
            FROM timescaledb_information.hypertables
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"  - {row[0]}.{row[1]} ({row[2]} dimensions)")
        else:
            print("  No hypertables found")
    print()

    # Final message
    if new_migrations > 0:
        print_color(f"✓ {new_migrations} new migration(s) applied successfully!", Colors.GREEN)
    else:
        print_color("✓ Database schema is up to date!", Colors.GREEN)

    conn.close()

if __name__ == '__main__':
    main()
