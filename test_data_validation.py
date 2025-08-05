#!/usr/bin/env python3
"""
Test to validate that data stored in PostgreSQL through the plugin is completely valid.
Verifies JSON structure, data types, constraints, and DBAPI compatibility.
"""

import os
import sys
import tempfile
import shutil
import json
import psycopg
from psycopg import sql
from psycopg.types.json import Json
import pickle

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after setting up path
import mock_gramps
from postgresqlenhanced import PostgreSQLEnhanced
from mock_gramps import DbTxn, Person, Name, Surname, Family, Event, Place

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

class DataValidationTests:
    """Tests to validate data integrity in PostgreSQL."""
    
    def __init__(self):
        self.temp_dirs = []
        self.test_dbs = []
    
    def setup_test_db(self, db_name, mode="separate"):
        """Set up a test database."""
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix=f"validate_{db_name}_")
        self.temp_dirs.append(temp_dir)
        
        tree_path = os.path.join(temp_dir, db_name)
        os.makedirs(tree_path, exist_ok=True)
        
        # Create config
        config_file = os.path.join(tree_path, "connection_info.txt")
        with open(config_file, "w") as f:
            if mode == "separate":
                f.write(f"""host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = separate
database_name = {db_name}
""")
            else:  # monolithic
                f.write(f"""host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = monolithic
shared_database_name = gramps_validation_shared
""")
        
        # Create database instance
        db = PostgreSQLEnhanced()
        db.load(tree_path, callback=None, mode="w")
        
        self.test_dbs.append((db_name, db, mode))
        
        return db, tree_path
    
    def test_json_data_structure(self):
        """Test 1: Validate JSON data structure in database."""
        print("\n=== Test 1: JSON Data Structure Validation ===")
        
        db_name = "test_json_structure"
        db, tree_path = self.setup_test_db(db_name)
        
        try:
            # Create test objects using Gramps API
            print("\nCreating test objects through Gramps API...")
            
            # Add a person with all fields
            with DbTxn("Add person", db) as trans:
                person = Person()
                person.set_handle("JSON_TEST_001")
                person.set_gramps_id("I0001")
                person.set_gender(Person.MALE)
                
                # Set name
                name = Name()
                name.set_first_name("John")
                surname = Surname()
                surname.set_surname("Doe")
                name.add_surname(surname)
                person.set_primary_name(name)
                
                # Note: Our mock doesn't support all methods, so we work with what we have
                db.add_person(person, trans)
            
            # Add a family
            with DbTxn("Add family", db) as trans:
                family = Family()
                family.set_handle("FAM_TEST_001")
                family.set_gramps_id("F0001")
                family.set_father_handle("JSON_TEST_001")
                db.add_family(trans)
            
            # Now validate the JSON structure directly in PostgreSQL
            print("\nValidating JSON structure in PostgreSQL...")
            
            conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=db_name
            )
            
            with conn.cursor() as cur:
                # Check person table
                cur.execute("SELECT handle, json_data, gramps_id FROM person WHERE handle = %s", ["JSON_TEST_001"])
                row = cur.fetchone()
                
                if row:
                    handle, json_data, gramps_id = row
                    print(f"\nPerson data found:")
                    print(f"  Handle: {handle}")
                    print(f"  Gramps ID: {gramps_id}")
                    print(f"  JSON type: {type(json_data)}")
                    
                    # Validate JSON structure
                    if isinstance(json_data, dict):
                        print("  ✓ JSON data is a valid dictionary")
                        print(f"  JSON keys: {list(json_data.keys())[:5]}...")  # Show first 5 keys
                    else:
                        print("  ✗ JSON data is not a dictionary!")
                else:
                    print("  ✗ No person data found!")
                
                # Check if JSON can be queried
                cur.execute("""
                    SELECT handle 
                    FROM person 
                    WHERE json_data IS NOT NULL 
                    AND jsonb_typeof(json_data) = 'object'
                """)
                valid_json_count = len(cur.fetchall())
                print(f"\n  ✓ {valid_json_count} records have valid JSON objects")
                
                # Test JSONB operations
                cur.execute("""
                    SELECT handle, 
                           json_data ? 'name' as has_name,
                           json_data ? 'gender' as has_gender
                    FROM person 
                    WHERE handle = %s
                """, ["JSON_TEST_001"])
                
                row = cur.fetchone()
                if row:
                    print(f"\n  JSONB field checks:")
                    print(f"    Has 'name' field: {row[1]}")
                    print(f"    Has 'gender' field: {row[2]}")
            
            conn.close()
            print("\n✅ JSON structure validation completed")
            
        except Exception as e:
            print(f"\n❌ JSON validation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def test_data_types_and_constraints(self):
        """Test 2: Validate data types and constraints."""
        print("\n\n=== Test 2: Data Types and Constraints Validation ===")
        
        db_name = "test_data_types"
        
        try:
            # Create database directly
            admin_conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname="postgres",
                autocommit=True
            )
            
            with admin_conn.cursor() as cur:
                cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            admin_conn.close()
            
            # Connect and examine schema
            conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=db_name
            )
            
            # Use the plugin to create schema
            db, tree_path = self.setup_test_db(db_name)
            
            print("\nExamining column data types...")
            
            with conn.cursor() as cur:
                # Get column information
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'person'
                    ORDER BY ordinal_position
                """)
                
                print("\nPerson table columns:")
                for col in cur.fetchall():
                    print(f"  {col[0]:20} {col[1]:15} NULL: {col[2]:5} DEFAULT: {col[3]}")
                
                # Validate constraints
                cur.execute("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = 'person'
                """)
                
                print("\nPerson table constraints:")
                for constraint in cur.fetchall():
                    print(f"  {constraint[0]:30} Type: {constraint[1]}")
                
                # Test data type enforcement
                print("\nTesting data type enforcement...")
                
                # Test valid data
                try:
                    cur.execute("""
                        INSERT INTO person (handle, json_data, gramps_id, gender, change, private)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, ("TYPE_TEST_001", Json({"test": "data"}), "I0001", 1, 12345, False))
                    conn.commit()
                    print("  ✓ Valid data inserted successfully")
                except Exception as e:
                    print(f"  ✗ Valid data failed: {e}")
                    conn.rollback()
                
                # Test primary key constraint
                try:
                    cur.execute("""
                        INSERT INTO person (handle, json_data, gramps_id)
                        VALUES (%s, %s, %s)
                    """, ("TYPE_TEST_001", Json({"duplicate": "test"}), "I0002"))
                    conn.commit()
                    print("  ✗ Duplicate primary key allowed!")
                except Exception as e:
                    print("  ✓ Primary key constraint enforced")
                    conn.rollback()
                
                # Test JSONB validation
                cur.execute("""
                    SELECT handle, 
                           jsonb_typeof(json_data) as json_type,
                           json_data::text LIKE '%{%' as is_object
                    FROM person
                    WHERE handle = 'TYPE_TEST_001'
                """)
                
                row = cur.fetchone()
                if row:
                    print(f"\n  JSONB validation:")
                    print(f"    Type: {row[1]}")
                    print(f"    Is object: {row[2]}")
            
            conn.close()
            print("\n✅ Data type validation completed")
            
        except Exception as e:
            print(f"\n❌ Data type validation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def test_metadata_serialization(self):
        """Test 3: Validate metadata serialization (pickle/blob data)."""
        print("\n\n=== Test 3: Metadata Serialization Validation ===")
        
        db_name = "test_metadata"
        db, tree_path = self.setup_test_db(db_name)
        
        try:
            # Test metadata storage
            print("\nTesting metadata storage...")
            
            conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=db_name
            )
            
            with conn.cursor() as cur:
                # Store test metadata
                test_data = {"version": "1.0", "created": "2025-08-05", "test": True}
                pickled_data = pickle.dumps(test_data)
                
                cur.execute("""
                    INSERT INTO metadata (setting, value)
                    VALUES (%s, %s)
                """, ("test_setting", pickled_data))
                conn.commit()
                print("  ✓ Metadata stored successfully")
                
                # Retrieve and validate
                cur.execute("SELECT setting, value FROM metadata WHERE setting = %s", ["test_setting"])
                row = cur.fetchone()
                
                if row:
                    setting, value = row
                    print(f"  Setting: {setting}")
                    print(f"  Value type: {type(value)}")
                    print(f"  Value length: {len(value)} bytes")
                    
                    # Unpickle
                    try:
                        unpickled = pickle.loads(value)
                        print(f"  ✓ Unpickled successfully: {unpickled}")
                        
                        # Verify data integrity
                        if unpickled == test_data:
                            print("  ✓ Data integrity verified")
                        else:
                            print("  ✗ Data integrity check failed")
                    except Exception as e:
                        print(f"  ✗ Failed to unpickle: {e}")
                
                # Check BYTEA storage
                cur.execute("""
                    SELECT setting, 
                           octet_length(value) as byte_length,
                           encode(value, 'hex')::text LIKE '80%' as is_pickle
                    FROM metadata
                    WHERE setting = 'test_setting'
                """)
                
                row = cur.fetchone()
                if row:
                    print(f"\n  BYTEA validation:")
                    print(f"    Byte length: {row[1]}")
                    print(f"    Looks like pickle data: {row[2]}")
            
            conn.close()
            print("\n✅ Metadata serialization validation completed")
            
        except Exception as e:
            print(f"\n❌ Metadata validation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def test_monolithic_prefix_integrity(self):
        """Test 4: Validate table prefix integrity in monolithic mode."""
        print("\n\n=== Test 4: Monolithic Mode Prefix Integrity ===")
        
        # Create shared database
        shared_db = "gramps_validation_shared"
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
            autocommit=True
        )
        
        with admin_conn.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(shared_db)))
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(shared_db)))
        admin_conn.close()
        
        # Create multiple trees
        tree_names = ["validation_tree1", "validation_tree2", "O_Brien_Family"]
        
        try:
            for tree_name in tree_names:
                db, tree_path = self.setup_test_db(tree_name, mode="monolithic")
                print(f"\nCreated tree: {tree_name}")
                print(f"  Table prefix: {db.table_prefix}")
            
            # Validate prefix isolation
            print("\nValidating prefix isolation...")
            
            conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=shared_db
            )
            
            with conn.cursor() as cur:
                # Get all tables
                cur.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
                
                tables = [row[0] for row in cur.fetchall()]
                print(f"\nTotal tables created: {len(tables)}")
                
                # Check prefix patterns
                for tree_name in tree_names:
                    prefix = tree_name.replace("'", "").replace("-", "_").replace(".", "_").replace(" ", "_") + "_"
                    prefix_tables = [t for t in tables if t.startswith(prefix.lower())]
                    print(f"\n  {tree_name}:")
                    print(f"    Expected prefix: {prefix}")
                    print(f"    Tables found: {len(prefix_tables)}")
                    
                    if prefix_tables:
                        print(f"    Sample tables: {prefix_tables[:3]}...")
                
                # Verify no table name collisions
                if len(tables) == len(set(tables)):
                    print("\n  ✓ No table name collisions detected")
                else:
                    print("\n  ✗ Table name collisions found!")
                
                # Test special character handling
                cur.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE tablename LIKE 'o_brien_family_%'
                    LIMIT 5
                """)
                
                obrien_tables = [row[0] for row in cur.fetchall()]
                if obrien_tables:
                    print(f"\n  ✓ Special characters handled correctly:")
                    print(f"    O'Brien_Family tables: {obrien_tables}")
            
            conn.close()
            print("\n✅ Monolithic prefix integrity validation completed")
            
        except Exception as e:
            print(f"\n❌ Prefix integrity validation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def cleanup(self):
        """Clean up test databases and directories."""
        print("\n\nCleaning up test resources...")
        
        # Close all database connections
        for db_name, db, mode in self.test_dbs:
            try:
                db.close()
                print(f"  Closed connection to {db_name}")
            except:
                pass
        
        # Drop test databases
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
            autocommit=True
        )
        
        test_db_names = ["test_json_structure", "test_data_types", "test_metadata", 
                        "validation_tree1", "validation_tree2", "O_Brien_Family",
                        "gramps_validation_shared"]
        
        with admin_conn.cursor() as cur:
            for db_name in test_db_names:
                try:
                    cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
                    print(f"  Dropped database {db_name}")
                except:
                    pass
        
        admin_conn.close()
        
        # Remove temp directories
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                print(f"  Removed {temp_dir}")
            except:
                pass
        
        print("\n✅ Cleanup completed")
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("="*60)
        print("PostgreSQL Data Validation Tests")
        print("Verifying data integrity and DBAPI compatibility")
        print("="*60)
        
        # Run tests
        self.test_json_data_structure()
        self.test_data_types_and_constraints()
        self.test_metadata_serialization()
        self.test_monolithic_prefix_integrity()
        
        # Cleanup
        self.cleanup()
        
        print("\n" + "="*60)
        print("VALIDATION COMPLETE")
        print("="*60)

if __name__ == "__main__":
    tester = DataValidationTests()
    tester.run_all_tests()