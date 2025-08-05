#!/usr/bin/env python3
"""
Direct test of commit functionality bypassing the mock framework.
"""

import os
import sys
import tempfile
import shutil
import psycopg
from psycopg import sql

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from postgresqlenhanced import PostgreSQLEnhanced
from connection import PostgreSQLConnection

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
    "shared_database": "gramps_commit_test",
}


def test_direct_commit():
    """Test commit directly without mock framework."""
    
    print("\n=== Direct Commit Test ===")
    
    # Create test database
    admin_conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname="postgres",
    )
    admin_conn.autocommit = True
    
    with admin_conn.cursor() as cur:
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(DB_CONFIG["shared_database"])
        ))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DB_CONFIG["shared_database"])
        ))
        print(f"✓ Created database: {DB_CONFIG['shared_database']}")
    
    admin_conn.close()
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="gramps_commit_")
    tree_dir = os.path.join(temp_dir, "test_tree")
    os.makedirs(tree_dir)
    
    config_file = os.path.join(tree_dir, "connection_info.txt")
    with open(config_file, "w") as f:
        f.write(f"""# PostgreSQL Connection Configuration
host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = monolithic
shared_database_name = {DB_CONFIG['shared_database']}
""")
    
    # Initialize database
    db = PostgreSQLEnhanced()
    db.load(tree_dir, None)
    
    print("\n1. Testing direct SQL insert with manual commit...")
    
    # Get the actual connection (unwrap if needed)
    if hasattr(db.dbapi, '_connection'):
        # It's wrapped
        actual_conn = db.dbapi._connection
        print("   - Using unwrapped connection")
    else:
        actual_conn = db.dbapi
        print("   - Using direct connection")
    
    # Direct SQL insert
    actual_conn.execute(
        """
        INSERT INTO test_tree_person (handle, json_data)
        VALUES (%s, %s)
        """,
        ["DIRECT001", '{"gramps_id": "D001", "gender": 1}']
    )
    print("   - Inserted row")
    
    # Explicit commit
    if hasattr(actual_conn, 'commit'):
        actual_conn.commit()
        print("   - Called commit()")
    elif hasattr(actual_conn, '_commit'):
        actual_conn._commit()
        print("   - Called _commit()")
    
    # Check if data persisted
    print("\n2. Checking if data persisted...")
    
    check_conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname=DB_CONFIG["shared_database"],
    )
    
    with check_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM test_tree_person")
        count = cur.fetchone()[0]
        print(f"   - Found {count} row(s)")
        
        if count > 0:
            cur.execute("SELECT handle, json_data FROM test_tree_person")
            for row in cur.fetchall():
                print(f"     Handle: {row[0]}, Data: {row[1]}")
    
    check_conn.close()
    
    # Test with autocommit
    print("\n3. Testing with autocommit mode...")
    
    # Get underlying psycopg connection
    if hasattr(actual_conn, '_connection'):
        psycopg_conn = actual_conn._connection
    else:
        psycopg_conn = actual_conn
    
    # Enable autocommit
    old_autocommit = psycopg_conn.autocommit
    psycopg_conn.autocommit = True
    print(f"   - Set autocommit=True (was {old_autocommit})")
    
    # Insert another row
    actual_conn.execute(
        """
        INSERT INTO test_tree_person (handle, json_data)
        VALUES (%s, %s)
        """,
        ["AUTO001", '{"gramps_id": "A001", "gender": 2}']
    )
    print("   - Inserted row with autocommit")
    
    # Check count
    actual_conn.execute("SELECT COUNT(*) FROM test_tree_person")
    result = actual_conn.fetchone()
    print(f"   - Current count: {result[0]} row(s)")
    
    # Restore autocommit setting
    psycopg_conn.autocommit = old_autocommit
    
    # Cleanup
    print("\n=== Cleanup ===")
    db.close()
    shutil.rmtree(temp_dir)
    
    admin_conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname="postgres",
    )
    admin_conn.autocommit = True
    
    with admin_conn.cursor() as cur:
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(DB_CONFIG["shared_database"])
        ))
        print("✓ Dropped test database")
    
    admin_conn.close()
    
    return count > 0


if __name__ == "__main__":
    success = test_direct_commit()
    if success:
        print("\n✓ Commit is working!")
    else:
        print("\n✗ Commit is NOT working")
    sys.exit(0 if success else 1)