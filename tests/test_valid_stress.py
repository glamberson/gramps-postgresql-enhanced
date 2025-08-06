#!/usr/bin/env python3
"""
VALID DATA STRESS TEST FOR POSTGRESQL ENHANCED
Tests with ALL valid data variations including edge cases.
NO invalid data - only legitimate variations that should be accepted.
"""

import os
import sys
import time
import random
import json
from datetime import datetime

# Add Gramps to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Import real Gramps objects
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
        if i == 17:  # Skip change_time - expected to change
            continue
        if o != r:
            return False
    return True

def generate_valid_test_data(data_type, variation=0):
    """
    Generate VALID test data for different types.
    All data returned is legitimate and should be accepted.
    """
    if data_type == "handle":
        return generate_handle()
    
    elif data_type == "boolean":
        # Valid boolean variations
        variations = [
            True,      # Standard boolean
            False,     # Standard boolean
            1,         # SQLite-style true
            0,         # SQLite-style false
            None,      # NULL value
        ]
        return variations[variation % len(variations)]
    
    elif data_type == "integer":
        # Valid integer variations
        variations = [
            0,                    # Zero
            1,                    # Small positive
            -1,                   # Small negative
            2147483647,          # Max 32-bit int
            -2147483648,         # Min 32-bit int
            random.randint(1, 1000000),  # Random positive
            None,                # NULL value
        ]
        return variations[variation % len(variations)]
    
    elif data_type == "string":
        # Valid string variations including unicode
        variations = [
            "Simple text",
            "Text with 'quotes' and \"double quotes\"",
            "Unicode: 李明 Владимир José François",
            "Special chars: & < > @ # $ % ^ * ( )",
            "Multi-line\ntext\nwith\nbreaks",
            "Very " + "long " * 100 + "text",  # Long but valid
            "",                    # Empty string (valid for most fields)
            None,                  # NULL value
            "Path: C:\\Users\\Test\\Documents\\file.txt",
            "URL: https://example.com/page?param=value&other=123",
            "Email: user@example.com",
            "Accented: àáâãäåæçèéêë",
            "Math: ∑ ∏ ∫ ≈ ≠ ≤ ≥ ± × ÷",
        ]
        return variations[variation % len(variations)]
    
    elif data_type == "text":
        # Large text blocks (for notes, descriptions)
        variations = [
            "A" * 10000,           # 10KB of text
            "Line\n" * 1000,       # Many lines
            json.dumps([{"key": "value"} for _ in range(100)]),  # JSON-like text
            "<!-- HTML-like content --> <tag>Not real HTML</tag>",
            None,                  # NULL value
        ]
        return variations[variation % len(variations)]
    
    elif data_type == "date":
        # Valid date representations
        variations = [
            0,                     # Epoch
            int(time.time()),      # Current time
            946684800,            # Year 2000
            -2208988800,          # Year 1900
            None,                 # NULL value
        ]
        return variations[variation % len(variations)]
    
    elif data_type == "gender":
        # Valid gender codes
        return random.choice([0, 1, 2])  # Unknown, Male, Female
    
    elif data_type == "confidence":
        # Valid confidence levels
        return random.choice([0, 1, 2, 3, 4])  # Very Low to Very High
    
    elif data_type == "privacy":
        # Valid privacy values - using variations
        variations = [True, False, 1, 0, None]
        return variations[variation % len(variations)]
    
    else:
        # Default: return None (NULL)
        return None

def create_valid_person_variations():
    """Create Person objects with various VALID data combinations."""
    variations = []
    
    for i in range(10):
        person = Person()
        person.set_handle(generate_handle())
        person.set_gramps_id(f"I{random.randint(1000, 99999)}")
        
        # Create name with valid variations
        name = Name()
        name.set_first_name(generate_valid_test_data("string", i))
        
        # Add surname properly
        surname = Surname()
        surname_text = generate_valid_test_data("string", i + 1)
        if surname_text:  # Only set if not None
            surname.set_surname(surname_text)
        name.add_surname(surname)
        
        person.set_primary_name(name)
        
        # Set gender with valid values
        person.set_gender(generate_valid_test_data("gender"))
        
        # Set privacy with valid variations (including SQLite style)
        privacy = generate_valid_test_data("privacy", i)
        if privacy is not None:
            person.set_privacy(privacy)
        
        # Add some attributes with valid data
        if i % 2 == 0:
            attr = Attribute()
            attr.set_type(AttributeType.OCCUPATION)
            attr.set_value(generate_valid_test_data("string", i + 2))
            person.add_attribute(attr)
        
        # Add notes with valid variations
        if i % 3 == 0:
            for j in range(3):
                person.add_note(generate_handle())
        
        variations.append((f"Person-Var{i}", person))
    
    return variations

