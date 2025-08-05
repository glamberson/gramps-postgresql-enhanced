#!/usr/bin/env python3
"""
COMPREHENSIVE API VARIATIONS TEST FOR POSTGRESQL ENHANCED
Tests ALL valid Gramps API methods and variations to ensure 100% compatibility.

This test verifies that the PostgreSQL Enhanced addon can handle:
- All valid API method variations
- Different ways to set the same data
- Edge cases and boundary conditions
- Legacy and modern API methods
"""

import os
import sys
import time
import random
from datetime import datetime

# Add Gramps to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Import real Gramps objects - import everything we might need
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
        print(f"❌ {obj_type} retrieval failed - object is None")
        return False

    orig_data = original.serialize()
    retr_data = retrieved.serialize()

    if len(orig_data) != len(retr_data):
        print(f"❌ {obj_type} serialization length mismatch: {len(orig_data)} vs {len(retr_data)}")
        return False

    differences = []
    for i, (o, r) in enumerate(zip(orig_data, retr_data)):
        if i == 17:  # Skip change_time - this is EXPECTED to change
            continue
        if o != r:
            differences.append(f"  Field {i}: {repr(o)[:100]} -> {repr(r)[:100]}")

    if differences:
        print(f"❌ {obj_type} has unexpected differences:")
        for diff in differences[:5]:
            print(diff)
        if len(differences) > 5:
            print(f"  ... and {len(differences) - 5} more differences")
        return False

    return True

