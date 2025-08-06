#!/usr/bin/env python3
"""
Simple test to isolate the monolithic mode table creation issue.
"""

import psycopg
from psycopg import sql

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def test_quoted_table_names():
    """Test how PostgreSQL handles quoted table names."""
    
    # Create test database
    test_db = "test_quotes"
    admin_conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname="postgres",
    )
    admin_conn.autocommit = True
    
    with admin_conn.cursor() as cur:
        # Force disconnect existing connections
        cur.execute("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
              AND pid <> pg_backend_pid()
        """, [test_db])
        
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db)))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db)))
    admin_conn.close()
    
    # Connect to test database
    conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname=test_db,
    )
    
    try:
        with conn.cursor() as cur:
            # Test 1: Create table with quoted name
            print("Test 1: Creating table with quoted name")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS "test_tree_metadata" (
                    setting VARCHAR(255) PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()
            print("  ✓ Table created")
            
            # Test 2: Check if table exists using information_schema
            print("\nTest 2: Checking table existence")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, ["test_tree_metadata"])  # Note: unquoted in parameter
            exists = cur.fetchone()[0]
            print(f"  Table exists (unquoted check): {exists}")
            
            # Test 3: Insert into quoted table
            print("\nTest 3: Inserting into quoted table")
            cur.execute('''
                INSERT INTO "test_tree_metadata" (setting, value)
                VALUES (%s, %s)
            ''', ['test_key', 'test_value'])
            conn.commit()
            print("  ✓ Insert successful")
            
            # Test 4: Select from quoted table
            print("\nTest 4: Selecting from quoted table")
            cur.execute('SELECT * FROM "test_tree_metadata"')
            rows = cur.fetchall()
            print(f"  Found {len(rows)} row(s): {rows}")
            
            # Test 5: List all tables
            print("\nTest 5: Listing all tables")
            cur.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = cur.fetchall()
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        
        # Drop test database
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )
        admin_conn.autocommit = True
        
        with admin_conn.cursor() as cur:
            # Force disconnect
            cur.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = %s
                  AND pid <> pg_backend_pid()
            """, [test_db])
            
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db)))
        admin_conn.close()
        print(f"\n✓ Cleaned up test database: {test_db}")

if __name__ == "__main__":
    test_quoted_table_names()