def create_valid_family_variations():
    """Create Family objects with various VALID data combinations."""
    variations = []
    
    for i in range(10):
        family = Family()
        family.set_handle(generate_handle())
        family.set_gramps_id(f"F{random.randint(1000, 99999)}")
        
        # Set parents (some families might have one parent)
        if i % 3 != 0:
            family.set_father_handle(generate_handle())
        if i % 3 != 1:
            family.set_mother_handle(generate_handle())
        
        # Add children
        num_children = i % 5
        for j in range(num_children):
            child = ChildRef()
            child.set_reference_handle(generate_handle())
            child.set_father_relation(ChildRefType.BIRTH)
            child.set_mother_relation(ChildRefType.BIRTH)
            family.add_child_ref(child)
        
        # Set privacy with valid variations
        privacy = generate_valid_test_data("privacy", i)
        if privacy is not None:
            family.set_privacy(privacy)
        
        variations.append((f"Family-Var{i}", family))
    
    return variations

def create_valid_note_variations():
    """Create Note objects with various VALID text content."""
    variations = []
    
    for i in range(10):
        note = Note()
        note.set_handle(generate_handle())
        note.set_gramps_id(f"N{random.randint(1000, 99999)}")
        
        # Set note type
        note.set_type(NoteType.RESEARCH if i % 2 == 0 else NoteType.GENERAL)
        
        # Set text content with valid variations
        text = generate_valid_test_data("text", i)
        if text:
            note.set(text)
        
        # Set format (0=formatted, 1=plain)
        note.set_format(i % 2)
        
        # Set privacy with valid variations
        privacy = generate_valid_test_data("privacy", i)
        if privacy is not None:
            note.set_privacy(privacy)
        
        variations.append((f"Note-Var{i}", note))
    
    return variations

