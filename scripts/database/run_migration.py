#!/usr/bin/env python3
"""
Run database migration for user tracking
"""
import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_migration():
    """Run the user tracking migration"""
    
    # Get database credentials
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        # Construct from individual variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        if not all([db_name, db_user, db_password]):
            print("❌ Database credentials not set in environment")
            print("Required: DB_NAME, DB_USER, DB_PASSWORD")
            return False
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print(f"🔄 Connecting to database: {db_name}@{db_host}:{db_port}")
    print("=" * 60)
    
    # Read migration SQL
    migration_file = project_root / 'scripts' / 'database' / 'migrations' / '003_add_user_tracking.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print("🔄 Running migration: 003_add_user_tracking.sql")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Execute migration
            cur.execute(migration_sql)
            
            # Verify tables created
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('telegram_users', 'user_queries')
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cur.fetchall()]
            
            print("\n✅ Migration completed successfully!")
            print(f"\nTables created: {', '.join(tables)}")
            
            # Check materialized view
            cur.execute("""
                SELECT matviewname 
                FROM pg_matviews 
                WHERE matviewname = 'user_stats'
            """)
            
            if cur.fetchone():
                print("Materialized view created: user_stats")
            
            # Check views
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name IN ('active_users', 'pending_users', 'recent_activity')
                ORDER BY table_name
            """)
            
            views = [row[0] for row in cur.fetchall()]
            if views:
                print(f"Views created: {', '.join(views)}")
            
            # Check functions
            cur.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('refresh_user_stats', 'get_daily_active_users', 'get_user_hourly_queries')
                ORDER BY routine_name
            """)
            
            functions = [row[0] for row in cur.fetchall()]
            if functions:
                print(f"Functions created: {', '.join(functions)}")
            
            print("\n" + "=" * 60)
            print("✅ Database schema ready for user tracking!")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
