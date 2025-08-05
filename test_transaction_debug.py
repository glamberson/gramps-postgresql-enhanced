#!/usr/bin/env python3
"""
Debug transaction handling step by step.
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
from gramps.gen.db import DbTxn
from gramps.gen.lib import Person, Name, Surname

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
    "shared_database": "gramps_txn_debug",
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

def test_transaction_flow():
    """Debug transaction flow step by step."""
    
    print("\n=== Transaction Debug Test ===")
    
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
    temp_dir = tempfile.mkdtemp(prefix="gramps_txn_")
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
    
    print("\n1. Checking transaction methods on db:")
    print(f"   - has transaction_begin: {hasattr(db, 'transaction_begin')}")
    print(f"   - has transaction_commit: {hasattr(db, 'transaction_commit')}")
    print(f"   - has transaction_abort: {hasattr(db, 'transaction_abort')}")
    
    # Try to call them anyway
    if not hasattr(db, 'transaction_begin'):
        print("   - Checking parent class methods...")
        # Check if it's inherited but not showing in hasattr
        try:
            method = getattr(type(db), 'transaction_begin', None)
            if method:
                print(f"     Found transaction_begin in class: {method}")
        except:
            pass
    
    print("\n2. Checking dbapi methods:")
    print(f"   - dbapi type: {type(db.dbapi)}")
    print(f"   - has commit: {hasattr(db.dbapi, 'commit')}")
    print(f"   - has _commit: {hasattr(db.dbapi, '_commit')}")
    print(f"   - has begin: {hasattr(db.dbapi, 'begin')}")
    
    # Check if dbapi is wrapped
    if hasattr(db.dbapi, '_connection'):
        print(f"   - dbapi is wrapped, _connection type: {type(db.dbapi._connection)}")
    
    print("\n3. Creating DbTxn and checking its type:")
    person = create_test_person("TEST001", "I0001", "John", "Smith")
    
    with DbTxn("Test Transaction", db) as trans:
        print(f"   - trans type: {type(trans)}")
        print(f"   - trans.db == db: {trans.db == db}")
        print(f"   - trans.msg: {trans.msg}")
        
        print("\n4. Adding person in transaction:")
        db.add_person(person, trans)
        print("   - Person added")
        
        # Check if data is visible within transaction
        people_in_txn = list(db.iter_people())
        print(f"   - People visible in transaction: {len(people_in_txn)}")
        
    print("\n5. After transaction exit:")
    
    # Check via db API
    people_after = list(db.iter_people())
    print(f"   - People via db API: {len(people_after)}")
    
    # Direct SQL check
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
        print(f"   - Direct SQL count: {count}")
        
        if count > 0:
            cur.execute("SELECT handle, json_data->>'gramps_id' FROM test_tree_person")
            for row in cur.fetchall():
                print(f"     Found: handle={row[0]}, gramps_id={row[1]}")
    
    check_conn.close()
    
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
    success = test_transaction_flow()
    if success:
        print("\n✓ Transaction handling works!")
    else:
        print("\n✗ Transaction handling FAILED")
    sys.exit(0 if success else 1)