#!/usr/bin/env python3
"""
Migrate PostgreSQL database from EC2 to RDS
Pure Python implementation using psycopg2 - no pg_dump/pg_restore needed
"""

import psycopg2
import sys
from datetime import datetime
from getpass import getpass

# Colors for terminal output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'

# Configuration
EC2_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'trading_user',
    'database': 'trading_db'
}

RDS_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'faizy',
    'database': 'trading_db'
}

def print_header(text):
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}{text.center(60)}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print()

def print_step(step, total, text):
    print(f"{Colors.BLUE}[{step}/{total}] {text}{Colors.NC}")
    print()

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")

def test_connection(config, password, name):
    """Test database connection"""
    print(f"Testing {name} connection...")
    try:
        conn = psycopg2.connect(**config, password=password, connect_timeout=5)
        conn.close()
        print_success(f"{name} connection successful")
        return True
    except Exception as e:
        print_error(f"Cannot connect to {name}")
        print(f"  Error: {e}")
        return False

def get_row_count(config, password, table):
    """Get row count for a table"""
    try:
        conn = psycopg2.connect(**config, password=password)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except:
        return 0

def copy_table_data(ec2_conn, rds_conn, table_name):
    """Copy data from EC2 table to RDS table"""
    ec2_cur = ec2_conn.cursor()
    rds_cur = rds_conn.cursor()
    
    # Get column names
    ec2_cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        ORDER BY ordinal_position;
    """)
    columns = [row[0] for row in ec2_cur.fetchall()]
    columns_str = ', '.join(columns)
    
    # Fetch all data from EC2
    print(f"  Copying {table_name}...")
    ec2_cur.execute(f"SELECT {columns_str} FROM {table_name};")
    
    # Insert into RDS in batches
    batch_size = 1000
    total_rows = 0
    
    while True:
        rows = ec2_cur.fetchmany(batch_size)
        if not rows:
            break
        
        # Build INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Execute batch insert
        for row in rows:
            try:
                rds_cur.execute(insert_sql, row)
            except Exception as e:
                # Skip duplicates or conflicts
                rds_conn.rollback()
                continue
        
        rds_conn.commit()
        total_rows += len(rows)
        print(f"    Copied {total_rows:,} rows...", end='\r')
    
    print(f"    Copied {total_rows:,} rows total")
    
    ec2_cur.close()
    rds_cur.close()
    return total_rows

def main():
    print_header("EC2 to RDS PostgreSQL Migration")
    
    # Get passwords
    ec2_password = getpass(f"Enter EC2 PostgreSQL password for user '{EC2_CONFIG['user']}': ")
    rds_password = getpass(f"Enter RDS PostgreSQL password for user '{RDS_CONFIG['user']}': ")
    print()
    
    # Step 1: Verify connections
    print_step(1, 6, "Verifying database connections...")
    
    if not test_connection(EC2_CONFIG, ec2_password, "EC2 PostgreSQL"):
        print()
        print("Make sure:")
        print("  1. The EC2 tunnel is running: ./scripts/connect-postgres.sh")
        print("  2. Password is correct")
        print()
        sys.exit(1)
    
    # Test RDS connection to postgres database first
    rds_test_config = RDS_CONFIG.copy()
    rds_test_config['database'] = 'postgres'
    
    if not test_connection(rds_test_config, rds_password, "RDS PostgreSQL"):
        print()
        print("Make sure:")
        print("  1. The RDS tunnel is running: ./scripts/connect-rds.sh")
        print("  2. Password is correct")
        print()
        sys.exit(1)
    
    print()
    
    # Step 2: Check EC2 database
    print_step(2, 6, "Checking EC2 database...")
    
    instruments_count = get_row_count(EC2_CONFIG, ec2_password, "instruments")
    ohlcv_count = get_row_count(EC2_CONFIG, ec2_password, "ohlcv_data")
    
    print(f"  Instruments: {instruments_count:,} rows")
    print(f"  OHLCV Data:  {ohlcv_count:,} rows")
    print()
    
    if instruments_count == 0 and ohlcv_count == 0:
        print_warning("EC2 database appears to be empty")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)
        print()
    
    # Step 3: Create database and schema on RDS
    print_step(3, 6, "Setting up RDS database...")
    
    try:
        # Connect to postgres database to create trading_db
        conn = psycopg2.connect(**rds_test_config, password=rds_password)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{RDS_CONFIG['database']}';")
        db_exists = cur.fetchone() is not None
        
        if db_exists:
            print_warning(f"Database '{RDS_CONFIG['database']}' already exists on RDS")
            response = input("Drop and recreate? This will DELETE all existing data! (y/N): ")
            if response.lower() == 'y':
                print("Terminating active connections...")
                # Terminate all connections to the database
                cur.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{RDS_CONFIG['database']}'
                    AND pid <> pg_backend_pid();
                """)
                print("Dropping existing database...")
                cur.execute(f"DROP DATABASE {RDS_CONFIG['database']};")
                print_success("Database dropped")
            else:
                print("Migration cancelled.")
                sys.exit(0)
        
        print(f"Creating database '{RDS_CONFIG['database']}'...")
        cur.execute(f"CREATE DATABASE {RDS_CONFIG['database']};")
        print_success("Database created")
        
        cur.close()
        conn.close()
        
        # Connect to new database and create TimescaleDB extension
        conn = psycopg2.connect(**RDS_CONFIG, password=rds_password)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Installing TimescaleDB extension...")
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            print_success("TimescaleDB extension installed")
        except Exception as e:
            print_warning(f"Could not install TimescaleDB (RDS doesn't support it by default)")
            print("  Continuing with regular PostgreSQL tables...")
            print("  Note: Hypertable optimizations won't be available")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print_error(f"Failed to setup RDS database: {e}")
        sys.exit(1)
    
    print()
    
    # Step 4: Copy schema
    print_step(4, 6, "Copying database schema...")
    
    try:
        ec2_conn = psycopg2.connect(**EC2_CONFIG, password=ec2_password)
        rds_conn = psycopg2.connect(**RDS_CONFIG, password=rds_password)
        rds_conn.autocommit = True
        
        ec2_cur = ec2_conn.cursor()
        rds_cur = rds_conn.cursor()
        
        # Get table definitions
        ec2_cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        tables = [row[0] for row in ec2_cur.fetchall()]
        
        print(f"  Found {len(tables)} tables to migrate")
        
        # Get full schema dump for each table
        for table in tables:
            print(f"  Creating table: {table}")
            
            # Get CREATE TABLE statement
            ec2_cur.execute(f"""
                SELECT 
                    'CREATE TABLE ' || quote_ident(tablename) || ' (' ||
                    string_agg(
                        quote_ident(attname) || ' ' || 
                        format_type(atttypid, atttypmod) ||
                        CASE WHEN attnotnull THEN ' NOT NULL' ELSE '' END,
                        ', '
                    ) || ');'
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = '{table}' 
                AND n.nspname = 'public'
                AND a.attnum > 0 
                AND NOT a.attisdropped
                GROUP BY tablename;
            """)
            
            create_stmt = ec2_cur.fetchone()
            if create_stmt:
                try:
                    rds_cur.execute(create_stmt[0])
                except Exception as e:
                    print_warning(f"    Could not create {table}: {e}")
        
        print_success("Schema copied")
        
        ec2_cur.close()
        rds_cur.close()
        ec2_conn.close()
        rds_conn.close()
        
    except Exception as e:
        print_error(f"Failed to copy schema: {e}")
        sys.exit(1)
    
    print()
    
    # Step 5: Copy data
    print_step(5, 6, "Copying data...")
    
    try:
        ec2_conn = psycopg2.connect(**EC2_CONFIG, password=ec2_password)
        rds_conn = psycopg2.connect(**RDS_CONFIG, password=rds_password)
        
        # Copy instruments table
        copy_table_data(ec2_conn, rds_conn, 'instruments')
        
        # Copy ohlcv_data table
        copy_table_data(ec2_conn, rds_conn, 'ohlcv_data')
        
        ec2_conn.close()
        rds_conn.close()
        
        print_success("Data copied")
        
    except Exception as e:
        print_error(f"Failed to copy data: {e}")
        print(f"  Error details: {e}")
        sys.exit(1)
    
    print()
    
    # Step 6: Verify migration
    print_step(6, 6, "Verifying migration...")
    
    rds_instruments_count = get_row_count(RDS_CONFIG, rds_password, "instruments")
    rds_ohlcv_count = get_row_count(RDS_CONFIG, rds_password, "ohlcv_data")
    
    print("EC2 Database:")
    print(f"  Instruments: {instruments_count:,} rows")
    print(f"  OHLCV Data:  {ohlcv_count:,} rows")
    print()
    print("RDS Database:")
    print(f"  Instruments: {rds_instruments_count:,} rows")
    print(f"  OHLCV Data:  {rds_ohlcv_count:,} rows")
    print()
    
    if instruments_count == rds_instruments_count and ohlcv_count == rds_ohlcv_count:
        print_success("Row counts match! Migration successful!")
    else:
        print_warning("Row counts don't match")
        print("Please investigate before using RDS database.")
    
    print()
    print_header("Migration Complete!")
    print()
    print("Next steps:")
    print("  1. Update application config to use RDS")
    print("  2. Test your application")
    print()
    print("RDS Connection Details:")
    print(f"  Host: localhost")
    print(f"  Port: {RDS_CONFIG['port']}")
    print(f"  Database: {RDS_CONFIG['database']}")
    print(f"  User: {RDS_CONFIG['user']}")
    print()

if __name__ == "__main__":
    main()
