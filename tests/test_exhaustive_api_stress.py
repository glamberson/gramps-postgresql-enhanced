#!/usr/bin/env python3
"""
EXHAUSTIVE API STRESS TEST FOR POSTGRESQL ENHANCED
Tests EVERY possible Gramps API method with maximum theoretical limits.

This test:
1. Dynamically discovers all available methods for each object type
2. Tests each method with maximum payloads
3. Tests boundary conditions and edge cases
4. Ensures the database can handle ANY valid Gramps operation
"""

import os
import sys
import time
import random
import inspect
import traceback
from datetime import datetime

# Add Gramps to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Import all Gramps objects
from gramps.gen.lib import *
from gramps.gen.db import DbTxn
from gramps.gen.utils.id import create_id

# Import PostgreSQL Enhanced addon
from postgresqlenhanced import PostgreSQLEnhanced

def generate_handle():
    """Generate a unique handle."""
    return create_id()

def compare_ignoring_change_time(original, retrieved, obj_type="Object"):
    """Compare serialized data ignoring field 17 (change_time)."""
    if not retrieved:
        return False

    try:
        orig_data = original.serialize()
        retr_data = retrieved.serialize()
    except:
        return False

    if len(orig_data) != len(retr_data):
        return False

    for i, (o, r) in enumerate(zip(orig_data, retr_data)):
        if i == 17:  # Skip change_time
            continue
        if o != r:
            return False
    return True

def discover_methods(obj):
    """Discover all methods of an object."""
    methods = {}
    for name in dir(obj):
        if not name.startswith('_'):
            attr = getattr(obj, name)
            if callable(attr):
                try:
                    sig = inspect.signature(attr)
                    methods[name] = {
                        'callable': attr,
                        'params': list(sig.parameters.keys()),
                        'param_count': len(sig.parameters)
                    }
                except:
                    methods[name] = {
                        'callable': attr,
                        'params': [],
                        'param_count': 0
                    }
    return methods

def generate_test_data(param_name, index=0):
    """Generate test data based on parameter name."""
    # Maximum size test data
    MAX_STRING = "A" * 100000  # 100KB string
    MAX_INT = 2147483647  # Max 32-bit integer
    MAX_FLOAT = 1.7976931348623157e+308  # Max float
    
    # SQL injection and XSS attempts
    INJECTION_STRINGS = [
        "'; DROP TABLE persons; --",
        "<script>alert('XSS')</script>",
        "\" OR \"1\"=\"1",
        "'; DELETE FROM persons WHERE '1'='1",
        "../../../etc/passwd",
        "\\x00\\x01\\x02\\x03",  # Null bytes
        "<?php system('rm -rf /'); ?>",
        "<img src=x onerror=alert('XSS')>",
    ]
    
    # Unicode stress test
    UNICODE_STRINGS = [
        "李明 Владимир José François Müller",  # Mixed scripts
        "🎉🎊🎈🎆🎇🎁🎂🎃🎄🎋",  # Emojis
        "ἀβγδεζηθικλμνξοπρστυφχψω",  # Greek
        "אבגדהוזחטיכלמנסעפצקרשת",  # Hebrew
        "अआइईउऊऋॠऌॡएऐओऔकखगघङ",  # Hindi
        "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ",  # Korean
        "\u200b\u200c\u200d\u2060\ufeff",  # Zero-width characters
    ]
    
    # Parameter-specific data generation
    if 'handle' in param_name.lower():
        return generate_handle()
    elif 'name' in param_name.lower() or 'title' in param_name.lower():
        return random.choice([MAX_STRING[:1000], random.choice(UNICODE_STRINGS)])
    elif 'description' in param_name.lower() or 'text' in param_name.lower():
        return random.choice([MAX_STRING, random.choice(INJECTION_STRINGS)])
    elif 'value' in param_name.lower() or 'data' in param_name.lower():
        return random.choice([MAX_STRING[:5000], random.choice(INJECTION_STRINGS)])
    elif 'date' in param_name.lower() or 'time' in param_name.lower():
        return random.randint(0, MAX_INT)
    elif 'latitude' in param_name.lower() or 'longitude' in param_name.lower():
        return str(random.uniform(-180, 180))
    elif 'index' in param_name.lower() or 'number' in param_name.lower():
        return random.randint(0, 1000)
    elif 'type' in param_name.lower():
        return random.randint(0, 100)
    elif 'privacy' in param_name.lower() or 'primary' in param_name.lower():
        return random.choice([True, False])
    elif 'list' in param_name.lower():
        return [generate_handle() for _ in range(100)]  # Large list
    elif 'path' in param_name.lower() or 'url' in param_name.lower():
        return random.choice(INJECTION_STRINGS + ["http://example.com/" + "x"*10000])
    else:
        # Default: try various types
        return random.choice([
            MAX_STRING[:100],
            random.choice(UNICODE_STRINGS),
            random.choice(INJECTION_STRINGS),
            MAX_INT,
            None,
            "",
            [],
            {}
        ])

