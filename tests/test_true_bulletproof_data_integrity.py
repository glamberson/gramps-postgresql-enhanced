#!/usr/bin/env python3
"""
TRUE BULLETPROOF DATA INTEGRITY TEST SUITE
===========================================
Tests ACTUAL data storage, retrieval, and integrity - not just method signatures.
Every byte of genealogical data must be perfect or families lose their history.
"""

import os
import sys
import json
import pickle
import hashlib
import tempfile
import threading
import time
import random
import traceback
from decimal import Decimal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from collections import defaultdict

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import mock framework and PostgreSQL Enhanced
import mock_gramps
from postgresqlenhanced import PostgreSQLEnhanced

# Import Gramps objects - use what's available in mock_gramps
try:
    # Try to import from actual Gramps if available
    from gramps.gen.lib import (
        Person, Name, Surname, Family, Event, Place, PlaceName,
        Source, Citation, Repository, Media, Note, Tag, Date, Address,
        Attribute, EventRef, EventType, ChildRef, PersonRef, Url,
        MediaRef, NoteRef, SourceRef, RepoRef
    )
    from gramps.gen.db import DbTxn
    USING_REAL_GRAMPS = True
except ImportError:
    # Fall back to mock objects
    from mock_gramps import (
        MockPerson as Person, MockName as Name, MockSurname as Surname,
        MockFamily as Family, MockEvent as Event, MockPlace as Place,
        MockSource as Source, MockCitation as Citation, 
        MockRepository as Repository, MockMedia as Media,
        MockNote as Note, MockTag as Tag, MockDbTxn as DbTxn,
        MockEventType as EventType, MockChildRef as ChildRef
    )
    # Create mock classes for missing ones
    class PlaceName:
        def __init__(self):
            self.value = ""
        def set_value(self, value):
            self.value = value
        def get_value(self):
            return self.value
    
    class Date:
        QUAL_ESTIMATED = 1
        MOD_ABOUT = 2 
        CAL_GREGORIAN = 1
        def __init__(self):
            self.text = ""
        def set(self, **kwargs):
            self.text = kwargs.get('text', '')
    
    class Address:
        def __init__(self):
            self.street = ""
            self.city = ""
            self.postal_code = ""
            self.country = ""
        def set_street(self, v): self.street = v
        def set_city(self, v): self.city = v
        def set_postal_code(self, v): self.postal_code = v
        def set_country(self, v): self.country = v
        def get_street(self): return self.street
        def get_city(self): return self.city
    
    class Attribute:
        def __init__(self):
            self.type = ""
            self.value = ""
        def set_type(self, t): self.type = t
        def set_value(self, v): self.value = v
        def get_value(self): return self.value
    
    class EventRef:
        def __init__(self):
            self.ref_handle = ""
        def set_reference_handle(self, h): self.ref_handle = h
        def get_reference_handle(self): return self.ref_handle
    
    class Url:
        def __init__(self):
            self.path = ""
            self.desc = ""
        def set_path(self, p): self.path = p
        def set_description(self, d): self.desc = d
        def get_path(self): return self.path
        def get_description(self): return self.desc
    
    class NoteRef:
        def __init__(self):
            self.ref_handle = ""
        def set_reference_handle(self, h): self.ref_handle = h
        def get_reference_handle(self): return self.ref_handle
    
    # Create aliases for missing classes
    PersonRef = type('PersonRef', (), {})
    MediaRef = type('MediaRef', (), {})
    SourceRef = type('SourceRef', (), {})
    RepoRef = type('RepoRef', (), {})
    
    USING_REAL_GRAMPS = False

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

