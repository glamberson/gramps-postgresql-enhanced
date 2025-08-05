#!/usr/bin/env python3
"""
Debug script to understand monolithic mode table creation issue.
"""

import os
import sys
import tempfile
import psycopg
from psycopg import sql

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def test_table_creation():
    """Test how table names are created in monolithic mode."""
    
    # Create test database
    test_db = "test_debug_mono"
    admin_conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname="postgres",
    )
    admin_conn.autocommit = True
    
    with admin_conn.cursor() as cur:
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db)))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db)))
    admin_conn.close()
    
    # Create test directory structure
    temp_dir = tempfile.mkdtemp(prefix="debug_mono_")
    tree_dir = os.path.join(temp_dir, "test_tree")
    os.makedirs(tree_dir)
    
    # Create config file
    config_file = os.path.join(tree_dir, "connection_info.txt")
    with open(config_file, "w") as f:
        f.write(f"""host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = monolithic
shared_database_name = {test_db}
""")
    
    print("=" * 60)
    print("TESTING TABLE CREATION IN MONOLITHIC MODE")
    print("=" * 60)
    
    # Import and initialize PostgreSQLEnhanced
    from postgresqlenhanced import PostgreSQLEnhanced
    
    # Add debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        db = PostgreSQLEnhanced()
        
        # Check what happens during load
        print("\nLoading database...")
        db.load(tree_dir)
        
        print(f"\nTable prefix: {db.table_prefix}")
        print(f"Database mode: monolithic")
        
        # Check what tables were created
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=test_db,
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = cur.fetchall()
            
            print("\nTables created:")
            for table in tables:
                print(f"  - {table[0]}")
        
        conn.close()
        db.close()
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
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

if __name__ == "__main__":
    test_table_creation()