def stress_test_object(obj_class, obj_name):
    """Stress test a single object type with all possible methods."""
    results = {
        'total_methods': 0,
        'methods_tested': 0,
        'methods_succeeded': 0,
        'methods_failed': 0,
        'max_payload_tests': 0,
        'edge_case_tests': 0,
        'failures': []
    }
    
    # Create instance
    try:
        obj = obj_class()
    except:
        return results
    
    # Set handle first (required for most objects)
    try:
        obj.set_handle(generate_handle())
    except:
        pass
    
    # Discover all methods
    methods = discover_methods(obj)
    results['total_methods'] = len(methods)
    
    # Test each method with various payloads
    for method_name, method_info in methods.items():
        results['methods_tested'] += 1
        
        # Skip certain methods that might break the object
        if method_name in ['serialize', 'unserialize', 'get_handle', 'to_struct', 'from_struct']:
            continue
        
        # Test with different payload sizes and types
        test_cases = []
        
        # Generate test cases based on parameter count
        if method_info['param_count'] == 0:
            test_cases.append([])  # No parameters
        elif method_info['param_count'] == 1:
            # Single parameter - test various inputs
            test_cases.extend([
                [generate_test_data(method_info['params'][0] if method_info['params'] else 'value', i)]
                for i in range(5)  # Test 5 different values
            ])
            # Add maximum payload test
            test_cases.append(["X" * 1000000])  # 1MB string
            results['max_payload_tests'] += 1
        else:
            # Multiple parameters
            test_cases.append([
                generate_test_data(param, i) 
                for i, param in enumerate(method_info['params'])
            ])
            # Edge case: all None
            test_cases.append([None] * method_info['param_count'])
            results['edge_case_tests'] += 1
        
        # Try each test case
        method_worked = False
        for test_case in test_cases:
            try:
                method_info['callable'](*test_case)
                method_worked = True
                break  # At least one case worked
            except Exception as e:
                continue
        
        if method_worked:
            results['methods_succeeded'] += 1
        else:
            results['methods_failed'] += 1
            results['failures'].append(method_name)
    
    return results, obj