class TrueBulletproofTester:
    """Test ACTUAL data integrity - every byte matters in genealogy."""
    
    def __init__(self):
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "critical_failures": [],
            "test_details": defaultdict(dict)
        }
        self.db = None
        
    def setup_database(self):
        """Set up a clean test database."""
        try:
            self.db = PostgreSQLEnhanced()
            
            # Create unique test database
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.test_db_name = f"bulletproof_test_{timestamp}"
            
            # Create database directory for metadata  
            self.test_dir = tempfile.mkdtemp(prefix="gramps_bulletproof_")
            os.makedirs(os.path.join(self.test_dir, ".gramps"), exist_ok=True)
            
            # Write connection settings to file (using expected format)
            settings_file = os.path.join(self.test_dir, "connection_info.txt")
            with open(settings_file, 'w') as f:
                f.write(f"host={DB_CONFIG['host']}\n")
                f.write(f"port={DB_CONFIG['port']}\n")
                f.write(f"user={DB_CONFIG['user']}\n")
                f.write(f"password={DB_CONFIG['password']}\n")
                f.write(f"database_name={self.test_db_name}\n")
                f.write("database_mode=separate\n")
            
            # Load database using directory-based approach
            self.db.load(
                directory=self.test_dir,
                callback=None,
                mode="w",
                username=None,
                password=None
            )
            
            return True
            
        except Exception as e:
            print(f"Database setup failed: {e}")
            traceback.print_exc()
            return False
    
    def calculate_checksum(self, obj):
        """Calculate a checksum for any Gramps object."""
        # Serialize object to ensure exact data preservation
        if hasattr(obj, 'serialize'):
            data = str(obj.serialize()).encode('utf-8')
        else:
            data = pickle.dumps(obj)
        return hashlib.sha256(data).hexdigest()
    
    def test_person_data_integrity(self):
        """Test that Person objects can be stored and retrieved perfectly."""
        test_name = "Person Data Integrity"
        print(f"\n  Testing {test_name}...")
        
        try:
            # Create complex person with all possible attributes
            person = Person()
            person.set_handle("PERSON_INTEGRITY_001")
            person.set_gramps_id("I0001")
            # Use gender constant that works with both real and mock
            male_gender = getattr(Person, 'MALE', 1)
            person.set_gender(male_gender)
            
            # Complex name with unicode
            name = Name()
            name.set_first_name("Björn")
            name.set_suffix("Jr.")
            name.set_title("Dr.")
            
            surname = Surname()
            surname.set_surname("Ö'Malley-Søren")
            surname.set_prefix("van der")
            name.add_surname(surname)
            
            # Add multiple surnames (compound names)
            surname2 = Surname()
            surname2.set_surname("黃")  # Chinese surname
            name.add_surname(surname2)
            
            person.set_primary_name(name)
            
            # Add alternate names (if supported)
            if hasattr(person, 'add_alternate_name'):
                alt_name = Name()
                alt_name.set_first_name("Bob")
                alt_surname = Surname()
                alt_surname.set_surname("O'Malley")
                alt_name.add_surname(alt_surname)
                person.add_alternate_name(alt_name)
            
            # Add birth event
            birth = Event()
            birth.set_handle("EVENT_BIRTH_001")
            # Set birth type (handle both real and mock)
            if hasattr(birth, 'set_type'):
                if hasattr(EventType, 'BIRTH'):
                    birth.set_type(EventType.BIRTH)
                else:
                    birth.set_type('Birth')
            birth.set_description("Born in 北京")
            
            # Complex date (skip if using mocks)
            if USING_REAL_GRAMPS:
                date = Date()
                date.set(
                    quality=Date.QUAL_ESTIMATED,
                    modifier=Date.MOD_ABOUT,
                    calendar=Date.CAL_GREGORIAN,
                    value=(False, 1850, 3, 15, False, 0, 0, 0),
                    text="About March 15, 1850"
                )
                birth.set_date_object(date)
            
            birth_ref = EventRef()
            birth_ref.set_reference_handle(birth.get_handle())
            person.add_event_ref(birth_ref)
            
            # Add addresses (if supported)
            if hasattr(person, 'add_address'):
                addr = Address()
                addr.set_street("123 Ñoño Street, Apt #404")
                addr.set_city("Zürich")
                addr.set_postal_code("8001")
                addr.set_country("Schweiz")
                person.add_address(addr)
            
            # Add URLs (if supported)
            if hasattr(person, 'add_url'):
                url = Url()
                url.set_path("https://example.com/person?id=Björn&test=true")
                url.set_description("Profile with special chars: < > & \" '")
                person.add_url(url)
            
            # Add attributes (if supported)
            if hasattr(person, 'add_attribute'):
                attr = Attribute()
                attr.set_type("Custom")
                attr.set_value("Value with emoji: 😀 🎉 👨‍👩‍👧‍👦")
                person.add_attribute(attr)
            
            # Add notes with special content
            note = Note()
            note.set_handle("NOTE_PERSON_001")
            note.set_text("""
            Multi-line note with special characters:
            • Bullet point (Unicode)
            « French quotes »
            "Smart quotes"
            Em—dash
            Ellipsis…
            Line with trailing spaces    
            	Tab character
            Mathematical: ∑ ∫ √ ∞
            """)
            
            # Calculate checksums BEFORE storage
            person_checksum = self.calculate_checksum(person)
            birth_checksum = self.calculate_checksum(birth)
            note_checksum = self.calculate_checksum(note)
            
            # Store everything
            with DbTxn("Store test person", self.db) as trans:
                self.db.add_event(birth, trans)
                self.db.add_note(note, trans)
                
                # Add note reference if supported
                if hasattr(person, 'add_note_ref'):
                    note_ref = NoteRef()
                    note_ref.set_reference_handle(note.get_handle())
                    person.add_note_ref(note_ref)
                
                self.db.add_person(person, trans)
            
            # Retrieve and verify
            retrieved_person = self.db.get_person_from_handle("PERSON_INTEGRITY_001")
            retrieved_birth = self.db.get_event_from_handle("EVENT_BIRTH_001")
            retrieved_note = self.db.get_note_from_handle("NOTE_PERSON_001")
            
            # Calculate checksums AFTER retrieval
            retrieved_person_checksum = self.calculate_checksum(retrieved_person)
            retrieved_birth_checksum = self.calculate_checksum(retrieved_birth)
            retrieved_note_checksum = self.calculate_checksum(retrieved_note)
            
            # Verify checksums match
            person_match = (person_checksum == retrieved_person_checksum)
            birth_match = (birth_checksum == retrieved_birth_checksum)
            note_match = (note_checksum == retrieved_note_checksum)
            
            # Detailed verification
            name_match = (
                retrieved_person.get_primary_name().get_first_name() == "Björn"
            )
            surname_match = (
                retrieved_person.get_primary_name().get_surname_list()[0].get_surname() 
                == "Ö'Malley-Søren"
            )
            chinese_surname_match = (
                len(retrieved_person.get_primary_name().get_surname_list()) > 1 and
                retrieved_person.get_primary_name().get_surname_list()[1].get_surname() == "黃"
            )
            
            # Verify alternate names preserved
            alt_names = retrieved_person.get_alternate_names()
            alt_name_match = (
                len(alt_names) == 1 and
                alt_names[0].get_first_name() == "Bob"
            )
            
            # Verify address with special chars
            addresses = retrieved_person.get_address_list()
            address_match = (
                len(addresses) == 1 and
                addresses[0].get_street() == "123 Ñoño Street, Apt #404" and
                addresses[0].get_city() == "Zürich"
            )
            
            # Verify URL encoding preserved
            urls = retrieved_person.get_url_list()
            url_match = (
                len(urls) == 1 and
                "Björn" in urls[0].get_path() and
                "< > & \" '" in urls[0].get_description()
            )
            
            # Verify emoji in attributes
            attrs = retrieved_person.get_attribute_list()
            emoji_match = (
                len(attrs) == 1 and
                "😀" in attrs[0].get_value() and
                "👨‍👩‍👧‍👦" in attrs[0].get_value()
            )
            
            all_checks_passed = all([
                person_match, birth_match, note_match,
                name_match, surname_match, chinese_surname_match,
                alt_name_match, address_match, url_match, emoji_match
            ])
            
            if all_checks_passed:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "details": "All data integrity checks passed"
                }
                print(f"    ✓ {test_name} PASSED")
            else:
                self.results["failed"] += 1
                failures = []
                if not person_match: failures.append("Person checksum mismatch")
                if not name_match: failures.append("Name corrupted")
                if not surname_match: failures.append("Surname corrupted")
                if not chinese_surname_match: failures.append("Unicode surname lost")
                if not alt_name_match: failures.append("Alternate names lost")
                if not address_match: failures.append("Address special chars corrupted")
                if not url_match: failures.append("URL encoding corrupted")
                if not emoji_match: failures.append("Emoji data corrupted")
                
                self.results["critical_failures"].append({
                    "test": test_name,
                    "failures": failures
                })
                self.results["test_details"][test_name] = {
                    "status": "FAILED",
                    "failures": failures
                }
                print(f"    ✗ {test_name} FAILED: {', '.join(failures)}")
            
        except Exception as e:
            self.results["failed"] += 1
            self.results["critical_failures"].append({
                "test": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"    ✗ {test_name} CRASHED: {e}")
        
        self.results["total_tests"] += 1
    
    def test_family_relationship_integrity(self):
        """Test complex family relationships including circular references."""
        test_name = "Family Relationship Integrity"
        print(f"\n  Testing {test_name}...")
        
        try:
            # Create complex family structure
            # Grandparents -> Parents -> Children
            # Include remarriage and step-relationships
            
            # Grandparents
            grandfather = Person()
            grandfather.set_handle("GRANDFATHER_001")
            grandfather.set_gramps_id("I1001")
            grandfather.set_gender(Person.MALE)
            
            grandmother = Person()
            grandmother.set_handle("GRANDMOTHER_001")
            grandmother.set_gramps_id("I1002")
            grandmother.set_gender(Person.FEMALE)
            
            # Parents
            father = Person()
            father.set_handle("FATHER_001")
            father.set_gramps_id("I2001")
            father.set_gender(Person.MALE)
            
            mother = Person()
            mother.set_handle("MOTHER_001")
            mother.set_gramps_id("I2002")
            mother.set_gender(Person.FEMALE)
            
            stepmother = Person()
            stepmother.set_handle("STEPMOTHER_001")
            stepmother.set_gramps_id("I2003")
            stepmother.set_gender(Person.FEMALE)
            
            # Children
            child1 = Person()
            child1.set_handle("CHILD_001")
            child1.set_gramps_id("I3001")
            child1.set_gender(Person.FEMALE)
            
            child2 = Person()
            child2.set_handle("CHILD_002")
            child2.set_gramps_id("I3002")
            child2.set_gender(Person.MALE)
            
            stepchild = Person()
            stepchild.set_handle("STEPCHILD_001")
            stepchild.set_gramps_id("I3003")
            stepchild.set_gender(Person.FEMALE)
            
            # Grandparent family
            grandparent_family = Family()
            grandparent_family.set_handle("FAMILY_GP_001")
            grandparent_family.set_gramps_id("F1001")
            grandparent_family.set_father_handle(grandfather.get_handle())
            grandparent_family.set_mother_handle(grandmother.get_handle())
            
            # Add father as child with specific relationship
            child_ref = ChildRef()
            child_ref.set_reference_handle(father.get_handle())
            child_ref.set_father_relation(ChildRef.BIRTH)
            child_ref.set_mother_relation(ChildRef.BIRTH)
            grandparent_family.add_child_ref(child_ref)
            
            # Original parent family
            parent_family = Family()
            parent_family.set_handle("FAMILY_P_001")
            parent_family.set_gramps_id("F2001")
            parent_family.set_father_handle(father.get_handle())
            parent_family.set_mother_handle(mother.get_handle())
            
            # Add children
            child_ref1 = ChildRef()
            child_ref1.set_reference_handle(child1.get_handle())
            child_ref1.set_father_relation(ChildRef.BIRTH)
            child_ref1.set_mother_relation(ChildRef.BIRTH)
            parent_family.add_child_ref(child_ref1)
            
            child_ref2 = ChildRef()
            child_ref2.set_reference_handle(child2.get_handle())
            child_ref2.set_father_relation(ChildRef.BIRTH)
            child_ref2.set_mother_relation(ChildRef.BIRTH)
            parent_family.add_child_ref(child_ref2)
            
            # Remarriage family
            remarriage_family = Family()
            remarriage_family.set_handle("FAMILY_R_001")
            remarriage_family.set_gramps_id("F2002")
            remarriage_family.set_father_handle(father.get_handle())
            remarriage_family.set_mother_handle(stepmother.get_handle())
            
            # Add stepchild
            step_ref = ChildRef()
            step_ref.set_reference_handle(stepchild.get_handle())
            step_ref.set_father_relation(ChildRef.STEPCHILD)
            step_ref.set_mother_relation(ChildRef.BIRTH)
            remarriage_family.add_child_ref(step_ref)
            
            # Also add original children as step-children to new family
            step_ref1 = ChildRef()
            step_ref1.set_reference_handle(child1.get_handle())
            step_ref1.set_father_relation(ChildRef.BIRTH)
            step_ref1.set_mother_relation(ChildRef.STEPCHILD)
            remarriage_family.add_child_ref(step_ref1)
            
            # Calculate checksums before storage
            checksums_before = {
                "grandfather": self.calculate_checksum(grandfather),
                "father": self.calculate_checksum(father),
                "child1": self.calculate_checksum(child1),
                "grandparent_family": self.calculate_checksum(grandparent_family),
                "parent_family": self.calculate_checksum(parent_family),
                "remarriage_family": self.calculate_checksum(remarriage_family)
            }
            
            # Store all objects
            with DbTxn("Store complex family", self.db) as trans:
                # Store all people
                self.db.add_person(grandfather, trans)
                self.db.add_person(grandmother, trans)
                self.db.add_person(father, trans)
                self.db.add_person(mother, trans)
                self.db.add_person(stepmother, trans)
                self.db.add_person(child1, trans)
                self.db.add_person(child2, trans)
                self.db.add_person(stepchild, trans)
                
                # Store families
                self.db.add_family(grandparent_family, trans)
                self.db.add_family(parent_family, trans)
                self.db.add_family(remarriage_family, trans)
            
            # Retrieve and verify
            retrieved_gf = self.db.get_person_from_handle("GRANDFATHER_001")
            retrieved_father = self.db.get_person_from_handle("FATHER_001")
            retrieved_child1 = self.db.get_person_from_handle("CHILD_001")
            retrieved_gp_family = self.db.get_family_from_handle("FAMILY_GP_001")
            retrieved_p_family = self.db.get_family_from_handle("FAMILY_P_001")
            retrieved_r_family = self.db.get_family_from_handle("FAMILY_R_001")
            
            # Calculate checksums after retrieval
            checksums_after = {
                "grandfather": self.calculate_checksum(retrieved_gf),
                "father": self.calculate_checksum(retrieved_father),
                "child1": self.calculate_checksum(retrieved_child1),
                "grandparent_family": self.calculate_checksum(retrieved_gp_family),
                "parent_family": self.calculate_checksum(retrieved_p_family),
                "remarriage_family": self.calculate_checksum(retrieved_r_family)
            }
            
            # Verify all checksums match
            checksum_matches = all(
                checksums_before[key] == checksums_after[key]
                for key in checksums_before
            )
            
            # Verify relationships are preserved
            gp_children = retrieved_gp_family.get_child_ref_list()
            relationship_check1 = (
                len(gp_children) == 1 and
                gp_children[0].get_reference_handle() == "FATHER_001" and
                gp_children[0].get_father_relation() == ChildRef.BIRTH
            )
            
            # Verify remarriage family has correct step relationships
            r_children = retrieved_r_family.get_child_ref_list()
            step_check = False
            for child_ref in r_children:
                if child_ref.get_reference_handle() == "CHILD_001":
                    step_check = (
                        child_ref.get_father_relation() == ChildRef.BIRTH and
                        child_ref.get_mother_relation() == ChildRef.STEPCHILD
                    )
                    break
            
            all_checks = checksum_matches and relationship_check1 and step_check
            
            if all_checks:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "details": "Complex family relationships preserved"
                }
                print(f"    ✓ {test_name} PASSED")
            else:
                self.results["failed"] += 1
                failures = []
                if not checksum_matches: failures.append("Checksum mismatch")
                if not relationship_check1: failures.append("Parent-child relations corrupted")
                if not step_check: failures.append("Step-relationships lost")
                
                self.results["critical_failures"].append({
                    "test": test_name,
                    "failures": failures
                })
                print(f"    ✗ {test_name} FAILED: {', '.join(failures)}")
                
        except Exception as e:
            self.results["failed"] += 1
            self.results["critical_failures"].append({
                "test": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"    ✗ {test_name} CRASHED: {e}")
        
        self.results["total_tests"] += 1
    
    def test_concurrent_access(self):
        """Test multiple threads accessing/modifying data simultaneously."""
        test_name = "Concurrent Access Safety"
        print(f"\n  Testing {test_name}...")
        
        try:
            # Create initial person
            person = Person()
            person.set_handle("CONCURRENT_TEST_001")
            person.set_gramps_id("I9001")
            
            name = Name()
            name.set_first_name("Initial")
            surname = Surname()
            surname.set_surname("Name")
            name.add_surname(surname)
            person.set_primary_name(name)
            
            with DbTxn("Create person for concurrent test", self.db) as trans:
                self.db.add_person(person, trans)
            
            # Track concurrent modifications
            errors = []
            success_count = 0
            
            def concurrent_update(thread_id):
                """Each thread tries to update the person."""
                try:
                    # Retrieve person
                    p = self.db.get_person_from_handle("CONCURRENT_TEST_001")
                    
                    # Modify person
                    name = p.get_primary_name()
                    name.set_first_name(f"Thread{thread_id}")
                    
                    # Add an attribute to track this thread's update
                    attr = Attribute()
                    attr.set_type(f"Thread{thread_id}")
                    attr.set_value(f"Updated at {time.time()}")
                    p.add_attribute(attr)
                    
                    # Save changes
                    with DbTxn(f"Thread {thread_id} update", self.db) as trans:
                        self.db.commit_person(p, trans)
                    
                    return True
                except Exception as e:
                    errors.append(f"Thread {thread_id}: {e}")
                    return False
            
            # Run concurrent updates
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(concurrent_update, i)
                    for i in range(10)
                ]
                results = [f.result() for f in futures]
                success_count = sum(1 for r in results if r)
            
            # Verify final state
            final_person = self.db.get_person_from_handle("CONCURRENT_TEST_001")
            attributes = final_person.get_attribute_list()
            
            # Check that at least some updates succeeded
            concurrent_success = success_count > 0
            
            # Check data integrity after concurrent access
            data_intact = (
                final_person is not None and
                final_person.get_handle() == "CONCURRENT_TEST_001" and
                len(attributes) > 0  # At least one thread succeeded
            )
            
            if concurrent_success and data_intact:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "details": f"{success_count}/10 concurrent updates succeeded"
                }
                print(f"    ✓ {test_name} PASSED ({success_count}/10 succeeded)")
            else:
                self.results["failed"] += 1
                self.results["critical_failures"].append({
                    "test": test_name,
                    "errors": errors,
                    "success_count": success_count
                })
                print(f"    ✗ {test_name} FAILED: Only {success_count}/10 succeeded")
                
        except Exception as e:
            self.results["failed"] += 1
            self.results["critical_failures"].append({
                "test": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"    ✗ {test_name} CRASHED: {e}")
        
        self.results["total_tests"] += 1
    
    def test_transaction_rollback(self):
        """Test that failed transactions don't corrupt data."""
        test_name = "Transaction Rollback Safety"
        print(f"\n  Testing {test_name}...")
        
        try:
            # Create initial state
            person1 = Person()
            person1.set_handle("ROLLBACK_TEST_001")
            person1.set_gramps_id("I8001")
            
            with DbTxn("Create initial person", self.db) as trans:
                self.db.add_person(person1, trans)
            
            # Get initial count
            initial_count = self.db.get_number_of_people()
            
            # Try a transaction that will fail
            try:
                with DbTxn("Failing transaction", self.db) as trans:
                    # Add a valid person
                    person2 = Person()
                    person2.set_handle("ROLLBACK_TEST_002")
                    person2.set_gramps_id("I8002")
                    self.db.add_person(person2, trans)
                    
                    # Force an error by adding duplicate handle
                    person3 = Person()
                    person3.set_handle("ROLLBACK_TEST_001")  # Duplicate!
                    person3.set_gramps_id("I8003")
                    self.db.add_person(person3, trans)
                    
                    # This should fail and rollback
                    
            except Exception:
                # Expected to fail
                pass
            
            # Verify rollback worked
            final_count = self.db.get_number_of_people()
            
            # Person2 should NOT exist
            try:
                should_not_exist = self.db.get_person_from_handle("ROLLBACK_TEST_002")
                person2_rolled_back = (should_not_exist is None)
            except:
                person2_rolled_back = True
            
            # Original person should still exist unchanged
            original_intact = self.db.get_person_from_handle("ROLLBACK_TEST_001")
            
            rollback_worked = (
                final_count == initial_count and
                person2_rolled_back and
                original_intact is not None
            )
            
            if rollback_worked:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "details": "Transaction rollback preserved data integrity"
                }
                print(f"    ✓ {test_name} PASSED")
            else:
                self.results["failed"] += 1
                self.results["critical_failures"].append({
                    "test": test_name,
                    "failure": "Rollback did not preserve data integrity"
                })
                print(f"    ✗ {test_name} FAILED: Rollback incomplete")
                
        except Exception as e:
            self.results["failed"] += 1
            self.results["critical_failures"].append({
                "test": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"    ✗ {test_name} CRASHED: {e}")
        
        self.results["total_tests"] += 1
    
    def test_large_dataset_performance(self):
        """Test with a large genealogical dataset."""
        test_name = "Large Dataset Performance"
        print(f"\n  Testing {test_name}...")
        
        try:
            num_people = 1000  # Start with 1000, can increase
            num_families = 400
            
            print(f"    Creating {num_people} people and {num_families} families...")
            
            start_time = time.time()
            people_handles = []
            
            # Create people
            with DbTxn("Add large dataset", self.db) as trans:
                for i in range(num_people):
                    person = Person()
                    handle = f"LARGE_{i:06d}"
                    person.set_handle(handle)
                    person.set_gramps_id(f"I{i:06d}")
                    person.set_gender(Person.MALE if i % 2 == 0 else Person.FEMALE)
                    
                    name = Name()
                    name.set_first_name(f"Person{i}")
                    surname = Surname()
                    surname.set_surname(f"Family{i % 100}")  # 100 family names
                    name.add_surname(surname)
                    person.set_primary_name(name)
                    
                    self.db.add_person(person, trans)
                    people_handles.append(handle)
                
                # Create families linking people
                for i in range(num_families):
                    family = Family()
                    family.set_handle(f"FAM_{i:06d}")
                    family.set_gramps_id(f"F{i:06d}")
                    
                    # Link parents
                    if i * 2 < len(people_handles):
                        family.set_father_handle(people_handles[i * 2])
                    if i * 2 + 1 < len(people_handles):
                        family.set_mother_handle(people_handles[i * 2 + 1])
                    
                    # Add some children
                    for j in range(min(3, len(people_handles) - (i * 2 + 2))):
                        child_ref = ChildRef()
                        child_ref.set_reference_handle(people_handles[i * 2 + 2 + j])
                        family.add_child_ref(child_ref)
                    
                    self.db.add_family(family, trans)
            
            creation_time = time.time() - start_time
            
            # Test retrieval performance
            retrieval_start = time.time()
            
            # Random access test
            for _ in range(100):
                random_handle = random.choice(people_handles)
                person = self.db.get_person_from_handle(random_handle)
                if person is None:
                    raise ValueError(f"Lost person {random_handle}")
            
            retrieval_time = time.time() - retrieval_start
            
            # Test iteration performance
            iteration_start = time.time()
            count = 0
            for person in self.db.iter_people():
                count += 1
            iteration_time = time.time() - iteration_start
            
            # Performance checks
            performance_ok = (
                creation_time < 60 and  # Should create 1000 people in < 1 minute
                retrieval_time < 1 and  # 100 random retrievals in < 1 second
                iteration_time < 10 and  # Iterate all in < 10 seconds
                count == num_people  # All people retrievable
            )
            
            if performance_ok:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "creation_time": f"{creation_time:.2f}s",
                    "retrieval_time": f"{retrieval_time:.2f}s",
                    "iteration_time": f"{iteration_time:.2f}s"
                }
                print(f"    ✓ {test_name} PASSED (create:{creation_time:.2f}s, retrieve:{retrieval_time:.2f}s)")
            else:
                self.results["failed"] += 1
                self.results["critical_failures"].append({
                    "test": test_name,
                    "creation_time": creation_time,
                    "retrieval_time": retrieval_time,
                    "iteration_time": iteration_time,
                    "count_mismatch": count != num_people
                })
                print(f"    ✗ {test_name} FAILED: Performance issues or data loss")
                
        except Exception as e:
            self.results["failed"] += 1
            self.results["critical_failures"].append({
                "test": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"    ✗ {test_name} CRASHED: {e}")
        
        self.results["total_tests"] += 1
    
    def test_edge_cases(self):
        """Test extreme edge cases that could break the database."""
        test_name = "Edge Cases and Boundary Conditions"
        print(f"\n  Testing {test_name}...")
        
        edge_case_results = []
        
        # Test 1: Empty strings and None values
        try:
            person = Person()
            person.set_handle("EDGE_EMPTY_001")
            person.set_gramps_id("")  # Empty gramps_id
            
            name = Name()
            name.set_first_name("")  # Empty name
            surname = Surname()
            surname.set_surname("")  # Empty surname
            name.add_surname(surname)
            person.set_primary_name(name)
            
            with DbTxn("Empty values test", self.db) as trans:
                self.db.add_person(person, trans)
            
            retrieved = self.db.get_person_from_handle("EDGE_EMPTY_001")
            empty_test_passed = (retrieved is not None)
            edge_case_results.append(("Empty values", empty_test_passed))
        except Exception as e:
            edge_case_results.append(("Empty values", False, str(e)))
        
        # Test 2: Maximum length strings
        try:
            person = Person()
            person.set_handle("EDGE_MAXLEN_001")
            person.set_gramps_id("I" + "9" * 100)  # Very long ID
            
            name = Name()
            # 10,000 character name
            name.set_first_name("A" * 10000)
            surname = Surname()
            surname.set_surname("B" * 10000)
            name.add_surname(surname)
            person.set_primary_name(name)
            
            # Huge note
            note = Note()
            note.set_handle("EDGE_NOTE_001")
            note.set_text("X" * 1000000)  # 1MB of text
            
            with DbTxn("Max length test", self.db) as trans:
                self.db.add_note(note, trans)
                self.db.add_person(person, trans)
            
            retrieved = self.db.get_person_from_handle("EDGE_MAXLEN_001")
            retrieved_note = self.db.get_note_from_handle("EDGE_NOTE_001")
            
            maxlen_test_passed = (
                retrieved is not None and
                len(retrieved.get_primary_name().get_first_name()) == 10000 and
                retrieved_note is not None and
                len(retrieved_note.get_text()) == 1000000
            )
            edge_case_results.append(("Maximum length", maxlen_test_passed))
        except Exception as e:
            edge_case_results.append(("Maximum length", False, str(e)))
        
        # Test 3: Special characters in all fields
        try:
            person = Person()
            person.set_handle("EDGE_SPECIAL_001")
            person.set_gramps_id("I!@#$%^&*()")
            
            name = Name()
            name.set_first_name("'; DROP TABLE persons; --")  # SQL injection attempt
            surname = Surname()
            surname.set_surname("<script>alert('XSS')</script>")  # XSS attempt
            name.add_surname(surname)
            person.set_primary_name(name)
            
            with DbTxn("Special chars test", self.db) as trans:
                self.db.add_person(person, trans)
            
            retrieved = self.db.get_person_from_handle("EDGE_SPECIAL_001")
            special_test_passed = (
                retrieved is not None and
                "DROP TABLE" in retrieved.get_primary_name().get_first_name() and
                "<script>" in retrieved.get_primary_name().get_surname()
            )
            edge_case_results.append(("SQL injection / XSS protection", special_test_passed))
        except Exception as e:
            edge_case_results.append(("SQL injection / XSS protection", False, str(e)))
        
        # Test 4: Circular family references
        try:
            # Person is their own parent (genealogical impossibility)
            person = Person()
            person.set_handle("EDGE_CIRCULAR_001")
            person.set_gramps_id("I7001")
            
            family = Family()
            family.set_handle("EDGE_CIRCULAR_FAM_001")
            family.set_gramps_id("F7001")
            family.set_father_handle("EDGE_CIRCULAR_001")  # Same person
            
            child_ref = ChildRef()
            child_ref.set_reference_handle("EDGE_CIRCULAR_001")  # Is own child
            family.add_child_ref(child_ref)
            
            with DbTxn("Circular reference test", self.db) as trans:
                self.db.add_person(person, trans)
                self.db.add_family(family, trans)
            
            retrieved_fam = self.db.get_family_from_handle("EDGE_CIRCULAR_FAM_001")
            circular_test_passed = (
                retrieved_fam is not None and
                retrieved_fam.get_father_handle() == "EDGE_CIRCULAR_001" and
                len(retrieved_fam.get_child_ref_list()) == 1
            )
            edge_case_results.append(("Circular references", circular_test_passed))
        except Exception as e:
            edge_case_results.append(("Circular references", False, str(e)))
        
        # Test 5: Null bytes and control characters
        try:
            person = Person()
            person.set_handle("EDGE_NULL_001")
            person.set_gramps_id("I6001")
            
            name = Name()
            name.set_first_name("Test\x00Null")  # Null byte
            surname = Surname()
            surname.set_surname("Tab\tNew\nCarriage\r")  # Control chars
            name.add_surname(surname)
            person.set_primary_name(name)
            
            with DbTxn("Null byte test", self.db) as trans:
                self.db.add_person(person, trans)
            
            retrieved = self.db.get_person_from_handle("EDGE_NULL_001")
            null_test_passed = (retrieved is not None)
            edge_case_results.append(("Null bytes/control chars", null_test_passed))
        except Exception as e:
            edge_case_results.append(("Null bytes/control chars", False, str(e)))
        
        # Evaluate overall edge case results
        total_edge_tests = len(edge_case_results)
        passed_edge_tests = sum(1 for _, passed, *_ in edge_case_results if passed)
        
        if passed_edge_tests == total_edge_tests:
            self.results["passed"] += 1
            self.results["test_details"][test_name] = {
                "status": "PASSED",
                "details": f"All {total_edge_tests} edge cases handled correctly"
            }
            print(f"    ✓ {test_name} PASSED ({passed_edge_tests}/{total_edge_tests})")
        else:
            self.results["failed"] += 1
            failures = [
                name for name, passed, *error in edge_case_results 
                if not passed
            ]
            self.results["critical_failures"].append({
                "test": test_name,
                "failed_cases": failures,
                "details": edge_case_results
            })
            print(f"    ✗ {test_name} FAILED ({passed_edge_tests}/{total_edge_tests})")
            for name, passed, *error in edge_case_results:
                if not passed:
                    error_msg = error[0] if error else "Unknown error"
                    print(f"      - {name}: {error_msg}")
        
        self.results["total_tests"] += 1
    
    def cleanup(self):
        """Clean up test database."""
        try:
            if self.db and self.db.is_open():
                self.db.close()
            
            # Drop test database
            # Note: Would need admin connection to drop database
            
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def run_all_tests(self):
        """Run the complete TRUE bulletproof test suite."""
        print("\n" + "=" * 80)
        print("TRUE BULLETPROOF DATA INTEGRITY TEST SUITE")
        print("Testing ACTUAL data storage, retrieval, and integrity")
        print("=" * 80)
        
        # Setup database
        print("\nSetting up test database...")
        if not self.setup_database():
            print("❌ Failed to setup database - cannot proceed")
            return
        
        print("\nRunning comprehensive data integrity tests...")
        
        # Run all test categories
        self.test_person_data_integrity()
        self.test_family_relationship_integrity()
        self.test_concurrent_access()
        self.test_transaction_rollback()
        self.test_large_dataset_performance()
        self.test_edge_cases()
        
        # Calculate reliability
        reliability = (
            (self.results["passed"] / self.results["total_tests"] * 100)
            if self.results["total_tests"] > 0 else 0
        )
        
        # Generate report
        print("\n" + "=" * 80)
        print("TRUE BULLETPROOF TEST RESULTS")
        print("=" * 80)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Data Integrity Reliability: {reliability:.2f}%")
        
        if reliability == 100:
            print("\n✅ TRULY BULLETPROOF - Data integrity verified at every level")
        elif reliability >= 95:
            print("\n⚠️ MOSTLY RELIABLE - Critical issues remain")
        else:
            print("\n❌ NOT BULLETPROOF - Serious data integrity problems detected")
        
        if self.results["critical_failures"]:
            print("\nCRITICAL FAILURES DETECTED:")
            for failure in self.results["critical_failures"]:
                print(f"\n  • {failure['test']}:")
                if 'error' in failure:
                    print(f"    Error: {failure['error']}")
                if 'failures' in failure:
                    for f in failure['failures']:
                        print(f"    - {f}")
        
        # Cleanup
        self.cleanup()
        
        # Save detailed report
        report_file = f"TRUE_BULLETPROOF_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nDetailed report saved: {report_file}")
        
        return reliability == 100

if __name__ == "__main__":
    tester = TrueBulletproofTester()
    is_bulletproof = tester.run_all_tests()
    
    sys.exit(0 if is_bulletproof else 1)