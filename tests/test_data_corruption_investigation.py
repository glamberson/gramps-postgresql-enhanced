#!/usr/bin/env python3
"""
DATA CORRUPTION INVESTIGATION
==============================
Focused test to identify exactly where and how data corruption occurs.
"""

import os
import sys
import json
import tempfile
import traceback
from datetime import datetime

# Add Gramps to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Import REAL Gramps objects
from gramps.gen.lib import Person, Name, Surname
from gramps.gen.db import DbTxn

# Add plugin directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from postgresqlenhanced import PostgreSQLEnhanced

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def investigate_corruption():
    """Investigate exactly where data corruption occurs."""
    
    print("=" * 80)
    print("DATA CORRUPTION INVESTIGATION")
    print("=" * 80)
    
    # Setup database
    db = PostgreSQLEnhanced()
    test_db_name = f"corruption_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_dir = tempfile.mkdtemp(prefix="corruption_test_")
    
    # Write connection settings
    settings_file = os.path.join(test_dir, "connection_info.txt")
    with open(settings_file, 'w') as f:
        f.write(f"host={DB_CONFIG['host']}\n")
        f.write(f"port={DB_CONFIG['port']}\n")
        f.write(f"user={DB_CONFIG['user']}\n")
        f.write(f"password={DB_CONFIG['password']}\n")
        f.write(f"database_name={test_db_name}\n")
        f.write("database_mode=separate\n")
    
    print(f"Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {test_db_name}\n")
    
    db.load(
        directory=test_dir,
        callback=None,
        mode="w",
        username=None,
        password=None
    )
    
    corruption_found = []
    
    # Test 1: Simple person with basic data
    print("Test 1: Simple person...")
    try:
        person1 = Person()
        person1.set_handle("TEST001")
        person1.set_gramps_id("I0001")
        person1.set_gender(Person.MALE)
        
        name1 = Name()
        name1.set_first_name("John")
        surname1 = Surname()
        surname1.set_surname("Smith")
        name1.add_surname(surname1)
        person1.set_primary_name(name1)
        
        # Get serialized data BEFORE storage
        before_data = person1.serialize()
        print(f"  Before: {json.dumps(before_data, indent=2)[:200]}...")
        
        # Store
        with DbTxn("Store person1", db) as trans:
            db.add_person(person1, trans)
        
        # Retrieve
        retrieved1 = db.get_person_from_handle("TEST001")
        
        # Get serialized data AFTER retrieval
        after_data = retrieved1.serialize() if retrieved1 else None
        print(f"  After:  {json.dumps(after_data, indent=2)[:200]}...")
        
        # Compare
        if before_data == after_data:
            print("  ✓ No corruption\n")
        else:
            print("  ✗ CORRUPTION DETECTED!")
            # Find differences
            import difflib
            diff = difflib.unified_diff(
                json.dumps(before_data, indent=2, sort_keys=True).splitlines(),
                json.dumps(after_data, indent=2, sort_keys=True).splitlines() if after_data else [],
                lineterm='',
                n=1
            )
            for line in list(diff)[:20]:
                print(f"    {line}")
            corruption_found.append("Simple person")
            print()
            
    except Exception as e:
        print(f"  Error: {e}\n")
        traceback.print_exc()
    
    # Test 2: Person with unicode and special characters
    print("Test 2: Person with unicode...")
    try:
        person2 = Person()
        person2.set_handle("TEST002")
        person2.set_gramps_id("I0002")
        person2.set_gender(Person.FEMALE)
        
        name2 = Name()
        name2.set_first_name("Björn")
        surname2 = Surname()
        surname2.set_surname("Müller-O'Brien")
        surname2.set_prefix("von der")
        name2.add_surname(surname2)
        person2.set_primary_name(name2)
        
        # Serialize before
        before_data = person2.serialize()
        
        # Store
        with DbTxn("Store person2", db) as trans:
            db.add_person(person2, trans)
        
        # Retrieve
        retrieved2 = db.get_person_from_handle("TEST002")
        after_data = retrieved2.serialize() if retrieved2 else None
        
        # Compare specific fields
        if retrieved2:
            orig_name = person2.get_primary_name().get_first_name()
            retr_name = retrieved2.get_primary_name().get_first_name()
            orig_surname = person2.get_primary_name().get_surname_list()[0].get_surname()
            retr_surname = retrieved2.get_primary_name().get_surname_list()[0].get_surname()
            
            print(f"  Original name: '{orig_name}' surname: '{orig_surname}'")
            print(f"  Retrieved name: '{retr_name}' surname: '{retr_surname}'")
            
            if orig_name == retr_name and orig_surname == retr_surname:
                print("  ✓ Unicode preserved\n")
            else:
                print("  ✗ UNICODE CORRUPTION!")
                corruption_found.append("Unicode data")
                print()
        else:
            print("  ✗ Person not retrieved!\n")
            corruption_found.append("Person retrieval failed")
            
    except Exception as e:
        print(f"  Error: {e}\n")
        traceback.print_exc()
    
    # Test 3: Multiple people to find pattern
    print("Test 3: Batch test for corruption pattern...")
    corrupted_handles = []
    
    try:
        # Create 100 people
        for i in range(100):
            person = Person()
            handle = f"BATCH{i:03d}"
            person.set_handle(handle)
            person.set_gramps_id(f"I{i:04d}")
            person.set_gender(Person.MALE if i % 2 == 0 else Person.FEMALE)
            
            name = Name()
            name.set_first_name(f"Person{i}")
            surname = Surname()
            surname.set_surname(f"Family{i % 10}")
            name.add_surname(surname)
            person.set_primary_name(name)
            
            # Store original serialization
            original_data = person.serialize()
            
            # Store in database
            with DbTxn(f"Store {handle}", db) as trans:
                db.add_person(person, trans)
            
            # Retrieve and check
            retrieved = db.get_person_from_handle(handle)
            if retrieved:
                retrieved_data = retrieved.serialize()
                if original_data != retrieved_data:
                    corrupted_handles.append(handle)
            else:
                corrupted_handles.append(f"{handle} (not found)")
        
        if corrupted_handles:
            print(f"  ✗ CORRUPTION in {len(corrupted_handles)}/100 records:")
            for handle in corrupted_handles[:10]:
                print(f"    - {handle}")
            if len(corrupted_handles) > 10:
                print(f"    ... and {len(corrupted_handles) - 10} more")
            corruption_found.append(f"Batch test: {len(corrupted_handles)}/100")
        else:
            print("  ✓ All 100 records intact")
            
    except Exception as e:
        print(f"  Error: {e}")
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("CORRUPTION INVESTIGATION RESULTS")
    print("=" * 80)
    
    if corruption_found:
        print("❌ DATA CORRUPTION DETECTED:")
        for item in corruption_found:
            print(f"  - {item}")
        print("\nThe PostgreSQL Enhanced addon is NOT safe for production use!")
    else:
        print("✓ No corruption detected in these tests")
    
    # Cleanup
    if db.is_open():
        db.close()
    
    print(f"\nTest database: {test_db_name}")

if __name__ == "__main__":
    investigate_corruption()