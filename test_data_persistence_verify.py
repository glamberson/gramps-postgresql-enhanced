#!/usr/bin/env python3
"""
Verify that data actually persists to PostgreSQL database.
This test keeps the database for manual verification.
"""

import os
import sys
import tempfile
import psycopg
from psycopg import sql

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mock_gramps
from postgresqlenhanced import PostgreSQLEnhanced
from mock_gramps import DbTxn, Person, Name, Surname

DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
    "database": "gramps_persistence_test",
}

def create_test_person(handle, gramps_id, first_name, surname):
    """Create a test person."""
    person = Person()
    person.set_handle(handle)
    person.set_gramps_id(gramps_id)
    person.set_gender(Person.MALE)
    
    name = Name()
    name.set_first_name(first_name)
    surname_obj = Surname()
    surname_obj.set_surname(surname)
    name.add_surname(surname_obj)
    person.set_primary_name(name)
    
    return person

def main():
    print("=" * 60)
    print("DATA PERSISTENCE VERIFICATION TEST")
    print("=" * 60)
    
    # Create database
    try:
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
            autocommit=True
        )
        
        with conn.cursor() as cur:
            # Drop if exists
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
                sql.Identifier(DB_CONFIG["database"])
            ))
            # Create fresh
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(DB_CONFIG["database"]),
                sql.Identifier(DB_CONFIG["user"])
            ))
        conn.close()
        print(f"✓ Created database: {DB_CONFIG['database']}")
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        return 1
    
    # Create temp directory for tree
    with tempfile.TemporaryDirectory() as tmpdir:
        tree_dir = os.path.join(tmpdir, "test_tree")
        os.makedirs(tree_dir)
        
        # Create connection config (note: filename should be connection_info.txt)
        config_path = os.path.join(tree_dir, "connection_info.txt")
        with open(config_path, "w") as f:
            f.write(f"host = {DB_CONFIG['host']}\n")
            f.write(f"port = {DB_CONFIG['port']}\n")
            f.write(f"user = {DB_CONFIG['user']}\n")
            f.write(f"password = {DB_CONFIG['password']}\n")
            f.write("database_mode = monolithic\n")
            f.write(f"shared_database_name = {DB_CONFIG['database']}\n")
        
        # Initialize database
        db = PostgreSQLEnhanced()
        db.load(tree_dir, None)
        print("✓ Database initialized")
        
        # Add test people
        print("\nAdding test people...")
        with DbTxn("Add test people", db) as trans:
            for i in range(5):
                person = create_test_person(
                    f"HANDLE{i:03d}",
                    f"I{i:04d}",
                    f"TestName{i}",
                    f"TestSurname{i}"
                )
                db.add_person(person, trans)
                print(f"  Added: {person.get_gramps_id()}")
        
        # Verify data through Gramps API
        count = db.get_number_of_people()
        print(f"\n✓ Gramps API reports {count} people in database")
        
        # Verify directly through SQL
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"]
        )
        
        with conn.cursor() as cur:
            # Check person table
            cur.execute("SELECT COUNT(*) FROM test_tree_person")
            sql_count = cur.fetchone()[0]
            print(f"✓ SQL query reports {sql_count} people in test_tree_person table")
            
            # Show some data
            cur.execute("""
                SELECT handle, json_data->>'gramps_id', 
                       json_data->'primary_name'->>'first_name'
                FROM test_tree_person 
                LIMIT 3
            """)
            print("\nSample data from database:")
            for row in cur.fetchall():
                print(f"  Handle: {row[0]}, ID: {row[1]}, Name: {row[2]}")
        
        conn.close()
        db.close()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED - Database kept for inspection")
    print(f"Database: {DB_CONFIG['database']}")
    print("To inspect manually:")
    print(f"  PGPASSWORD='{DB_CONFIG['password']}' psql -h {DB_CONFIG['host']} \\")
    print(f"    -U {DB_CONFIG['user']} -d {DB_CONFIG['database']}")
    print("  Then run: SELECT * FROM test_tree_person;")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())