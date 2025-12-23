#!/usr/bin/env python3
"""
Simple PostgreSQL connection test
Usage: 
  export DB_PASSWORD='your-password'
  python test_simple.py
"""

import sys
import os

# Configuration - EDIT THESE
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "trading_db"
DB_USER = "trading_user"
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # Set via: export DB_PASSWORD='your-password'

def main():
    print("🧪 PostgreSQL Connection Test")
    print("=" * 60)
    
    # Check password
    if not DB_PASSWORD:
        print("❌ DB_PASSWORD not set!")
        print()
        print("Set it with:")
        print("  export DB_PASSWORD='your-actual-password'")
        print("  python test_simple.py")
        print()
        print("Or edit test_simple.py and set DB_PASSWORD directly")
        return False
    
    # Check psycopg2
    try:
        import psycopg2
        print("✅ psycopg2 installed")
    except ImportError:
        print("❌ psycopg2 not installed")
        print("   pip install psycopg2-binary")
        return False
    
    # Connect
    print(f"🔌 Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("✅ Connected successfully!")
        
        # Run queries
        cursor = conn.cursor()
        
        # PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n📊 PostgreSQL: {version[:60]}...")
        
        # TimescaleDB
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname='timescaledb';")
        result = cursor.fetchone()
        if result:
            print(f"✅ TimescaleDB: v{result[0]}")
        else:
            print("⚠️  TimescaleDB not installed")
        
        # Tables
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname='public'
            ORDER BY tablename;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Tables ({len(tables)}):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} records")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Database is ready! 🚀")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Is SSH tunnel running? ./connect-postgres.sh")
        print("2. Check tunnel: lsof -i :5432")
        print("3. Verify password is correct")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
