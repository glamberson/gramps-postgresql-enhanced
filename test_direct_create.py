#!/usr/bin/env python3
"""
Test creating tables directly through the connection to understand the issue.
"""

import psycopg
from psycopg import sql
import sys
import os

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from connection import PostgreSQLConnection

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def test_direct_create():
    """Test creating tables directly."""
    
    # Create test database
    test_db = "test_direct"
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
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db)))
    admin_conn.close()
    
    # Use PostgreSQLConnection wrapper
    conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{test_db}"
    pg_conn = PostgreSQLConnection(conn_string)
    
    try:
        print("Testing direct table creation through PostgreSQLConnection:")
        print("=" * 60)
        
        # Test 1: Create table with quoted name
        print("\n1. Creating table with quoted name")
        pg_conn.execute('''
            CREATE TABLE IF NOT EXISTS "test_prefix_metadata" (
                setting VARCHAR(255) PRIMARY KEY,
                value TEXT
            )
        ''')
        pg_conn.commit()
        print("  ✓ Table created")
        
        # Test 2: Check if table exists
        print("\n2. Checking if table exists")
        exists = pg_conn.table_exists('"test_prefix_metadata"')  # With quotes
        print(f"  With quotes: {exists}")
        exists = pg_conn.table_exists('test_prefix_metadata')  # Without quotes
        print(f"  Without quotes: {exists}")
        
        # Test 3: Insert data
        print("\n3. Inserting data")
        pg_conn.execute('''
            INSERT INTO "test_prefix_metadata" (setting, value)
            VALUES (%s, %s)
        ''', ['key1', 'value1'])
        pg_conn.commit()
        print("  ✓ Data inserted")
        
        # Test 4: Now wrap with TablePrefixWrapper
        print("\n4. Testing with TablePrefixWrapper")
        from postgresqlenhanced import TablePrefixWrapper
        
        wrapped = TablePrefixWrapper(pg_conn, "wrapped_")
        
        # Create table through wrapper
        print("  Creating table through wrapper")
        wrapped.execute('''
            CREATE TABLE IF NOT EXISTS "wrapped_test" (
                id SERIAL PRIMARY KEY,
                data TEXT
            )
        ''')
        wrapped.commit()
        print("  ✓ Table created through wrapper")
        
        # Check what tables exist
        print("\n5. Listing all tables")
        result = pg_conn.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = pg_conn.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        pg_conn.close()
        
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
    test_direct_create()