def test_person_api_variations():
    """Test all valid Person API variations."""
    variations = []
    
    # Variation 1: Basic person with minimal data
    p1 = Person()
    p1.set_handle(generate_handle())
    variations.append(("Person-Minimal", p1))
    
    # Variation 2: Person with all name variations
    p2 = Person()
    p2.set_handle(generate_handle())
    p2.set_gramps_id(f"I{random.randint(1000, 9999)}")
    
    name = Name()
    name.set_first_name("John")
    name.set_surname("Smith")
    
    # Try different nickname API methods (check what actually exists)
    try:
        name.set_nick("Johnny")  # Old API?
    except AttributeError:
        try:
            name.set_nick_name("Johnny")  # New API?
        except AttributeError:
            # If neither works, set a note about it
            name.set_call_name("Johnny")  # Use call name as fallback
    
    p2.set_primary_name(name)
    variations.append(("Person-WithName", p2))
    
    # Variation 3: Person with multiple names and surnames
    p3 = Person()
    p3.set_handle(generate_handle())
    
    # Primary name with multiple surnames
    primary_name = Name()
    primary_name.set_first_name("María José")
    
    # Add multiple surnames
    surname1 = Surname()
    surname1.set_surname("García")
    surname1.set_prefix("de")
    surname1.set_primary(True)
    primary_name.add_surname(surname1)
    
    surname2 = Surname()
    surname2.set_surname("López")
    surname2.set_connector("y")
    primary_name.add_surname(surname2)
    
    p3.set_primary_name(primary_name)
    
    # Add alternate names
    alt_name1 = Name()
    alt_name1.set_first_name("Mary")
    alt_name1.set_surname("Garcia-Lopez")
    alt_name1.set_type(NameType.AKA)
    p3.add_alternate_name(alt_name1)
    
    alt_name2 = Name()
    alt_name2.set_first_name("MJ")
    alt_name2.set_type(NameType.NICK)
    p3.add_alternate_name(alt_name2)
    
    variations.append(("Person-MultipleNames", p3))
    
    # Variation 4: Person with all possible attributes
    p4 = Person()
    p4.set_handle(generate_handle())
    p4.set_gramps_id(f"I{random.randint(10000, 99999)}")
    
    # Set all person attributes
    p4.set_gender(Person.MALE)
    p4.set_privacy(True)
    
    # Add multiple addresses
    for i in range(3):
        addr = Address()
        addr.set_street(f"Street {i+1}")
        addr.set_city(f"City {i+1}")
        addr.set_postal_code(f"{10000+i}")
        p4.add_address(addr)
    
    # Add URLs
    for i in range(2):
        url = Url()
        url.set_path(f"https://example.com/person{i}")
        url.set_description(f"Link {i+1}")
        url.set_type(UrlType.WEB_HOME if i == 0 else UrlType.EMAIL)
        p4.add_url(url)
    
    # Add attributes
    for attr_type in [AttributeType.OCCUPATION, AttributeType.EDUCATION, AttributeType.RESIDENCE]:
        attr = Attribute()
        attr.set_type(attr_type)
        attr.set_value(f"Value for {attr_type}")
        p4.add_attribute(attr)
    
    # Add event references
    for i in range(3):
        event_ref = EventRef()
        event_ref.set_reference_handle(generate_handle())
        event_ref.set_role(EventRoleType.PRIMARY if i == 0 else EventRoleType.WITNESS)
        p4.add_event_ref(event_ref)
    
    # Add media references
    for i in range(2):
        media_ref = MediaRef()
        media_ref.set_reference_handle(generate_handle())
        p4.add_media_reference(media_ref)
    
    # Add notes
    for i in range(3):
        p4.add_note(generate_handle())
    
    # Add citations
    for i in range(2):
        p4.add_citation(generate_handle())
    
    # Add tags
    for tag in ["Important", "Review", "Verified"]:
        p4.add_tag(tag)
    
    variations.append(("Person-AllAttributes", p4))
    
    # Variation 5: Person with special characters and unicode
    p5 = Person()
    p5.set_handle(generate_handle())
    
    unicode_name = Name()
    unicode_name.set_first_name("李明 Владимир José")
    unicode_name.set_surname("O'Brien-García 王")
    unicode_name.set_title("Dr. 教授")
    unicode_name.set_suffix("Jr., Ph.D., 博士")
    unicode_name.set_call_name("李")
    p5.set_primary_name(unicode_name)
    
    # Attribute with potential SQL injection
    sql_attr = Attribute()
    sql_attr.set_type(AttributeType.DESCRIPTION)
    sql_attr.set_value("'; DROP TABLE persons; -- <script>alert('XSS')</script>")
    p5.add_attribute(sql_attr)
    
    variations.append(("Person-SpecialChars", p5))
    
    # Variation 6: Person with maximum field lengths
    p6 = Person()
    p6.set_handle(generate_handle())
    
    long_name = Name()
    long_name.set_first_name("A" * 500)  # Very long first name
    long_name.set_surname("B" * 500)     # Very long surname
    long_name.set_title("C" * 200)       # Long title
    long_name.set_suffix("D" * 200)      # Long suffix
    p6.set_primary_name(long_name)
    
    # Very long attribute
    long_attr = Attribute()
    long_attr.set_type(AttributeType.DESCRIPTION)
    long_attr.set_value("E" * 10000)  # 10KB description
    p6.add_attribute(long_attr)
    
    variations.append(("Person-MaxLength", p6))
    
    # Variation 7: Person with empty/null values
    p7 = Person()
    p7.set_handle(generate_handle())
    
    empty_name = Name()
    empty_name.set_first_name("")  # Empty first name
    empty_name.set_surname("")     # Empty surname
    p7.set_primary_name(empty_name)
    
    # Empty attribute
    empty_attr = Attribute()
    empty_attr.set_type(AttributeType.CUSTOM)
    empty_attr.set_value("")
    p7.add_attribute(empty_attr)
    
    variations.append(("Person-EmptyValues", p7))
    
    return variations

