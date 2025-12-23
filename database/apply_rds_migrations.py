#!/usr/bin/env python3
"""
Apply RDS migrations without TimescaleDB
"""

import psycopg2
from src.config.settings import DatabaseConfig

def main():
    print("=" * 60)
    print("Applying RDS Migrations")
    print("=" * 60)
    
    config = DatabaseConfig()
    
    print(f"Connecting to:")
    print(f"  Host: {config.HOST}")
    print(f"  Port: {config.PORT}")
    print(f"  Database: {config.NAME}")
    print(f"  User: {config.USER}")
    print()
    
    # Connect to database
    conn = psycopg2.connect(
        host=config.HOST,
        port=config.PORT,
        database=config.NAME,
        user=config.USER,
        password=config.PASSWORD
    )
    
    print("✅ Connected successfully")
    print()
    
    cur = conn.cursor()
    
    # Read and execute migration SQL
    with open('database/rds_migrations.sql', 'r') as f:
        sql = f.read()
   
    print("Applying migrations...")
    cur.execute(sql)
    conn.commit()
    
    print("✅ Migrations applied successfully!")
    print()
    
    # Show applied migrations
    cur.execute('SELECT * FROM schema_migrations ORDER BY version')
    print("Applied migrations:")
    for row in cur.fetchall():
        print(f"  [{row[0]}] {row[2]} (applied: {row[1]})")
    
    print()
    
    # Verify tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    
    print("Created tables:")
    for row in cur.fetchall():
        print(f"  - {row[0]}")
    
    cur.close()
    conn.close()
    
    print()
    print("=" * 60)
    print("✅ RDS database setup complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
