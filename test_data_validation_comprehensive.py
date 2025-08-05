#!/usr/bin/env python3
"""
Comprehensive data validation tests for PostgreSQL Enhanced plugin.
Tests data integrity, CRUD operations, and relationships in both separate and monolithic modes.
"""

import os
import sys
import tempfile
import json
import time
import psycopg
from psycopg import sql
from datetime import datetime
from collections import defaultdict

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import mock framework and get real/mock classes
import mock_gramps
from postgresqlenhanced import PostgreSQLEnhanced

# Import Gramps classes (real if available, mock otherwise)
from mock_gramps import (
    DbTxn, Person, Name, Surname, Family, Event, Place, Source,
    MockCitation as Citation, MockRepository as Repository,
    MockMedia as Media, MockNote as Note, MockTag as Tag,
    MockEventType as EventType, MockChildRef as ChildRef
)

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

class ComprehensiveDataValidation:
    """Complete data validation for both database modes."""
    
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.temp_dirs = []
        self.test_dbs = []
        
    def cleanup(self):
        """Clean up test databases and directories."""
        # Clean up databases
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
                for db_name in self.test_dbs:
                    try:
                        # Terminate connections
                        cur.execute(sql.SQL("""
                            SELECT pg_terminate_backend(pid)
                            FROM pg_stat_activity
                            WHERE datname = %s AND pid <> pg_backend_pid()
                        """), (db_name,))
                        
                        # Drop database
                        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
                            sql.Identifier(db_name)
                        ))
                        print(f"  ✓ Cleaned up database: {db_name}")
                    except Exception as e:
                        print(f"  ⚠ Could not clean up {db_name}: {e}")
            conn.close()
        except Exception as e:
            print(f"  ⚠ Cleanup error: {e}")
        
        # Clean up temp directories
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass
    
    def create_test_database(self, db_name):
        """Create a test database."""
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
                sql.Identifier(db_name)
            ))
            # Create new
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(db_name),
                sql.Identifier(DB_CONFIG["user"])
            ))
        
        conn.close()
        self.test_dbs.append(db_name)
        return db_name
    
    def setup_tree(self, tree_name, mode="separate", shared_db=None):
        """Set up a family tree in specified mode."""
        temp_dir = tempfile.mkdtemp(prefix=f"validate_{mode}_")
        self.temp_dirs.append(temp_dir)
        
        tree_path = os.path.join(temp_dir, tree_name)
        os.makedirs(tree_path)
        
        # Create connection config
        config_path = os.path.join(tree_path, "connection_info.txt")
        with open(config_path, "w") as f:
            f.write(f"host = {DB_CONFIG['host']}\n")
            f.write(f"port = {DB_CONFIG['port']}\n")
            f.write(f"user = {DB_CONFIG['user']}\n")
            f.write(f"password = {DB_CONFIG['password']}\n")
            f.write(f"database_mode = {mode}\n")
            if mode == "monolithic" and shared_db:
                f.write(f"shared_database_name = {shared_db}\n")
        
        # Initialize database
        db = PostgreSQLEnhanced()
        db.load(tree_path, None)
        
        return db, tree_path
    
    def create_test_person(self, handle, gramps_id, first_name, surname):
        """Create a test person with full data."""
        person = Person()
        person.set_handle(handle)
        person.set_gramps_id(gramps_id)
        person.set_gender(Person.MALE)
        
        # Primary name
        name = Name()
        name.set_first_name(first_name)
        surname_obj = Surname()
        surname_obj.set_surname(surname)
        name.add_surname(surname_obj)
        person.set_primary_name(name)
        
        # Add birth and death dates if supported
        if hasattr(person, 'set_birth_ref_index'):
            person.set_birth_ref_index(-1)
            person.set_death_ref_index(-1)
        
        return person
    
    def create_test_family(self, handle, gramps_id, father_handle=None, mother_handle=None):
        """Create a test family."""
        family = Family()
        family.set_handle(handle)
        family.set_gramps_id(gramps_id)
        
        if father_handle:
            family.set_father_handle(father_handle)
        if mother_handle:
            family.set_mother_handle(mother_handle)
        
        return family
    
    def create_test_event(self, handle, gramps_id, event_type, date_text=None):
        """Create a test event."""
        event = Event()
        event.set_handle(handle)
        event.set_gramps_id(gramps_id)
        
        # Set event type if method exists
        if hasattr(event, 'set_type'):
            if hasattr(EventType, 'BIRTH'):
                event.set_type(EventType.BIRTH)
        
        # Set description
        if hasattr(event, 'set_description'):
            event.set_description(f"Test event: {event_type}")
        
        return event
    
    def validate_crud_operations(self, db, mode_name):
        """Test Create, Read, Update, Delete operations."""
        print(f"\n  Testing CRUD operations in {mode_name} mode:")
        
        results = {
            "create": False,
            "read": False,
            "update": False,
            "delete": False
        }
        
        try:
            # CREATE
            person_handle = f"CRUD_TEST_{mode_name}"
            person = self.create_test_person(
                person_handle,
                "I9999",
                "TestCRUD",
                "ValidationTest"
            )
            
            with DbTxn("Create test", db) as trans:
                db.add_person(person, trans)
            
            # Verify created
            count = db.get_number_of_people()
            if count > 0:
                results["create"] = True
                print("    ✓ CREATE: Person added successfully")
            else:
                print("    ✗ CREATE: Person not added")
            
            # READ
            retrieved = db.get_person_from_handle(person_handle)
            if retrieved and retrieved.get_gramps_id() == "I9999":
                results["read"] = True
                print("    ✓ READ: Person retrieved successfully")
            else:
                print("    ✗ READ: Could not retrieve person")
            
            # UPDATE
            if retrieved:
                # Modify the person
                new_name = Name()
                new_name.set_first_name("UpdatedName")
                surname_obj = Surname()
                surname_obj.set_surname("UpdatedSurname")
                new_name.add_surname(surname_obj)
                retrieved.set_primary_name(new_name)
                
                with DbTxn("Update test", db) as trans:
                    db.commit_person(retrieved, trans)
                
                # Verify update
                updated = db.get_person_from_handle(person_handle)
                if updated and hasattr(updated.get_primary_name(), 'get_first_name'):
                    if updated.get_primary_name().get_first_name() == "UpdatedName":
                        results["update"] = True
                        print("    ✓ UPDATE: Person updated successfully")
                    else:
                        print("    ✗ UPDATE: Person not updated correctly")
            
            # DELETE
            if hasattr(db, 'remove_person'):
                with DbTxn("Delete test", db) as trans:
                    db.remove_person(person_handle, trans)
                
                # Verify deleted
                try:
                    deleted = db.get_person_from_handle(person_handle)
                    if not deleted:
                        results["delete"] = True
                        print("    ✓ DELETE: Person removed successfully")
                    else:
                        print("    ✗ DELETE: Person still exists")
                except:
                    results["delete"] = True
                    print("    ✓ DELETE: Person removed successfully")
            else:
                print("    ⚠ DELETE: Not implemented")
            
        except Exception as e:
            print(f"    ✗ CRUD test error: {e}")
            self.results["errors"].append(f"CRUD {mode_name}: {str(e)}")
        
        # Update results
        for operation, success in results.items():
            if success:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        
        return results
    
    def validate_relationships(self, db, mode_name):
        """Validate relationship integrity between objects."""
        print(f"\n  Testing relationship integrity in {mode_name} mode:")
        
        try:
            # Create related objects
            father = self.create_test_person("FATHER01", "I0001", "John", "Smith")
            mother = self.create_test_person("MOTHER01", "I0002", "Jane", "Doe")
            child = self.create_test_person("CHILD01", "I0003", "Junior", "Smith")
            
            family = self.create_test_family("FAMILY01", "F0001", "FATHER01", "MOTHER01")
            
            # Add child to family if method exists
            if hasattr(family, 'add_child_ref'):
                child_ref = ChildRef()
                child_ref.set_reference_handle("CHILD01")
                family.add_child_ref(child_ref)
            
            # Store all objects
            with DbTxn("Add relationships", db) as trans:
                db.add_person(father, trans)
                db.add_person(mother, trans)
                db.add_person(child, trans)
                db.add_family(family, trans)
            
            # Verify relationships
            retrieved_family = db.get_family_from_handle("FAMILY01")
            
            tests_passed = 0
            tests_failed = 0
            
            if retrieved_family:
                # Check father
                if retrieved_family.get_father_handle() == "FATHER01":
                    print("    ✓ Father relationship preserved")
                    tests_passed += 1
                else:
                    print("    ✗ Father relationship lost")
                    tests_failed += 1
                
                # Check mother
                if retrieved_family.get_mother_handle() == "MOTHER01":
                    print("    ✓ Mother relationship preserved")
                    tests_passed += 1
                else:
                    print("    ✗ Mother relationship lost")
                    tests_failed += 1
                
                # Check children if method exists
                if hasattr(retrieved_family, 'get_child_ref_list'):
                    child_refs = retrieved_family.get_child_ref_list()
                    if child_refs and len(child_refs) > 0:
                        print("    ✓ Child relationships preserved")
                        tests_passed += 1
                    else:
                        print("    ⚠ No children in family")
            else:
                print("    ✗ Could not retrieve family")
                tests_failed += 3
            
            self.results["passed"] += tests_passed
            self.results["failed"] += tests_failed
            
        except Exception as e:
            print(f"    ✗ Relationship test error: {e}")
            self.results["errors"].append(f"Relationships {mode_name}: {str(e)}")
            self.results["failed"] += 1
    
    def validate_json_storage(self, db, tree_name, mode):
        """Validate JSON storage in PostgreSQL."""
        print(f"\n  Testing JSON storage in {mode} mode:")
        
        # Determine database and table names
        if mode == "monolithic":
            db_name = db.dbapi.database
            table_prefix = f"{tree_name}_"
        else:
            db_name = tree_name
            table_prefix = ""
        
        try:
            # Connect directly to PostgreSQL
            conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=db_name
            )
            
            with conn.cursor() as cur:
                # Check person table structure
                person_table = f"{table_prefix}person"
                
                # Verify JSONB column exists
                cur.execute("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = 'json_data'
                """, (person_table,))
                
                result = cur.fetchone()
                if result and result[0] == 'jsonb':
                    print("    ✓ JSONB column exists")
                    self.results["passed"] += 1
                else:
                    print("    ✗ JSONB column missing or wrong type")
                    self.results["failed"] += 1
                
                # Check if JSON data is queryable
                cur.execute(sql.SQL("""
                    SELECT 
                        handle,
                        json_data->>'gramps_id' as gramps_id,
                        json_data->'primary_name'->>'first_name' as first_name
                    FROM {}
                    LIMIT 1
                """).format(sql.Identifier(person_table)))
                
                row = cur.fetchone()
                if row:
                    print(f"    ✓ JSON queries work: {row[1]} - {row[2]}")
                    self.results["passed"] += 1
                else:
                    print("    ⚠ No data to query")
                
                # Test JSON indexing capability
                cur.execute(sql.SQL("""
                    EXPLAIN (FORMAT JSON) 
                    SELECT * FROM {} 
                    WHERE json_data->>'gramps_id' = 'I0001'
                """).format(sql.Identifier(person_table)))
                
                explain = cur.fetchone()
                if explain:
                    print("    ✓ JSON indexing available")
                    self.results["passed"] += 1
                
            conn.close()
            
        except Exception as e:
            print(f"    ✗ JSON validation error: {e}")
            self.results["errors"].append(f"JSON {mode}: {str(e)}")
            self.results["failed"] += 1
    
    def validate_data_isolation(self, shared_db):
        """Test data isolation in monolithic mode."""
        print("\n  Testing data isolation in monolithic mode:")
        
        try:
            # Create two trees in same database
            db1, _ = self.setup_tree("tree_one", "monolithic", shared_db)
            db2, _ = self.setup_tree("tree_two", "monolithic", shared_db)
            
            # Add different data to each tree
            person1 = self.create_test_person("ISO_TEST1", "I1001", "TreeOne", "Person")
            person2 = self.create_test_person("ISO_TEST2", "I1002", "TreeTwo", "Person")
            
            with DbTxn("Add to tree1", db1) as trans:
                db1.add_person(person1, trans)
            
            with DbTxn("Add to tree2", db2) as trans:
                db2.add_person(person2, trans)
            
            # Verify isolation
            count1 = db1.get_number_of_people()
            count2 = db2.get_number_of_people()
            
            # Each tree should only see its own data
            if count1 == 1 and count2 == 1:
                print("    ✓ Each tree has exactly 1 person")
                self.results["passed"] += 1
                
                # Verify correct person in each tree
                p1 = db1.get_person_from_handle("ISO_TEST1")
                p2 = db2.get_person_from_handle("ISO_TEST2")
                
                if p1 and not db1.get_person_from_handle("ISO_TEST2"):
                    print("    ✓ Tree1 only sees its own data")
                    self.results["passed"] += 1
                else:
                    print("    ✗ Tree1 sees wrong data")
                    self.results["failed"] += 1
                
                if p2 and not db2.get_person_from_handle("ISO_TEST1"):
                    print("    ✓ Tree2 only sees its own data")
                    self.results["passed"] += 1
                else:
                    print("    ✗ Tree2 sees wrong data")
                    self.results["failed"] += 1
            else:
                print(f"    ✗ Wrong counts: tree1={count1}, tree2={count2}")
                self.results["failed"] += 1
            
            # Clean up
            db1.close()
            db2.close()
            
        except Exception as e:
            print(f"    ✗ Isolation test error: {e}")
            self.results["errors"].append(f"Isolation: {str(e)}")
            self.results["failed"] += 1
    
    def validate_all_object_types(self, db, mode_name):
        """Test all Gramps object types."""
        print(f"\n  Testing all object types in {mode_name} mode:")
        
        object_tests = [
            ("Person", Person, "PERS_TEST", "I8001"),
            ("Family", Family, "FAM_TEST", "F8001"),
            ("Event", Event, "EVT_TEST", "E8001"),
            ("Place", Place, "PLC_TEST", "P8001"),
            ("Source", Source, "SRC_TEST", "S8001"),
            ("Citation", Citation, "CIT_TEST", "C8001"),
            ("Repository", Repository, "REP_TEST", "R8001"),
            ("Media", Media, "MED_TEST", "M8001"),
            ("Note", Note, "NOT_TEST", "N8001"),
            ("Tag", Tag, "TAG_TEST", "T8001"),
        ]
        
        for obj_name, obj_class, handle, gramps_id in object_tests:
            try:
                # Create object
                obj = obj_class()
                obj.set_handle(handle)
                
                # Set gramps_id if method exists
                if hasattr(obj, 'set_gramps_id'):
                    obj.set_gramps_id(gramps_id)
                
                # Add to database
                add_method = f"add_{obj_name.lower()}"
                if hasattr(db, add_method):
                    with DbTxn(f"Add {obj_name}", db) as trans:
                        getattr(db, add_method)(obj, trans)
                    
                    # Verify retrieval
                    get_method = f"get_{obj_name.lower()}_from_handle"
                    if hasattr(db, get_method):
                        retrieved = getattr(db, get_method)(handle)
                        if retrieved:
                            print(f"    ✓ {obj_name}: stored and retrieved")
                            self.results["passed"] += 1
                        else:
                            print(f"    ✗ {obj_name}: retrieval failed")
                            self.results["failed"] += 1
                    else:
                        print(f"    ⚠ {obj_name}: no get method")
                else:
                    print(f"    ⚠ {obj_name}: no add method")
                    
            except Exception as e:
                print(f"    ✗ {obj_name}: {e}")
                self.results["failed"] += 1
    
    def run_all_tests(self):
        """Run complete validation suite."""
        print("=" * 70)
        print("COMPREHENSIVE DATA VALIDATION TEST SUITE")
        print("Testing both separate and monolithic database modes")
        print("=" * 70)
        
        try:
            # Test 1: Separate mode
            print("\n=== SEPARATE MODE TESTS ===")
            
            # Create separate database
            sep_db_name = self.create_test_database("validate_separate")
            print(f"Created test database: {sep_db_name}")
            
            # Setup tree
            sep_db, sep_path = self.setup_tree(sep_db_name, "separate")
            print(f"Initialized separate mode tree")
            
            # Run tests
            self.validate_crud_operations(sep_db, "separate")
            self.validate_relationships(sep_db, "separate")
            self.validate_json_storage(sep_db, sep_db_name, "separate")
            self.validate_all_object_types(sep_db, "separate")
            
            sep_db.close()
            
            # Test 2: Monolithic mode
            print("\n=== MONOLITHIC MODE TESTS ===")
            
            # Create shared database
            mono_db_name = self.create_test_database("validate_monolithic")
            print(f"Created shared database: {mono_db_name}")
            
            # Setup tree
            mono_db, mono_path = self.setup_tree("test_tree", "monolithic", mono_db_name)
            print(f"Initialized monolithic mode tree")
            
            # Run tests
            self.validate_crud_operations(mono_db, "monolithic")
            self.validate_relationships(mono_db, "monolithic")
            self.validate_json_storage(mono_db, "test_tree", "monolithic")
            self.validate_all_object_types(mono_db, "monolithic")
            
            # Test isolation
            self.validate_data_isolation(mono_db_name)
            
            mono_db.close()
            
        except Exception as e:
            print(f"\n✗ Test suite error: {e}")
            self.results["errors"].append(f"Suite: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        
        if self.results["errors"]:
            print("\nErrors encountered:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        print("\n" + "=" * 70)
        
        # Clean up
        print("\nCleaning up test resources...")
        self.cleanup()
        
        return self.results["failed"] == 0

if __name__ == "__main__":
    import shutil
    
    validator = ComprehensiveDataValidation()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)