def test_family_api_variations():
    """Test all valid Family API variations."""
    variations = []
    
    # Variation 1: Minimal family
    f1 = Family()
    f1.set_handle(generate_handle())
    variations.append(("Family-Minimal", f1))
    
    # Variation 2: Traditional nuclear family
    f2 = Family()
    f2.set_handle(generate_handle())
    f2.set_gramps_id(f"F{random.randint(1000, 9999)}")
    f2.set_father_handle(generate_handle())
    f2.set_mother_handle(generate_handle())
    f2.set_relationship(FamilyRelType.MARRIED)
    
    # Add biological children
    for i in range(3):
        child = ChildRef()
        child.set_reference_handle(generate_handle())
        child.set_father_relation(ChildRefType.BIRTH)
        child.set_mother_relation(ChildRefType.BIRTH)
        f2.add_child_ref(child)
    
    variations.append(("Family-Nuclear", f2))
    
    # Variation 3: Blended family with various relationships
    f3 = Family()
    f3.set_handle(generate_handle())
    f3.set_father_handle(generate_handle())
    f3.set_mother_handle(generate_handle())
    f3.set_relationship(FamilyRelType.UNMARRIED)
    
    # Biological child
    bio_child = ChildRef()
    bio_child.set_reference_handle(generate_handle())
    bio_child.set_father_relation(ChildRefType.BIRTH)
    bio_child.set_mother_relation(ChildRefType.BIRTH)
    f3.add_child_ref(bio_child)
    
    # Adopted child
    adopted = ChildRef()
    adopted.set_reference_handle(generate_handle())
    adopted.set_father_relation(ChildRefType.ADOPTED)
    adopted.set_mother_relation(ChildRefType.ADOPTED)
    f3.add_child_ref(adopted)
    
    # Stepchild (father's child from previous relationship)
    stepchild = ChildRef()
    stepchild.set_reference_handle(generate_handle())
    stepchild.set_father_relation(ChildRefType.BIRTH)
    stepchild.set_mother_relation(ChildRefType.STEPCHILD)
    f3.add_child_ref(stepchild)
    
    # Foster child
    foster = ChildRef()
    foster.set_reference_handle(generate_handle())
    foster.set_father_relation(ChildRefType.FOSTER)
    foster.set_mother_relation(ChildRefType.FOSTER)
    f3.add_child_ref(foster)
    
    variations.append(("Family-Blended", f3))
    
    # Variation 4: Single parent family
    f4 = Family()
    f4.set_handle(generate_handle())
    f4.set_mother_handle(generate_handle())  # Only mother, no father
    
    child = ChildRef()
    child.set_reference_handle(generate_handle())
    child.set_mother_relation(ChildRefType.BIRTH)
    child.set_father_relation(ChildRefType.UNKNOWN)
    f4.add_child_ref(child)
    
    variations.append(("Family-SingleParent", f4))
    
    # Variation 5: Same-sex family
    f5 = Family()
    f5.set_handle(generate_handle())
    f5.set_father_handle(generate_handle())
    f5.set_mother_handle(generate_handle())  # Two fathers in practice
    f5.set_relationship(FamilyRelType.CIVIL_UNION)
    
    # Adopted children
    for i in range(2):
        child = ChildRef()
        child.set_reference_handle(generate_handle())
        child.set_father_relation(ChildRefType.ADOPTED)
        child.set_mother_relation(ChildRefType.ADOPTED)
        f5.add_child_ref(child)
    
    variations.append(("Family-SameSex", f5))
    
    return variations

