#!/usr/bin/env python3
"""
Trace transaction calls to understand what's happening.
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

# Monkey-patch to trace calls
original_transaction_begin = None
original_transaction_commit = None

def trace_transaction_begin(self, transaction):
    print(f"*** TRACE: transaction_begin called on {type(self).__name__}")
    print(f"    Transaction: {transaction}")
    print(f"    Has dbapi: {hasattr(self, 'dbapi')}")
    if hasattr(self, 'dbapi'):
        print(f"    dbapi type: {type(self.dbapi)}")
    if original_transaction_begin:
        return original_transaction_begin(self, transaction)
    return transaction

def trace_transaction_commit(self, transaction):
    print(f"*** TRACE: transaction_commit called on {type(self).__name__}")
    print(f"    Transaction: {transaction}")
    print(f"    Has dbapi: {hasattr(self, 'dbapi')}")
    if hasattr(self, 'dbapi'):
        print(f"    dbapi type: {type(self.dbapi)}")
        print(f"    dbapi.commit exists: {hasattr(self.dbapi, 'commit')}")
        
        # Try to actually call commit
        if hasattr(self.dbapi, 'commit'):
            print("    Calling dbapi.commit()...")
            self.dbapi.commit()
            print("    dbapi.commit() called successfully")
    
    if original_transaction_commit:
        return original_transaction_commit(self, transaction)

from postgresqlenhanced import PostgreSQLEnhanced

# Apply monkey-patch
if hasattr(PostgreSQLEnhanced, 'transaction_begin'):
    original_transaction_begin = PostgreSQLEnhanced.transaction_begin
    PostgreSQLEnhanced.transaction_begin = trace_transaction_begin

if hasattr(PostgreSQLEnhanced, 'transaction_commit'):
    original_transaction_commit = PostgreSQLEnhanced.transaction_commit
    PostgreSQLEnhanced.transaction_commit = trace_transaction_commit

from gramps.gen.db import DbTxn
from gramps.gen.lib import Person, Name, Surname

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
    "shared_database": "gramps_trace_test",
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

def test_with_tracing():
    """Test with transaction tracing enabled."""
    
    print("\n=== Transaction Trace Test ===")
    
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
    temp_dir = tempfile.mkdtemp(prefix="gramps_trace_")
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
    
    print("\n=== Creating transaction with DbTxn ===")
    person = create_test_person("TEST001", "I0001", "John", "Smith")
    
    print("\nEntering DbTxn context...")
    with DbTxn("Test Transaction", db) as trans:
        print("\nInside DbTxn context")
        print(f"Transaction type: {type(trans)}")
        
        print("\nAdding person...")
        db.add_person(person, trans)
        print("Person added")
        
    print("\nExited DbTxn context")
    
    # Check if data persisted
    print("\n=== Checking if data persisted ===")
    
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
        print(f"Direct SQL count: {count}")
        
        if count > 0:
            print("✓ Data persisted successfully!")
        else:
            print("✗ Data did NOT persist")
    
    check_conn.close()
    
    # Cleanup
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
    
    admin_conn.close()
    
    return count > 0

if __name__ == "__main__":
    success = test_with_tracing()
    sys.exit(0 if success else 1)