#!/usr/bin/env python3
"""Debug test to understand data persistence issue."""

import os
import sys
import tempfile
import psycopg
from psycopg import sql

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Gramps imports
import mock_gramps
from postgresqlenhanced import PostgreSQLEnhanced
from gramps.gen.db import DbTxn
from gramps.gen.lib import Person, Name, Surname

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def test_separate_mode():
    """Test data persistence in separate mode."""
    print("\n=== Testing Separate Mode Data Persistence ===")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_persist_")
    tree_name = "test_persist_db"
    tree_path = os.path.join(temp_dir, tree_name)
    os.makedirs(tree_path, exist_ok=True)
    
    # Create config
    config_file = os.path.join(tree_path, "connection_info.txt")
    with open(config_file, "w") as f:
        f.write(f"""host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = separate
database_name = {tree_name}
""")
    
    try:
        # Create database instance
        print(f"Creating database {tree_name}...")
        db = PostgreSQLEnhanced()
        db.load(tree_path, callback=None, mode="w")
        
        # Add a person
        print("Adding test person...")
        with DbTxn("Add person", db) as trans:
            person = Person()
            person.set_handle("TEST001")
            person.set_gramps_id("I0001")
            person.set_gender(Person.MALE)
            
            name = Name()
            name.set_first_name("Test")
            surname = Surname()
            surname.set_surname("Person")
            name.add_surname(surname)
            person.set_primary_name(name)
            
            db.add_person(person, trans)
            print(f"  Added person with handle: {person.get_handle()}")
        
        # Try to retrieve immediately
        print("\nRetrieving person immediately...")
        retrieved = db.get_person_from_handle("TEST001")
        if retrieved:
            print(f"  ✓ Found person: {retrieved.get_handle()}")
        else:
            print("  ✗ Person not found!")
        
        # Check handles
        print("\nChecking person handles...")
        handles = list(db.get_person_handles())
        print(f"  Found {len(handles)} handles: {handles}")
        
        # Direct SQL check
        print("\nDirect SQL check...")
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=tree_name
        )
        
        with conn.cursor() as cur:
            cur.execute("SELECT handle FROM person")
            rows = cur.fetchall()
            print(f"  Found {len(rows)} rows in person table")
            for row in rows:
                print(f"    - {row[0]}")
        
        conn.close()
        db.close()
        
        # Clean up
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
            autocommit=True
        )
        with admin_conn.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(tree_name)))
        admin_conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up temp dir
    import shutil
    shutil.rmtree(temp_dir)

def test_monolithic_mode():
    """Test data persistence in monolithic mode."""
    print("\n\n=== Testing Monolithic Mode Data Persistence ===")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_mono_")
    tree_name = "test_mono_tree"
    tree_path = os.path.join(temp_dir, tree_name)
    os.makedirs(tree_path, exist_ok=True)
    
    # Create config
    config_file = os.path.join(tree_path, "connection_info.txt")
    with open(config_file, "w") as f:
        f.write(f"""host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = monolithic
shared_database_name = gramps_monolithic_test
""")
    
    try:
        # Create database instance
        print(f"Creating tree {tree_name} in monolithic mode...")
        db = PostgreSQLEnhanced()
        db.load(tree_path, callback=None, mode="w")
        
        # Check table prefix
        print(f"Table prefix: {db.table_prefix}")
        
        # Add a person
        print("Adding test person...")
        with DbTxn("Add person", db) as trans:
            person = Person()
            person.set_handle("MONO001")
            person.set_gramps_id("I0001")
            person.set_gender(Person.MALE)
            
            name = Name()
            name.set_first_name("Mono")
            surname = Surname()
            surname.set_surname("Test")
            name.add_surname(surname)
            person.set_primary_name(name)
            
            db.add_person(person, trans)
            print(f"  Added person with handle: {person.get_handle()}")
        
        # Try to retrieve immediately
        print("\nRetrieving person immediately...")
        retrieved = db.get_person_from_handle("MONO001")
        if retrieved:
            print(f"  ✓ Found person: {retrieved.get_handle()}")
        else:
            print("  ✗ Person not found!")
        
        # Check handles
        print("\nChecking person handles...")
        handles = list(db.get_person_handles())
        print(f"  Found {len(handles)} handles: {handles}")
        
        # Direct SQL check
        print("\nDirect SQL check...")
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="gramps_monolithic_test"
        )
        
        with conn.cursor() as cur:
            # Check prefixed table
            table_name = f"{db.table_prefix}person"
            print(f"  Checking table: {table_name}")
            cur.execute(sql.SQL("SELECT handle FROM {}").format(sql.Identifier(table_name)))
            rows = cur.fetchall()
            print(f"  Found {len(rows)} rows in {table_name} table")
            for row in rows:
                print(f"    - {row[0]}")
        
        conn.close()
        db.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up temp dir
    import shutil
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_separate_mode()
    test_monolithic_mode()