def test_event_api_variations():
    """Test all valid Event API variations."""
    variations = []
    
    # Test various event types
    event_types = [
        EventType.BIRTH, EventType.DEATH, EventType.MARRIAGE,
        EventType.DIVORCE, EventType.BAPTISM, EventType.BURIAL,
        EventType.CENSUS, EventType.IMMIGRATION, EventType.OCCUPATION,
        EventType.GRADUATION, EventType.CUSTOM
    ]
    
    for event_type in event_types:
        event = Event()
        event.set_handle(generate_handle())
        event.set_gramps_id(f"E{random.randint(1000, 9999)}")
        event.set_type(event_type)
        event.set_description(f"Event of type {event_type}")
        
        # Add date with various formats
        date = Date()
        if event_type == EventType.BIRTH:
            date.set_yr_mon_day(1950, 6, 15)
        elif event_type == EventType.DEATH:
            date.set_yr_mon_day(2020, 12, 31)
            date.set_modifier(Date.MOD_ABOUT)
        elif event_type == EventType.MARRIAGE:
            date.set_yr_mon_day(1975, 7, 20)
            date.set_quality(Date.QUAL_ESTIMATED)
        else:
            date.set_year(2000 + random.randint(0, 20))
        
        event.set_date_object(date)
        
        # Add place
        event.set_place_handle(generate_handle())
        
        # Add attributes
        attr = Attribute()
        attr.set_type(AttributeType.WITNESS if event_type == EventType.MARRIAGE else AttributeType.DESCRIPTION)
        attr.set_value(f"Details for {event_type}")
        event.add_attribute(attr)
        
        variations.append((f"Event-{str(event_type).split('.')[-1]}", event))
    
    return variations

def test_place_api_variations():
    """Test all valid Place API variations."""
    variations = []
    
    # Check which API is available for Place names
    p1 = Place()
    p1.set_handle(generate_handle())
    
    # Try different methods to set place name
    try:
        # Try PlaceName object (newer API)
        place_name = PlaceName()
        place_name.set_value("Test Place")
        p1.set_name(place_name)
        variations.append(("Place-WithPlaceName", p1))
    except (NameError, TypeError):
        # Fall back to string (older API)
        try:
            p1.set_name("Test Place")
            variations.append(("Place-WithStringName", p1))
        except:
            pass
    
    # Place with coordinates
    p2 = Place()
    p2.set_handle(generate_handle())
    p2.set_gramps_id(f"P{random.randint(1000, 9999)}")
    p2.set_title("Geographic Place")
    p2.set_latitude("48.8566")
    p2.set_longitude("2.3522")
    variations.append(("Place-WithCoordinates", p2))
    
    # Place with hierarchy
    p3 = Place()
    p3.set_handle(generate_handle())
    p3.set_code("NYC")
    
    # Add place references (hierarchy)
    for i in range(3):
        try:
            place_ref = PlaceRef()
            place_ref.set_reference_handle(generate_handle())
            p3.add_placeref(place_ref)
        except (NameError, AttributeError):
            # If PlaceRef doesn't exist or method not available
            break
    
    variations.append(("Place-WithHierarchy", p3))
    
    return variations

