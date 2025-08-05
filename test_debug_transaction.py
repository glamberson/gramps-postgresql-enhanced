#!/usr/bin/env python3
"""
Debug test for transaction handling in monolithic mode.
"""

import os
import sys
import tempfile
import shutil
import psycopg
from psycopg import sql

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Gramps imports for testing
import mock_gramps

from postgresqlenhanced import PostgreSQLEnhanced
from connection import PostgreSQLConnection

# Import Gramps classes from mock
from gramps.gen.db import DbTxn
from gramps.gen.lib import Person, Name, Surname

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
    "shared_database": "gramps_debug_test",
}


def create_test_person(handle, gramps_id, first_name, surname_text):
    """Helper to create a Person object for testing."""
    person = Person()
    person.set_handle(handle)
    person.set_gramps_id(gramps_id)
    person.set_gender(Person.MALE)
    
    # Set name
    name = Name()
    name.set_first_name(first_name)
    surname = Surname()
    surname.set_surname(surname_text)
    name.add_surname(surname)
    person.set_primary_name(name)
    
    return person


def test_transaction_handling():
    """Test transaction handling in monolithic mode."""
    
    print("\n=== Setting Up Test Environment ===")
    
    # Create test database
    try:
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )
        admin_conn.autocommit = True
        
        with admin_conn.cursor() as cur:
            # Drop if exists
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(DB_CONFIG["shared_database"])
                )
            )
            
            # Create fresh
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DB_CONFIG["shared_database"])
                )
            )
            print(f"✓ Created database: {DB_CONFIG['shared_database']}")
        
        admin_conn.close()
        
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        raise
    
    # Create temporary directory for config
    temp_dir = tempfile.mkdtemp(prefix="gramps_debug_")
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
    
    print("\n=== Testing Transaction Handling ===")
    
    # Initialize database
    db = PostgreSQLEnhanced()
    db.load(tree_dir, None)
    
    # Create a person with explicit transaction
    person = create_test_person("TEST001", "I0001", "John", "Smith")
    
    print("\n1. Adding person with DbTxn context manager...")
    with DbTxn("Add Person", db) as trans:
        print("   - Entering transaction")
        db.add_person(person, trans)
        print("   - Person added to database")
    print("   - Exited transaction (should commit)")
    
    # Check if person was saved
    print("\n2. Checking if person was saved...")
    
    # Direct SQL check
    conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname=DB_CONFIG["shared_database"],
    )
    
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM test_tree_person
            """
        )
        count = cur.fetchone()[0]
        print(f"   - Direct SQL count: {count} person(s)")
        
        if count > 0:
            cur.execute(
                """
                SELECT handle, json_data->>'gramps_id' 
                FROM test_tree_person
                """
            )
            for row in cur.fetchall():
                print(f"     Found: handle={row[0]}, gramps_id={row[1]}")
    
    conn.close()
    
    # Also check via db API
    people = list(db.iter_people())
    print(f"   - DB API count: {len(people)} person(s)")
    
    for p in people:
        print(f"     Found: {p.get_primary_name().get_first_name()} {p.get_primary_name().get_surname()}")
    
    # Test manual commit
    print("\n3. Testing manual commit...")
    person2 = create_test_person("TEST002", "I0002", "Jane", "Doe")
    
    # Add without transaction context
    db.add_person(person2, None)
    print("   - Added person without transaction")
    
    # Manual commit
    if hasattr(db, 'dbapi'):
        print("   - Calling dbapi.commit()...")
        db.dbapi.commit()
    
    # Check count again
    conn = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname=DB_CONFIG["shared_database"],
    )
    
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM test_tree_person")
        count = cur.fetchone()[0]
        print(f"   - Final count: {count} person(s)")
    
    conn.close()
    
    # Cleanup
    print("\n=== Cleaning Up ===")
    
    db.close()
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
        cur.execute(
            sql.SQL("DROP DATABASE IF EXISTS {}").format(
                sql.Identifier(DB_CONFIG["shared_database"])
            )
        )
        print(f"✓ Dropped test database")
    
    admin_conn.close()
    
    if count >= 1:
        print("\n✓ Transaction handling is working!")
        return True
    else:
        print("\n✗ Transaction handling is NOT working - data not persisting")
        return False


if __name__ == "__main__":
    success = test_transaction_handling()
    sys.exit(0 if success else 1)