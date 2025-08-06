#!/usr/bin/env python3
"""
Minimal test to isolate monolithic mode issue.
"""

import os
import sys
import tempfile
import shutil
import psycopg
from psycopg import sql

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import PostgreSQLEnhanced directly
from postgresqlenhanced import PostgreSQLEnhanced

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def test_minimal_monolithic():
    """Minimal test of monolithic mode."""
    
    test_db = "test_minimal_mono"
    
    # Clean up any existing database
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
    
    # Create test directory
    temp_dir = tempfile.mkdtemp(prefix="minimal_mono_")
    tree_dir = os.path.join(temp_dir, "test_tree")
    os.makedirs(tree_dir)
    
    # Create config file for monolithic mode
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
    print("MINIMAL MONOLITHIC MODE TEST")
    print("=" * 60)
    
    try:
        # Create PostgreSQLEnhanced instance
        print("\n1. Creating PostgreSQLEnhanced instance...")
        db = PostgreSQLEnhanced()
        
        # Load the database
        print("2. Loading database with monolithic config...")
        db.load(tree_dir)
        
        print(f"   ✓ Database loaded successfully!")
        print(f"   Table prefix: {db.table_prefix}")
        
        # Check what tables were created
        print("\n3. Checking created tables...")
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
            
            print("   Tables in database:")
            for table in tables:
                print(f"     - {table[0]}")
        
        conn.close()
        
        # Test basic operations
        print("\n4. Testing basic operations...")
        count = db.get_number_of_people()
        print(f"   Number of people: {count}")
        
        db.close()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
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
        print(f"\n✓ Cleaned up test database: {test_db}")

if __name__ == "__main__":
    test_minimal_monolithic()