def test_all_api_variations():
    """Main test function for all API variations."""
    print("=" * 80)
    print("COMPREHENSIVE API VARIATIONS TEST")
    print("Testing all valid Gramps API methods and variations")
    print("=" * 80)
    print()
    
    # Database configuration
    config = {
        "host": "192.168.10.90",
        "port": 5432,
        "user": "genealogy_user",
        "password": "GenealogyData2025",
        "database": f"api_variations_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
    # Create a directory for the connection file
    test_dir = f"/tmp/api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(test_dir, exist_ok=True)
    
    # Move connection file to proper location
    conn_file_path = os.path.join(test_dir, "connection_info.txt")
    os.rename(conn_file, conn_file_path)
    
    db.load(test_dir, update=False, callback=None)
    
    total_tested = 0
    total_passed = 0
    total_failed = 0
    
    try:
        # Test Person API variations
        print("\n" + "="*60)
        print("Testing Person API Variations")
        print("="*60)
        
        person_variations = test_person_api_variations()
        for variation_name, person in person_variations:
            try:
                handle = person.get_handle()
                
                # Store in database
                with DbTxn(f"Add {variation_name}", db) as trans:
                    db.add_person(person, trans)
                
                # Retrieve from database
                retrieved = db.get_person_from_handle(handle)
                
                # Verify data integrity
                if compare_ignoring_change_time(person, retrieved, variation_name):
                    print(f"  ✅ {variation_name}: PASSED")
                    total_passed += 1
                else:
                    print(f"  ❌ {variation_name}: FAILED - Data mismatch")
                    total_failed += 1
                
                total_tested += 1
                
            except Exception as e:
                print(f"  ❌ {variation_name}: FAILED - {str(e)}")
                total_failed += 1
                total_tested += 1
        
        # Test Family API variations
        print("\n" + "="*60)
        print("Testing Family API Variations")
        print("="*60)
        
        family_variations = test_family_api_variations()
        for variation_name, family in family_variations:
            try:
                handle = family.get_handle()
                
                # Store in database
                with DbTxn(f"Add {variation_name}", db) as trans:
                    db.add_family(family, trans)
                
                # Retrieve from database
                retrieved = db.get_family_from_handle(handle)
                
                # Verify data integrity
                if compare_ignoring_change_time(family, retrieved, variation_name):
                    print(f"  ✅ {variation_name}: PASSED")
                    total_passed += 1
                else:
                    print(f"  ❌ {variation_name}: FAILED - Data mismatch")
                    total_failed += 1
                
                total_tested += 1
                
            except Exception as e:
                print(f"  ❌ {variation_name}: FAILED - {str(e)}")
                total_failed += 1
                total_tested += 1
        
        # Test Event API variations
        print("\n" + "="*60)
        print("Testing Event API Variations")
        print("="*60)
        
        event_variations = test_event_api_variations()
        for variation_name, event in event_variations:
            try:
                handle = event.get_handle()
                
                # Store in database
                with DbTxn(f"Add {variation_name}", db) as trans:
                    db.add_event(event, trans)
                
                # Retrieve from database
                retrieved = db.get_event_from_handle(handle)
                
                # Verify data integrity
                if compare_ignoring_change_time(event, retrieved, variation_name):
                    print(f"  ✅ {variation_name}: PASSED")
                    total_passed += 1
                else:
                    print(f"  ❌ {variation_name}: FAILED - Data mismatch")
                    total_failed += 1
                
                total_tested += 1
                
            except Exception as e:
                print(f"  ❌ {variation_name}: FAILED - {str(e)}")
                total_failed += 1
                total_tested += 1
        
        # Test Place API variations
        print("\n" + "="*60)
        print("Testing Place API Variations")
        print("="*60)
        
        place_variations = test_place_api_variations()
        for variation_name, place in place_variations:
            try:
                handle = place.get_handle()
                
                # Store in database
                with DbTxn(f"Add {variation_name}", db) as trans:
                    db.add_place(place, trans)
                
                # Retrieve from database
                retrieved = db.get_place_from_handle(handle)
                
                # Verify data integrity
                if compare_ignoring_change_time(place, retrieved, variation_name):
                    print(f"  ✅ {variation_name}: PASSED")
                    total_passed += 1
                else:
                    print(f"  ❌ {variation_name}: FAILED - Data mismatch")
                    total_failed += 1
                
                total_tested += 1
                
            except Exception as e:
                print(f"  ❌ {variation_name}: FAILED - {str(e)}")
                total_failed += 1
                total_tested += 1
        
        # Print summary
        print("\n" + "="*80)
        print("API VARIATIONS TEST SUMMARY")
        print("="*80)
        print(f"Total Variations Tested: {total_tested}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        print(f"Success Rate: {(total_passed/total_tested*100):.1f}%")
        
        if total_failed == 0:
            print("\n✅ ALL API VARIATIONS PASSED - EXCELLENT COMPATIBILITY!")
        else:
            print(f"\n⚠️ {total_failed} API VARIATIONS FAILED - INVESTIGATION NEEDED")
            
    finally:
        # Close database
        db.close()
        print(f"\nTest database: {config['database']}")
    
    return total_failed == 0

if __name__ == "__main__":
    success = test_all_api_variations()
    sys.exit(0 if success else 1)