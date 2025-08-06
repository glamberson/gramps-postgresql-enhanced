#!/usr/bin/env python3
"""
Comprehensive test suite for PostgreSQL Enhanced plugin in separate mode.

This test suite rigorously tests all functionality when each family tree
has its own dedicated PostgreSQL database.
"""

import os
import sys
import tempfile
import shutil
import time
import threading
import subprocess
import json
from datetime import datetime
import psycopg
from psycopg import sql

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Gramps imports for testing
import mock_gramps

from postgresqlenhanced import PostgreSQLEnhanced
from connection import PostgreSQLConnection
from schema import PostgreSQLSchema

# Import Gramps classes (real if available, mock otherwise)
from mock_gramps import DbTxn, Person, Name, Surname, Family, Event, Place, Source

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

# Test data
TEST_TREES = ["gramps_test_smith", "gramps_test_jones", "gramps_test_wilson"]

TEST_PERSON_DATA = {
    "handle": "TEST001",
    "gramps_id": "I0001",
    "gender": 1,  # Male
    "primary_name": {
        "first_name": "John",
        "surname_list": [{"surname": "Smith", "prefix": "", "primary": True}],
    },
    "birth_ref_index": -1,
    "death_ref_index": -1,
    "event_ref_list": [],
    "family_list": [],
    "parent_family_list": [],
    "alternate_names": [],
    "person_ref_list": [],
    "attribute_list": [],
    "address_list": [],
    "url_list": [],
    "lds_ord_list": [],
    "citation_list": [],
    "note_list": [],
    "media_list": [],
    "tag_list": [],
    "private": False,
    "change": int(time.time()),
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


class SeparateModeTests:
    """Comprehensive test suite for separate database mode."""

    def __init__(self):
        self.temp_dirs = []
        self.db_instances = {}
        self.results = {"passed": 0, "failed": 0, "errors": []}

    def setup(self):
        """Set up test environment."""
        print("\n=== Setting up test environment ===")
        
        # Clean up any existing test databases
        self.cleanup_databases()
        
        # Create connection configuration files for each tree
        for tree_name in TEST_TREES:
            tree_dir = tempfile.mkdtemp(prefix=f"gramps_{tree_name}_")
            self.temp_dirs.append(tree_dir)
            
            # Create subdirectory with tree name
            full_path = os.path.join(tree_dir, tree_name)
            os.makedirs(full_path, exist_ok=True)
            
            # Create connection config
            config_file = os.path.join(full_path, "connection_info.txt")
            with open(config_file, "w") as f:
                f.write(f"""# PostgreSQL Connection Configuration for {tree_name}
host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = separate
database_name = {tree_name}
""")
            print(f"  Created config for {tree_name} at {config_file}")

    def cleanup_databases(self):
        """Remove any existing test databases."""
        print("\n=== Cleaning up existing test databases ===")
        
        try:
            # Connect to postgres database
            admin_conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname="postgres",
                autocommit=True
            )
            
            with admin_conn.cursor() as cur:
                for tree_name in TEST_TREES:
                    # Check if database exists
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [tree_name])
                    if cur.fetchone():
                        print(f"  Dropping existing database: {tree_name}")
                        # Terminate connections
                        cur.execute(
                            """
                            SELECT pg_terminate_backend(pid)
                            FROM pg_stat_activity
                            WHERE datname = %s AND pid <> pg_backend_pid()
                            """,
                            [tree_name]
                        )
                        # Drop database
                        cur.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(tree_name)))
            
            admin_conn.close()
            
        except Exception as e:
            print(f"  Warning during cleanup: {e}")

    def test_separate_databases_creation(self):
        """Test 1: Verify each tree creates its own database."""
        print("\n=== Test 1: Separate Database Creation ===")
        
        try:
            # Create database instances for each tree
            for i, tree_name in enumerate(TEST_TREES):
                tree_path = os.path.join(self.temp_dirs[i], tree_name)
                
                print(f"\n  Creating database for {tree_name}...")
                db = PostgreSQLEnhanced()
                db.load(tree_path, callback=None, mode="w")
                
                # Verify database was created
                admin_conn = psycopg.connect(
                    host=DB_CONFIG["host"],
                    port=DB_CONFIG["port"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    dbname="postgres",
                    autocommit=True
                )
                
                with admin_conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [tree_name])
                    if cur.fetchone():
                        print(f"    ✓ Database {tree_name} created successfully")
                    else:
                        raise Exception(f"Database {tree_name} was not created")
                
                admin_conn.close()
                
                # Store instance for later tests
                self.db_instances[tree_name] = db
                
                # Verify tables exist
                conn = psycopg.connect(
                    host=DB_CONFIG["host"],
                    port=DB_CONFIG["port"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    dbname=tree_name
                )
                
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public' 
                        ORDER BY tablename
                    """)
                    tables = [row[0] for row in cur.fetchall()]
                    
                    # Correct expectation: Real Gramps tables + our enhancements
                    expected_tables = [
                        'person', 'family', 'source', 'citation', 'event', 
                        'media', 'place', 'repository', 'note', 'tag',
                        'reference', 'name_group', 'metadata', 'gender_stats',
                        'surname'  # Our enhancement table
                    ]
                    
                    missing = set(expected_tables) - set(tables)
                    if missing:
                        raise Exception(f"Missing tables in {tree_name}: {missing}")
                    
                    print(f"    ✓ All {len(expected_tables)} tables created in {tree_name}")
                
                conn.close()
            
            print("\n  ✅ Test 1 PASSED: All databases created separately")
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"\n  ❌ Test 1 FAILED: {e}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Test 1: {e}")

    def test_data_isolation(self):
        """Test 2: Verify data isolation between databases."""
        print("\n=== Test 2: Data Isolation Between Databases ===")
        
        try:
            # Add different people to each database
            test_data = [
                ("gramps_test_smith", "SMITH001", "I0001", "John", "Smith"),
                ("gramps_test_jones", "JONES001", "I0001", "Mary", "Jones"),
                ("gramps_test_wilson", "WILSON001", "I0001", "Robert", "Wilson"),
            ]
            
            for tree_name, handle, gramps_id, first_name, surname in test_data:
                db = self.db_instances[tree_name]
                
                print(f"\n  Adding {first_name} {surname} to {tree_name}...")
                
                with DbTxn("Add person", db) as trans:
                    person = create_test_person(handle, gramps_id, first_name, surname)
                    db.add_person(person, trans)
                
                print(f"    ✓ Added person to {tree_name}")
            
            # Verify isolation - each database should only have its own person
            print("\n  Verifying data isolation...")
            
            for tree_name in TEST_TREES:
                db = self.db_instances[tree_name]
                
                # Get all people
                people = []
                for handle in db.get_person_handles():
                    person = db.get_person_from_handle(handle)
                    if person:
                        people.append(person)
                
                if len(people) != 1:
                    raise Exception(f"{tree_name} has {len(people)} people, expected 1")
                
                person = people[0]
                name = person.get_primary_name()
                first_name = name.get_first_name()
                surnames = name.get_surname_list()
                surname = surnames[0].get_surname() if surnames else ""
                
                # Verify it's the correct person for this tree
                if tree_name == "gramps_test_smith" and surname != "Smith":
                    raise Exception(f"Wrong person in {tree_name}: {surname}")
                elif tree_name == "gramps_test_jones" and surname != "Jones":
                    raise Exception(f"Wrong person in {tree_name}: {surname}")
                elif tree_name == "gramps_test_wilson" and surname != "Wilson":
                    raise Exception(f"Wrong person in {tree_name}: {surname}")
                
                print(f"    ✓ {tree_name} contains only {first_name} {surname}")
            
            print("\n  ✅ Test 2 PASSED: Data properly isolated between databases")
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"\n  ❌ Test 2 FAILED: {e}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Test 2: {e}")

    def test_concurrent_access(self):
        """Test 3: Verify concurrent access to different databases."""
        print("\n=== Test 3: Concurrent Access to Different Databases ===")
        
        def add_people_to_tree(tree_name, db, start_id, count, results):
            """Add multiple people to a tree in a thread."""
            try:
                for i in range(count):
                    handle = f"{tree_name.upper()}{start_id + i:04d}"
                    gramps_id = f"I{start_id + i:04d}"
                    first_name = f"Person{i}"
                    surname = tree_name.split("_")[-1].capitalize()
                    
                    with DbTxn(f"Add person {i}", db) as trans:
                        person = create_test_person(handle, gramps_id, first_name, surname)
                        db.add_person(person, trans)
                
                results[tree_name] = {"success": True, "count": count}
                
            except Exception as e:
                results[tree_name] = {"success": False, "error": str(e)}
        
        try:
            # Run concurrent additions
            threads = []
            results = {}
            
            print("\n  Starting concurrent operations...")
            
            for i, tree_name in enumerate(TEST_TREES):
                db = self.db_instances[tree_name]
                thread = threading.Thread(
                    target=add_people_to_tree,
                    args=(tree_name, db, 1000 + i*100, 10, results)
                )
                threads.append(thread)
                thread.start()
                print(f"    Started thread for {tree_name}")
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Check results
            print("\n  Checking results...")
            all_success = True
            
            for tree_name in TEST_TREES:
                if tree_name in results and results[tree_name]["success"]:
                    print(f"    ✓ {tree_name}: Added {results[tree_name]['count']} people")
                else:
                    error = results.get(tree_name, {}).get("error", "Unknown error")
                    print(f"    ✗ {tree_name}: Failed - {error}")
                    all_success = False
            
            if not all_success:
                raise Exception("Some concurrent operations failed")
            
            # Verify counts
            print("\n  Verifying final counts...")
            
            for tree_name in TEST_TREES:
                db = self.db_instances[tree_name]
                count = len(list(db.get_person_handles()))
                expected = 11  # 1 from test 2 + 10 from this test
                
                if count != expected:
                    raise Exception(f"{tree_name} has {count} people, expected {expected}")
                
                print(f"    ✓ {tree_name}: {count} people total")
            
            print("\n  ✅ Test 3 PASSED: Concurrent access works correctly")
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"\n  ❌ Test 3 FAILED: {e}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Test 3: {e}")

    def test_complex_operations(self):
        """Test 4: Test complex operations with relationships."""
        print("\n=== Test 4: Complex Operations with Relationships ===")
        
        try:
            # Use the first database for complex operations
            tree_name = TEST_TREES[0]
            db = self.db_instances[tree_name]
            
            print(f"\n  Testing complex operations in {tree_name}...")
            
            # Create a family
            with DbTxn("Create family", db) as trans:
                # Create parents
                father = create_test_person("FATHER001", "I2001", "James", "Smith")
                mother = create_test_person("MOTHER001", "I2002", "Sarah", "Johnson")
                db.add_person(father, trans)
                db.add_person(mother, trans)
                
                # Create family
                family = Family()
                family.set_handle("FAM001")
                family.set_gramps_id("F0001")
                family.set_father_handle(father.get_handle())
                family.set_mother_handle(mother.get_handle())
                
                # Create children
                for i in range(3):
                    child = create_test_person(f"CHILD00{i+1}", f"I300{i+1}", f"Child{i+1}", "Smith")
                    db.add_person(child, trans)
                    family.add_child_ref(child.get_handle())
                
                db.add_family(family, trans)
                
                print("    ✓ Created family with 2 parents and 3 children")
            
            # Create an event
            with DbTxn("Create event", db) as trans:
                event = Event()
                event.set_handle("EVENT001")
                event.set_gramps_id("E0001")
                event.set_type(Event.MARRIAGE)
                event.set_date_object(datetime(1995, 6, 15))
                event.set_description("Marriage of James and Sarah")
                
                db.add_event(event, trans)
                
                # Link event to family
                family = db.get_family_from_handle("FAM001")
                family.add_event_ref(event.get_handle())
                db.commit_family(family, trans)
                
                print("    ✓ Created and linked marriage event")
            
            # Create a place
            with DbTxn("Create place", db) as trans:
                place = Place()
                place.set_handle("PLACE001")
                place.set_gramps_id("P0001")
                place.set_title("Springfield Church")
                place.set_name("Springfield Church")
                
                db.add_place(place, trans)
                
                # Link place to event
                event = db.get_event_from_handle("EVENT001")
                event.set_place_handle(place.get_handle())
                db.commit_event(event, trans)
                
                print("    ✓ Created and linked place")
            
            # Verify all relationships
            print("\n  Verifying relationships...")
            
            # Check family
            family = db.get_family_from_handle("FAM001")
            if not family:
                raise Exception("Family not found")
            
            if family.get_father_handle() != "FATHER001":
                raise Exception("Father not linked correctly")
            
            if family.get_mother_handle() != "MOTHER001":
                raise Exception("Mother not linked correctly")
            
            if len(family.get_child_ref_list()) != 3:
                raise Exception("Children not linked correctly")
            
            print("    ✓ Family relationships verified")
            
            # Check event
            event = db.get_event_from_handle("EVENT001")
            if not event or event.get_place_handle() != "PLACE001":
                raise Exception("Event-place relationship not correct")
            
            print("    ✓ Event relationships verified")
            
            print("\n  ✅ Test 4 PASSED: Complex operations work correctly")
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"\n  ❌ Test 4 FAILED: {e}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Test 4: {e}")

    def test_performance(self):
        """Test 5: Performance test for separate databases."""
        print("\n=== Test 5: Performance Test ===")
        
        try:
            tree_name = TEST_TREES[1]  # Use second database
            db = self.db_instances[tree_name]
            
            print(f"\n  Testing performance in {tree_name}...")
            
            # Bulk insert test
            start_time = time.time()
            
            with DbTxn("Bulk insert", db) as trans:
                for i in range(100):
                    person = create_test_person(
                        f"PERF{i:04d}",
                        f"I9{i:04d}",
                        f"Person{i}",
                        "Performance"
                    )
                    db.add_person(person, trans)
            
            insert_time = time.time() - start_time
            print(f"    ✓ Inserted 100 people in {insert_time:.2f} seconds")
            
            # Query test
            start_time = time.time()
            
            handles = list(db.get_person_handles())
            people = []
            for handle in handles:
                person = db.get_person_from_handle(handle)
                if person:
                    people.append(person)
            
            query_time = time.time() - start_time
            print(f"    ✓ Retrieved {len(people)} people in {query_time:.2f} seconds")
            
            # Search test
            start_time = time.time()
            
            performance_people = []
            for person in people:
                surnames = person.get_primary_name().get_surname_list()
                if surnames and surnames[0].get_surname() == "Performance":
                    performance_people.append(person)
            
            search_time = time.time() - start_time
            print(f"    ✓ Found {len(performance_people)} Performance surnames in {search_time:.2f} seconds")
            
            # Performance thresholds
            if insert_time > 5.0:
                raise Exception(f"Insert too slow: {insert_time:.2f}s > 5.0s")
            
            if query_time > 2.0:
                raise Exception(f"Query too slow: {query_time:.2f}s > 2.0s")
            
            print("\n  ✅ Test 5 PASSED: Performance within acceptable limits")
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"\n  ❌ Test 5 FAILED: {e}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Test 5: {e}")

    def cleanup(self):
        """Clean up test environment."""
        print("\n=== Cleaning up test environment ===")
        
        # Close all database connections
        for tree_name, db in self.db_instances.items():
            try:
                db.close()
                print(f"  Closed connection to {tree_name}")
            except:
                pass
        
        # Remove temporary directories
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                print(f"  Removed {temp_dir}")
            except:
                pass
        
        # Optionally remove test databases
        # Uncomment to clean up databases after test
        # self.cleanup_databases()

    def run_all_tests(self):
        """Run all tests and report results."""
        print("\n" + "="*60)
        print("PostgreSQL Enhanced - Separate Mode Comprehensive Tests")
        print("NO FALLBACK POLICY: All tests must pass completely")
        print("="*60)
        
        # Setup
        self.setup()
        
        # Run tests
        self.test_separate_databases_creation()
        self.test_data_isolation()
        self.test_concurrent_access()
        self.test_complex_operations()
        self.test_performance()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY - SEPARATE MODE")
        print("="*60)
        print(f"Tests passed: {self.results['passed']}")
        print(f"Tests failed: {self.results['failed']}")
        
        if self.results['errors']:
            print("\nErrors:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        # Cleanup
        self.cleanup()
        
        # Return exit code
        return 0 if self.results['failed'] == 0 else 1


def main():
    """Main test runner."""
    tester = SeparateModeTests()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())