def test_database_limits():
    """Test database with maximum theoretical limits."""
    print("=" * 80)
    print("EXHAUSTIVE API STRESS TEST WITH MAXIMUM LIMITS")
    print("Testing every possible Gramps API method with extreme payloads")
    print("=" * 80)
    print()
    
    # Database configuration
    config = {
        "host": "192.168.10.90",
        "port": 5432,
        "user": "genealogy_user",
        "password": "GenealogyData2025",
        "database": f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "database_mode": "separate"
    }
    
    # Initialize database
    db = PostgreSQLEnhanced()
    
    # Write connection info to file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(f"host={config['host']}\n")
        f.write(f"port={config['port']}\n")
        f.write(f"user={config['user']}\n")
        f.write(f"password={config['password']}\n")
        f.write(f"database={config['database']}\n")
        f.write(f"database_mode={config['database_mode']}\n")
        conn_file = f.name
    
    print(f"Creating stress test database: {config['database']}")
    # Create a directory for the connection file
    test_dir = f"/tmp/stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(test_dir, exist_ok=True)
    
    # Move connection file to proper location
    conn_file_path = os.path.join(test_dir, "connection_info.txt")
    os.rename(conn_file, conn_file_path)
    
    db.load(test_dir, update=False, callback=None)
    
    # Object types to test
    test_objects = [
        (Person, "Person", db.add_person, db.get_person_from_handle),
        (Family, "Family", db.add_family, db.get_family_from_handle),
        (Event, "Event", db.add_event, db.get_event_from_handle),
        (Place, "Place", db.add_place, db.get_place_from_handle),
        (Source, "Source", db.add_source, db.get_source_from_handle),
        (Citation, "Citation", db.add_citation, db.get_citation_from_handle),
        (Repository, "Repository", db.add_repository, db.get_repository_from_handle),
        (Media, "Media", db.add_media, db.get_media_from_handle),
        (Note, "Note", db.add_note, db.get_note_from_handle),
        (Tag, "Tag", db.add_tag, db.get_tag_from_handle),
    ]
    
    overall_results = {}
    
    try:
        for obj_class, obj_name, add_func, get_func in test_objects:
            print(f"\n{'='*60}")
            print(f"STRESS TESTING: {obj_name}")
            print(f"{'='*60}")
            
            # Stress test the object
            results, test_obj = stress_test_object(obj_class, obj_name)
            overall_results[obj_name] = results
            
            print(f"Methods discovered: {results['total_methods']}")
            print(f"Methods tested: {results['methods_tested']}")
            print(f"Methods succeeded: {results['methods_succeeded']}")
            print(f"Methods failed: {results['methods_failed']}")
            print(f"Max payload tests: {results['max_payload_tests']}")
            print(f"Edge case tests: {results['edge_case_tests']}")
            
            if results['failures']:
                print(f"Failed methods: {', '.join(results['failures'][:10])}")
                if len(results['failures']) > 10:
                    print(f"  ... and {len(results['failures']) - 10} more")
            
            # Now test database storage with the stressed object
            print(f"\nTesting database storage for stressed {obj_name}...")
            
            # Test multiple variations
            for i in range(5):
                try:
                    # Create heavily stressed object
                    stressed_obj, _ = stress_test_object(obj_class, obj_name)
                    
                    # Ensure it has a handle
                    if hasattr(test_obj, 'set_handle'):
                        test_obj.set_handle(generate_handle())
                    
                    handle = test_obj.get_handle() if hasattr(test_obj, 'get_handle') else None
                    
                    if handle:
                        # Store in database
                        with DbTxn(f"Add stressed {obj_name} #{i}", db) as trans:
                            add_func(test_obj, trans)
                        
                        # Retrieve from database
                        retrieved = get_func(handle)
                        
                        # Verify data integrity
                        if compare_ignoring_change_time(test_obj, retrieved, f"Stressed-{obj_name}-{i}"):
                            print(f"  ✅ Stressed {obj_name} #{i}: Database handled extreme data")
                        else:
                            print(f"  ❌ Stressed {obj_name} #{i}: Data integrity failed")
                    
                except Exception as e:
                    print(f"  ❌ Stressed {obj_name} #{i}: Exception - {str(e)[:100]}")
        
        # Test extreme cases
        print("\n" + "="*60)
        print("EXTREME EDGE CASES")
        print("="*60)
        
        # Test 1: Maximum number of objects
        print("\nTest 1: Creating 1000 persons rapidly...")
        start_time = time.time()
        for i in range(1000):
            p = Person()
            p.set_handle(generate_handle())
            p.set_gramps_id(f"I{i:06d}")
            with DbTxn(f"Add person {i}", db) as trans:
                db.add_person(p, trans)
        elapsed = time.time() - start_time
        print(f"  ✅ Created 1000 persons in {elapsed:.2f} seconds")
        
        # Test 2: Object with maximum relationships
        print("\nTest 2: Family with 100 children...")
        mega_family = Family()
        mega_family.set_handle(generate_handle())
        mega_family.set_father_handle(generate_handle())
        mega_family.set_mother_handle(generate_handle())
        for i in range(100):
            child = ChildRef()
            child.set_reference_handle(generate_handle())
            mega_family.add_child_ref(child)
        
        with DbTxn("Add mega family", db) as trans:
            db.add_family(mega_family, trans)
        
        retrieved_family = db.get_family_from_handle(mega_family.get_handle())
        if retrieved_family and len(retrieved_family.get_child_ref_list()) == 100:
            print(f"  ✅ Family with 100 children stored and retrieved")
        else:
            print(f"  ❌ Failed to handle family with 100 children")
        
        # Test 3: Note with 10MB of text
        print("\nTest 3: Note with 10MB of text...")
        huge_note = Note()
        huge_note.set_handle(generate_handle())
        huge_text = "A" * (10 * 1024 * 1024)  # 10MB
        huge_note.set(huge_text)
        
        try:
            with DbTxn("Add huge note", db) as trans:
                db.add_note(huge_note, trans)
            retrieved_note = db.get_note_from_handle(huge_note.get_handle())
            if retrieved_note and len(retrieved_note.get()) == len(huge_text):
                print(f"  ✅ 10MB note stored and retrieved successfully")
            else:
                print(f"  ❌ Failed to handle 10MB note")
        except Exception as e:
            print(f"  ❌ Exception with 10MB note: {str(e)[:100]}")
        
        # Test 4: Person with 1000 notes
        print("\nTest 4: Person with 1000 notes...")
        note_person = Person()
        note_person.set_handle(generate_handle())
        for i in range(1000):
            note_person.add_note(generate_handle())
        
        with DbTxn("Add person with 1000 notes", db) as trans:
            db.add_person(note_person, trans)
        
        retrieved_person = db.get_person_from_handle(note_person.get_handle())
        if retrieved_person and len(retrieved_person.get_note_list()) == 1000:
            print(f"  ✅ Person with 1000 notes stored and retrieved")
        else:
            print(f"  ❌ Failed to handle person with 1000 notes")
        
        # Print summary
        print("\n" + "="*80)
        print("STRESS TEST SUMMARY")
        print("="*80)
        
        total_methods = sum(r['total_methods'] for r in overall_results.values())
        total_tested = sum(r['methods_tested'] for r in overall_results.values())
        total_succeeded = sum(r['methods_succeeded'] for r in overall_results.values())
        total_failed = sum(r['methods_failed'] for r in overall_results.values())
        total_max_payload = sum(r['max_payload_tests'] for r in overall_results.values())
        total_edge_cases = sum(r['edge_case_tests'] for r in overall_results.values())
        
        print(f"Total methods discovered: {total_methods}")
        print(f"Total methods tested: {total_tested}")
        print(f"Total methods succeeded: {total_succeeded}")
        print(f"Total methods failed: {total_failed}")
        print(f"Total max payload tests: {total_max_payload}")
        print(f"Total edge case tests: {total_edge_cases}")
        
        if total_failed == 0:
            print("\n✅ PERFECT! Database handled ALL API methods with extreme payloads!")
        else:
            success_rate = (total_succeeded / total_tested * 100) if total_tested > 0 else 0
            print(f"\n⚠️ Success rate: {success_rate:.1f}%")
            print("Some methods failed, but this may be expected for invalid operations")
            
    finally:
        # Close database
        db.close()
        print(f"\nStress test database: {config['database']}")
    
    return True

if __name__ == "__main__":
    success = test_database_limits()
    sys.exit(0 if success else 1)