def test_valid_stress():
    """Main test function for valid data stress testing."""
    print("=" * 80)
    print("VALID DATA STRESS TEST")
    print("Testing with all valid data variations")
    print("=" * 80)
    print()
    
    # Database configuration
    config = {
        "host": "192.168.10.90",
        "port": 5432,
        "user": "genealogy_user",
        "password": "GenealogyData2025",
        "database": f"valid_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
    
    print(f"Creating test database: {config['database']}")
    test_dir = f"/tmp/valid_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(test_dir, exist_ok=True)
    
    conn_file_path = os.path.join(test_dir, "connection_info.txt")
    os.rename(conn_file, conn_file_path)
    
    db.load(test_dir, update=False, callback=None)
    
    total_tested = 0
    total_passed = 0
    total_failed = 0
    
    try:
        # Test Person variations
        print("\n" + "="*60)
        print("Testing Person with valid variations")
        print("="*60)
        
        person_variations = create_valid_person_variations()
        for var_name, person in person_variations:
            try:
                handle = person.get_handle()
                
                # Store in database
                with DbTxn(f"Add {var_name}", db) as trans:
                    db.add_person(person, trans)
                
                # Retrieve from database
                retrieved = db.get_person_from_handle(handle)
                
                # Verify data integrity
                if compare_ignoring_change_time(person, retrieved, var_name):
                    print(f"  ✅ {var_name}: Data preserved correctly")
                    total_passed += 1
                else:
                    print(f"  ❌ {var_name}: Data changed unexpectedly")
                    total_failed += 1
                
                total_tested += 1
                
            except Exception as e:
                print(f"  ❌ {var_name}: Exception - {str(e)}")
                total_failed += 1
                total_tested += 1
        
        # Test Family variations
        print("\n" + "="*60)
        print("Testing Family with valid variations")
        print("="*60)
        
        family_variations = create_valid_family_variations()
        for var_name, family in family_variations:
            try:
                handle = family.get_handle()
                
                # Store in database
                with DbTxn(f"Add {var_name}", db) as trans:
                    db.add_family(family, trans)
                
                # Retrieve from database
                retrieved = db.get_family_from_handle(handle)
                
                # Verify data integrity
                if compare_ignoring_change_time(family, retrieved, var_name):
                    print(f"  ✅ {var_name}: Data preserved correctly")
                    total_passed += 1
                else:
                    print(f"  ❌ {var_name}: Data changed unexpectedly")
                    total_failed += 1
                
                total_tested += 1
                
            except Exception as e:
                print(f"  ❌ {var_name}: Exception - {str(e)}")
                total_failed += 1
                total_tested += 1
        
        # Test Note variations
        print("\n" + "="*60)
        print("Testing Note with valid variations")
        print("="*60)
        
        note_variations = create_valid_note_variations()
        for var_name, note in note_variations:
            try:
                handle = note.get_handle()
                
                # Store in database
                with DbTxn(f"Add {var_name}", db) as trans:
                    db.add_note(note, trans)
                
                # Retrieve from database
                retrieved = db.get_note_from_handle(handle)
                
                # Verify data integrity
                if compare_ignoring_change_time(note, retrieved, var_name):
                    print(f"  ✅ {var_name}: Data preserved correctly")
                    total_passed += 1
                else:
                    print(f"  ❌ {var_name}: Data changed unexpectedly")
                    total_failed += 1
                
                total_tested += 1
                
            except Exception as e:
                print(f"  ❌ {var_name}: Exception - {str(e)}")
                total_failed += 1
                total_tested += 1
        
        # Test edge cases
        print("\n" + "="*60)
        print("EDGE CASE TESTS")
        print("="*60)
        
        # Test 1: Empty database queries
        print("\nTest 1: Empty result queries...")
        try:
            result = db.get_person_from_handle("nonexistent_handle")
            if result is None:
                print("  ✅ Nonexistent handle returns None correctly")
                total_passed += 1
            else:
                print("  ❌ Nonexistent handle should return None")
                total_failed += 1
            total_tested += 1
        except Exception as e:
            print(f"  ❌ Exception on nonexistent handle: {e}")
            total_failed += 1
            total_tested += 1
        
        # Test 2: Large batch insertion
        print("\nTest 2: Batch insertion of 1000 persons...")
        start_time = time.time()
        try:
            for i in range(1000):
                p = Person()
                p.set_handle(generate_handle())
                p.set_gramps_id(f"BATCH{i:06d}")
                with DbTxn(f"Batch add {i}", db) as trans:
                    db.add_person(p, trans)
            
            elapsed = time.time() - start_time
            print(f"  ✅ 1000 persons inserted in {elapsed:.2f} seconds")
            print(f"     Performance: {1000/elapsed:.0f} persons/second")
            total_passed += 1
            total_tested += 1
        except Exception as e:
            print(f"  ❌ Batch insertion failed: {e}")
            total_failed += 1
            total_tested += 1
        
        # Test 3: Maximum field sizes (but still valid)
        print("\nTest 3: Maximum valid field sizes...")
        try:
            big_note = Note()
            big_note.set_handle(generate_handle())
            # 1MB of valid text (not 10MB to be reasonable)
            big_text = "A" * (1024 * 1024)
            big_note.set(big_text)
            
            with DbTxn("Add big note", db) as trans:
                db.add_note(big_note, trans)
            
            retrieved = db.get_note_from_handle(big_note.get_handle())
            if retrieved and len(retrieved.get()) == len(big_text):
                print(f"  ✅ 1MB note stored and retrieved correctly")
                total_passed += 1
            else:
                print(f"  ❌ 1MB note not preserved correctly")
                total_failed += 1
            total_tested += 1
        except Exception as e:
            print(f"  ❌ Large note failed: {e}")
            total_failed += 1
            total_tested += 1
        
        # Print summary
        print("\n" + "="*80)
        print("VALID DATA STRESS TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tested}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        
        if total_tested > 0:
            success_rate = (total_passed / total_tested * 100)
            print(f"Success Rate: {success_rate:.1f}%")
            
            if total_failed == 0:
                print("\n✅ PERFECT! All valid data handled correctly!")
            else:
                print(f"\n⚠️ {total_failed} tests failed - investigation needed")
        
    finally:
        # Close database
        db.close()
        print(f"\nTest database: {config['database']}")
    
    return total_failed == 0

if __name__ == "__main__":
    success = test_valid_stress()
    sys.exit(0 if success else 1)