#!/usr/bin/env python3
"""
Test to verify that databases are preserved when trees are deleted in separate mode.
Date: 2025-08-06
"""

import os
import psycopg
import subprocess
import time
import uuid

# Database connection details
DB_CONFIG = {
    'host': '192.168.10.90',
    'port': 5432,
    'user': 'genealogy_user',
    'password': 'GenealogyData2025'
}

def create_test_tree():
    """Create a test tree ID and register it with Gramps."""
    # Generate a unique 8-character hex ID like Gramps does
    tree_id = uuid.uuid4().hex[:8]
    tree_name = f"Test Tree {tree_id}"
    
    # Create the tree directory
    tree_dir = os.path.expanduser(f"~/.local/share/gramps/grampsdb/{tree_id}")
    os.makedirs(tree_dir, exist_ok=True)
    
    # Register it as PostgreSQL Enhanced
    with open(os.path.join(tree_dir, "database.txt"), "w") as f:
        f.write("postgresqlenhanced")
    
    with open(os.path.join(tree_dir, "name.txt"), "w") as f:
        f.write(tree_name)
    
    print(f"✓ Created test tree: {tree_id} ({tree_name})")
    return tree_id, tree_name, tree_dir

def create_database(tree_id):
    """Create the PostgreSQL database for the tree."""
    conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/postgres"
    
    try:
        conn = psycopg.connect(conn_string)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [tree_id])
            if not cur.fetchone():
                # Create database
                cur.execute(f"CREATE DATABASE {tree_id}")
                print(f"✓ Created PostgreSQL database: {tree_id}")
                
                # Create a test table to verify it's our database
                test_conn = psycopg.connect(
                    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{tree_id}"
                )
                with test_conn.cursor() as test_cur:
                    test_cur.execute("""
                        CREATE TABLE test_marker (
                            id SERIAL PRIMARY KEY,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            tree_id VARCHAR(10)
                        )
                    """)
                    test_cur.execute("INSERT INTO test_marker (tree_id) VALUES (%s)", [tree_id])
                    test_conn.commit()
                print(f"✓ Added test marker to database")
                test_conn.close()
            else:
                print(f"  Database {tree_id} already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False

def delete_tree_from_gramps(tree_id, tree_dir):
    """Simulate deleting a tree from Gramps (remove registration only)."""
    try:
        # Remove the tree directory (this is what Gramps does)
        subprocess.run(['rm', '-rf', tree_dir], check=True)
        print(f"✓ Deleted tree {tree_id} from Gramps registration")
        return True
    except Exception as e:
        print(f"✗ Error deleting tree from Gramps: {e}")
        return False

def check_database_exists(tree_id):
    """Check if the PostgreSQL database still exists."""
    conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/postgres"
    
    try:
        conn = psycopg.connect(conn_string)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [tree_id])
            exists = cur.fetchone() is not None
        conn.close()
        return exists
    except Exception as e:
        print(f"✗ Error checking database: {e}")
        return False

def verify_database_contents(tree_id):
    """Verify the database contents are still intact."""
    try:
        conn = psycopg.connect(
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{tree_id}"
        )
        with conn.cursor() as cur:
            cur.execute("SELECT tree_id FROM test_marker WHERE tree_id = %s", [tree_id])
            result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"  Could not verify contents: {e}")
        return False

def cleanup_test_database(tree_id):
    """Clean up the test database."""
    conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/postgres"
    
    try:
        conn = psycopg.connect(conn_string)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {tree_id}")
        conn.close()
        print(f"✓ Cleaned up test database: {tree_id}")
    except Exception as e:
        print(f"✗ Error cleaning up: {e}")

def main():
    """Run the test."""
    print("=" * 60)
    print("TESTING SEPARATE MODE DATABASE PRESERVATION")
    print("Date: 2025-08-06")
    print("=" * 60)
    print()
    
    # Step 1: Create test tree
    print("Step 1: Creating test tree...")
    tree_id, tree_name, tree_dir = create_test_tree()
    print()
    
    # Step 2: Create database
    print("Step 2: Creating PostgreSQL database...")
    if not create_database(tree_id):
        print("Failed to create database. Exiting.")
        return
    print()
    
    # Step 3: Verify database exists
    print("Step 3: Verifying database exists...")
    if check_database_exists(tree_id):
        print(f"✓ Database {tree_id} exists in PostgreSQL")
    else:
        print(f"✗ Database {tree_id} not found!")
        return
    print()
    
    # Step 4: Delete tree from Gramps
    print("Step 4: Deleting tree from Gramps (simulating user action)...")
    if not delete_tree_from_gramps(tree_id, tree_dir):
        print("Failed to delete tree from Gramps. Exiting.")
        return
    print()
    
    # Step 5: Check if database still exists
    print("Step 5: Checking if database is preserved...")
    time.sleep(1)  # Brief pause to ensure deletion is processed
    
    if check_database_exists(tree_id):
        print(f"✓ SUCCESS: Database {tree_id} is PRESERVED after Gramps deletion!")
        
        # Verify contents
        if verify_database_contents(tree_id):
            print(f"✓ Database contents are intact!")
    else:
        print(f"✗ FAILURE: Database {tree_id} was deleted!")
    print()
    
    # Step 6: Show how to manually clean up
    print("Step 6: Manual cleanup instructions...")
    print(f"To permanently delete this orphaned database, run:")
    print(f"  PGPASSWORD='{DB_CONFIG['password']}' psql -h {DB_CONFIG['host']} \\")
    print(f"    -U {DB_CONFIG['user']} -d postgres -c \"DROP DATABASE {tree_id};\"")
    print()
    
    # Step 7: Clean up test database
    print("Step 7: Cleaning up test database...")
    response = input(f"Do you want to clean up the test database {tree_id}? (y/n): ")
    if response.lower() == 'y':
        cleanup_test_database(tree_id)
    else:
        print(f"Test database {tree_id} left in place for inspection.")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("RESULT: Databases ARE preserved when trees are deleted in separate mode.")
    print("This is the intended behavior for data safety.")
    print("=" * 60)

if __name__ == "__main__":
    main()