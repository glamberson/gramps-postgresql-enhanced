#!/usr/bin/env python3
"""
REAL GRAMPS DATA INTEGRITY TEST SUITE
======================================
Tests with ACTUAL Gramps objects against the REAL PostgreSQL server.
No mocks, no shortcuts - real genealogical data integrity validation.
"""

import os
import sys
import json
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

# Add Gramps to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Import REAL Gramps objects
from gramps.gen.lib import (
    Person, Name, Surname, Family, Event, Place, PlaceName,
    Source, Citation, Repository, Media, Note, Tag, 
    Date, Address, Attribute, EventRef, EventType, 
    ChildRef, PersonRef, Url, MediaRef, RepoRef, PlaceRef, PlaceType
)
# NoteRef doesn't exist, use handle directly for note references
from gramps.gen.db import DbTxn
from gramps.gen.lib.serialize import JSONSerializer

# Add plugin directory to Python path for our PostgreSQL Enhanced addon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from postgresqlenhanced import PostgreSQLEnhanced

# Real database configuration - using actual server
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

class RealGrampsDataIntegrityTester:
    """Test REAL data integrity with actual Gramps objects."""
    
    def __init__(self):
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "critical_failures": [],
            "test_details": defaultdict(dict)
        }
        self.db = None
        self.test_db_name = None
        
    def setup_database(self):
        """Set up a clean test database on the real server."""
        try:
            self.db = PostgreSQLEnhanced()
            
            # Create unique test database name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.test_db_name = f"gramps_real_test_{timestamp}"
            
            # Create database directory for metadata
            self.test_dir = tempfile.mkdtemp(prefix="gramps_real_test_")
            
            # Write connection settings for remote server
            settings_file = os.path.join(self.test_dir, "connection_info.txt")
            with open(settings_file, 'w') as f:
                f.write(f"host={DB_CONFIG['host']}\n")
                f.write(f"port={DB_CONFIG['port']}\n")
                f.write(f"user={DB_CONFIG['user']}\n")
                f.write(f"password={DB_CONFIG['password']}\n")
                f.write(f"database_name={self.test_db_name}\n")
                f.write("database_mode=separate\n")
            
            print(f"  Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            print(f"  Creating test database: {self.test_db_name}")
            
            # Load database
            self.db.load(
                directory=self.test_dir,
                callback=None,
                mode="w",
                username=None,
                password=None
            )
            
            print(f"  ✓ Database connected and ready")
            return True
            
        except Exception as e:
            print(f"  ✗ Database setup failed: {e}")
            traceback.print_exc()
            return False
    
    def calculate_data_checksum(self, obj):
        """Calculate checksum for any Gramps object using its serialization."""
        try:
            # Use Gramps native serialization
            if hasattr(obj, 'serialize'):
                # Serialize to get the raw data structure
                serialized = obj.serialize()
                # Convert to stable JSON string for hashing
                json_str = json.dumps(serialized, sort_keys=True)
                return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
            else:
                # Fallback for objects without serialize
                return hashlib.sha256(str(obj).encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"    Warning: Checksum calculation failed: {e}")
            return None
    
    def test_person_complete_data_integrity(self):
        """Test that complex Person objects preserve EVERY field perfectly."""
        test_name = "Person Complete Data Integrity"
        print(f"\n  Testing {test_name}...")
        
        try:
            # Create a FULLY populated person with all possible fields
            person = Person()
            person.set_handle("PERSON_COMPLETE_001")
            person.set_gramps_id("I0001")
            person.set_gender(Person.MALE)
            
            # Primary name with all fields
            name = Name()
            name.set_first_name("Björn")
            name.set_suffix("Jr.")
            name.set_title("Dr.")
            name.set_nick("Benny")
            name.set_call_name("Ben")
            name.set_family_nick("The Vikings")
            
            # Multiple surnames with different origins
            surname1 = Surname()
            surname1.set_surname("Ö'Malley-Søren")
            surname1.set_prefix("van der")
            surname1.set_primary(True)
            name.add_surname(surname1)
            
            surname2 = Surname()
            surname2.set_surname("黃")  # Chinese surname
            surname2.set_origintype("Patrilineal")
            name.add_surname(surname2)
            
            surname3 = Surname()
            surname3.set_surname("Müller")  # German umlaut
            surname3.set_connector("von")
            name.add_surname(surname3)
            
            person.set_primary_name(name)
            
            # Add alternate names
            alt_name1 = Name()
            alt_name1.set_first_name("Robert")
            alt_name1.set_type("Birth Name")
            alt_surname = Surname()
            alt_surname.set_surname("O'Malley")
            alt_name1.add_surname(alt_surname)
            person.add_alternate_name(alt_name1)
            
            alt_name2 = Name()
            alt_name2.set_first_name("Роберт")  # Cyrillic
            alt_surname2 = Surname()
            alt_surname2.set_surname("О'Мэлли")
            alt_name2.add_surname(alt_surname2)
            person.add_alternate_name(alt_name2)
            
            # Birth event with full details
            birth = Event()
            birth.set_handle("EVENT_BIRTH_001")
            birth.set_gramps_id("E0001")
            birth.set_type(EventType.BIRTH)
            birth.set_description("Born during a thunderstorm in 北京 (Beijing)")
            
            # Complex date
            date = Date()
            date.set(
                quality=Date.QUAL_ESTIMATED,
                modifier=Date.MOD_ABOUT,
                calendar=Date.CAL_GREGORIAN,
                value=(0, 1850, 3, 15, False),
                text="About March 15, 1850"
            )
            birth.set_date_object(date)
            
            # Place with hierarchy
            place = Place()
            place.set_handle("PLACE_BIRTH_001")
            place.set_gramps_id("P0001")
            place.set_title("St. Mary's Hospital")
            
            place_name = PlaceName()
            place_name.set_value("St. Mary's Hospital, Beijing, China")
            place.set_name(place_name)
            
            place.set_longitude("116.4074")
            place.set_latitude("39.9042")
            
            birth.set_place_handle(place.get_handle())
            
            birth_ref = EventRef()
            birth_ref.set_reference_handle(birth.get_handle())
            birth_ref.set_role("Primary")
            person.add_event_ref(birth_ref)
            
            # Death event
            death = Event()
            death.set_handle("EVENT_DEATH_001")
            death.set_gramps_id("E0002")
            death.set_type(EventType.DEATH)
            death.set_description("Died peacefully")
            
            death_date = Date()
            death_date.set(
                quality=Date.QUAL_NONE,
                modifier=Date.MOD_NONE,
                calendar=Date.CAL_GREGORIAN,
                value=(0, 1925, 12, 25, False),
                text="December 25, 1925"
            )
            death.set_date_object(death_date)
            
            death_ref = EventRef()
            death_ref.set_reference_handle(death.get_handle())
            person.add_event_ref(death_ref)
            
            # Multiple addresses
            addr1 = Address()
            addr1.set_street("123 Ñoño Street, Apt #404")
            addr1.set_locality("Old Town")
            addr1.set_city("Zürich")
            addr1.set_county("Zürich")
            addr1.set_state("ZH")
            addr1.set_postal_code("8001")
            addr1.set_country("Schweiz")
            addr1.set_phone("+41 44 123 4567")
            
            addr_date = Date()
            addr_date.set(
                quality=Date.QUAL_NONE,
                modifier=Date.MOD_NONE,
                calendar=Date.CAL_GREGORIAN,
                value=(0, 1870, 1, 1, False)
            )
            addr1.set_date_object(addr_date)
            person.add_address(addr1)
            
            addr2 = Address()
            addr2.set_street("東京都渋谷区")  # Japanese address
            addr2.set_city("Tokyo")
            addr2.set_country("日本")
            person.add_address(addr2)
            
            # URLs with various special characters
            url1 = Url()
            url1.set_path("https://example.com/person?id=Björn&test=true&char=<>&\"'")
            url1.set_description("Profile with <special> & \"quoted\" 'chars'")
            url1.set_type("Website")
            person.add_url(url1)
            
            url2 = Url()
            url2.set_path("https://例え.jp/人物/björn")  # International domain
            url2.set_description("日本語 profile")
            person.add_url(url2)
            
            # Attributes with various data types
            attr1 = Attribute()
            attr1.set_type("Height")
            attr1.set_value("6'2\" (188cm)")
            person.add_attribute(attr1)
            
            attr2 = Attribute()
            attr2.set_type("DNA")
            attr2.set_value("Haplogroup: R1b-M269; mtDNA: H1a1")
            person.add_attribute(attr2)
            
            attr3 = Attribute()
            attr3.set_type("Emoji Test")
            attr3.set_value("😀 🎉 👨‍👩‍👧‍👦 🇨🇭 🏴󐁧󐁢󐁳󐁣󐁴󐁿")
            person.add_attribute(attr3)
            
            # LDS ordinances (if person was LDS)
            person.add_lds_ord("Baptism")
            person.add_lds_ord("Endowment")
            
            # Notes with complex formatting
            note1 = Note()
            note1.set_handle("NOTE_PERSON_001")
            note1.set_gramps_id("N0001")
            note1.set_type("General")
            note1.set_format(True)  # Formatted text
            note1.set_text("""
Multi-line note with special characters and formatting:
• Bullet point (Unicode U+2022)
« French quotes » and "smart quotes"
Em—dash and en–dash
Ellipsis… and math: ∑ ∫ √ ∞ π ≠ ≈
Line with trailing spaces    
	Tab character and 　full-width space
Hebrew: שלום  Arabic: السلام عليكم
Emoji: 🌍 🚀 💻 🧬
Control chars: \r\n\t\v
            """)
            
            # Add note directly by handle
            person.add_note(note1.get_handle())
            
            # Tags
            tag1 = Tag()
            tag1.set_handle("TAG_001")
            tag1.set_name("VIP")
            tag1.set_color("#FF0000")
            tag1.set_priority(1)
            
            tag2 = Tag()
            tag2.set_handle("TAG_002")
            tag2.set_name("DNA Tested")
            tag2.set_color("#00FF00")
            
            person.add_tag(tag1.get_handle())
            person.add_tag(tag2.get_handle())
            
            # Citations and sources
            source = Source()
            source.set_handle("SOURCE_001")
            source.set_gramps_id("S0001")
            source.set_title("1850 Census of Beijing")
            source.set_author("Imperial Census Bureau")
            source.set_pubinfo("Published 1851, Beijing")
            source.set_abbrev("1850 Census")
            
            citation = Citation()
            citation.set_handle("CITATION_001")
            citation.set_gramps_id("C0001")
            citation.set_reference_handle(source.get_handle())
            citation.set_page("Page 42, Line 7")
            citation.set_confidence_level(Citation.CONF_VERY_HIGH)
            
            citation_date = Date()
            citation_date.set(
                quality=Date.QUAL_NONE,
                modifier=Date.MOD_NONE,
                calendar=Date.CAL_GREGORIAN,
                value=(0, 2024, 1, 15, False)
            )
            citation.set_date_object(citation_date)
            
            person.add_citation(citation.get_handle())
            
            # Media
            media = Media()
            media.set_handle("MEDIA_001")
            media.set_gramps_id("O0001")
            media.set_path("/photos/björn_portrait.jpg")
            media.set_mime_type("image/jpeg")
            media.set_description("Portrait of Björn")
            
            media_ref = MediaRef()
            media_ref.set_reference_handle(media.get_handle())
            media_ref.set_rectangle((10, 20, 100, 150))  # Face region
            person.add_media_reference(media_ref)
            
            # Person references (associations)
            person_ref = PersonRef()
            person_ref.set_reference_handle("PERSON_FRIEND_001")
            person_ref.set_relation("Friend")
            person.add_person_ref(person_ref)
            
            # Calculate checksums BEFORE storage
            checksums_before = {
                "person": self.calculate_data_checksum(person),
                "birth": self.calculate_data_checksum(birth),
                "death": self.calculate_data_checksum(death),
                "place": self.calculate_data_checksum(place),
                "note": self.calculate_data_checksum(note1),
                "source": self.calculate_data_checksum(source),
                "citation": self.calculate_data_checksum(citation),
                "media": self.calculate_data_checksum(media),
                "tag1": self.calculate_data_checksum(tag1),
                "tag2": self.calculate_data_checksum(tag2)
            }
            
            # Store everything in database
            with DbTxn("Store complete person test data", self.db) as trans:
                self.db.add_place(place, trans)
                self.db.add_event(birth, trans)
                self.db.add_event(death, trans)
                self.db.add_note(note1, trans)
                self.db.add_source(source, trans)
                self.db.add_citation(citation, trans)
                self.db.add_media(media, trans)
                self.db.add_tag(tag1, trans)
                self.db.add_tag(tag2, trans)
                self.db.add_person(person, trans)
            
            # Retrieve everything from database
            retrieved_person = self.db.get_person_from_handle("PERSON_COMPLETE_001")
            retrieved_birth = self.db.get_event_from_handle("EVENT_BIRTH_001")
            retrieved_death = self.db.get_event_from_handle("EVENT_DEATH_001")
            retrieved_place = self.db.get_place_from_handle("PLACE_BIRTH_001")
            retrieved_note = self.db.get_note_from_handle("NOTE_PERSON_001")
            retrieved_source = self.db.get_source_from_handle("SOURCE_001")
            retrieved_citation = self.db.get_citation_from_handle("CITATION_001")
            retrieved_media = self.db.get_media_from_handle("MEDIA_001")
            retrieved_tag1 = self.db.get_tag_from_handle("TAG_001")
            retrieved_tag2 = self.db.get_tag_from_handle("TAG_002")
            
            # Calculate checksums AFTER retrieval
            checksums_after = {
                "person": self.calculate_data_checksum(retrieved_person),
                "birth": self.calculate_data_checksum(retrieved_birth),
                "death": self.calculate_data_checksum(retrieved_death),
                "place": self.calculate_data_checksum(retrieved_place),
                "note": self.calculate_data_checksum(retrieved_note),
                "source": self.calculate_data_checksum(retrieved_source),
                "citation": self.calculate_data_checksum(retrieved_citation),
                "media": self.calculate_data_checksum(retrieved_media),
                "tag1": self.calculate_data_checksum(retrieved_tag1),
                "tag2": self.calculate_data_checksum(retrieved_tag2)
            }
            
            # Verify ALL checksums match
            all_checksums_match = all(
                checksums_before[key] == checksums_after[key]
                for key in checksums_before
                if checksums_before[key] is not None
            )
            
            # Detailed field verification
            name_checks = [
                retrieved_person.get_primary_name().get_first_name() == "Björn",
                retrieved_person.get_primary_name().get_suffix() == "Jr.",
                retrieved_person.get_primary_name().get_title() == "Dr.",
                retrieved_person.get_primary_name().get_nick() == "Benny",
                retrieved_person.get_primary_name().get_call_name() == "Ben",
            ]
            
            # Check all three surnames preserved
            surnames = retrieved_person.get_primary_name().get_surname_list()
            surname_checks = [
                len(surnames) == 3,
                surnames[0].get_surname() == "Ö'Malley-Søren" if len(surnames) > 0 else False,
                surnames[1].get_surname() == "黃" if len(surnames) > 1 else False,
                surnames[2].get_surname() == "Müller" if len(surnames) > 2 else False,
            ]
            
            # Check alternate names
            alt_names = retrieved_person.get_alternate_names()
            alt_name_checks = [
                len(alt_names) == 2,
                alt_names[0].get_first_name() == "Robert" if len(alt_names) > 0 else False,
                alt_names[1].get_first_name() == "Роберт" if len(alt_names) > 1 else False,
            ]
            
            # Check addresses
            addresses = retrieved_person.get_address_list()
            address_checks = [
                len(addresses) == 2,
                addresses[0].get_street() == "123 Ñoño Street, Apt #404" if len(addresses) > 0 else False,
                addresses[0].get_city() == "Zürich" if len(addresses) > 0 else False,
                addresses[1].get_street() == "東京都渋谷区" if len(addresses) > 1 else False,
            ]
            
            # Check URLs
            urls = retrieved_person.get_url_list()
            url_checks = [
                len(urls) == 2,
                "Björn" in urls[0].get_path() if len(urls) > 0 else False,
                "<special>" in urls[0].get_description() if len(urls) > 0 else False,
                "例え.jp" in urls[1].get_path() if len(urls) > 1 else False,
            ]
            
            # Check attributes including emoji
            attributes = retrieved_person.get_attribute_list()
            attr_checks = [
                len(attributes) == 3,
                any(a.get_value() == "6'2\" (188cm)" for a in attributes),
                any("R1b-M269" in a.get_value() for a in attributes),
                any("😀" in a.get_value() for a in attributes),
            ]
            
            # Check note text preservation
            note_text = retrieved_note.get_text() if retrieved_note else ""
            note_checks = [
                "• Bullet point" in note_text,
                "« French quotes »" in note_text,
                "∑ ∫ √ ∞" in note_text,
                "שלום" in note_text,  # Hebrew
                "السلام عليكم" in note_text,  # Arabic
                "🌍 🚀 💻 🧬" in note_text,  # Emoji
            ]
            
            # Check tags
            tag_handles = retrieved_person.get_tag_list()
            tag_checks = [
                len(tag_handles) == 2,
                "TAG_001" in tag_handles,
                "TAG_002" in tag_handles,
                retrieved_tag1.get_name() == "VIP" if retrieved_tag1 else False,
                retrieved_tag2.get_color() == "#00FF00" if retrieved_tag2 else False,
            ]
            
            # All checks
            all_checks = (
                all_checksums_match and
                all(name_checks) and
                all(surname_checks) and
                all(alt_name_checks) and
                all(address_checks) and
                all(url_checks) and
                all(attr_checks) and
                all(note_checks) and
                all(tag_checks)
            )
            
            if all_checks:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "details": "All person data preserved perfectly"
                }
                print(f"    ✓ {test_name} PASSED - Every byte preserved")
            else:
                self.results["failed"] += 1
                failures = []
                if not all_checksums_match:
                    for key in checksums_before:
                        if checksums_before[key] != checksums_after[key]:
                            failures.append(f"Checksum mismatch: {key}")
                if not all(name_checks): failures.append("Name fields corrupted")
                if not all(surname_checks): failures.append("Surnames lost or corrupted")
                if not all(alt_name_checks): failures.append("Alternate names corrupted")
                if not all(address_checks): failures.append("Address data corrupted")
                if not all(url_checks): failures.append("URL data corrupted")
                if not all(attr_checks): failures.append("Attributes corrupted")
                if not all(note_checks): failures.append("Note text corrupted")
                if not all(tag_checks): failures.append("Tags corrupted")
                
                self.results["critical_failures"].append({
                    "test": test_name,
                    "failures": failures
                })
                print(f"    ✗ {test_name} FAILED")
                for failure in failures:
                    print(f"      - {failure}")
                
        except Exception as e:
            self.results["failed"] += 1
            self.results["critical_failures"].append({
                "test": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"    ✗ {test_name} CRASHED: {e}")
            
        self.results["total_tests"] += 1
    
    def test_complex_family_relationships(self):
        """Test complex multi-generational family structures."""
        test_name = "Complex Family Relationships"
        print(f"\n  Testing {test_name}...")
        
        try:
            # Create 4 generation family tree
            people = {}
            families = {}
            
            # Great-grandparents
            for i, (handle, name) in enumerate([
                ("GGF1", "Wilhelm"), ("GGM1", "Anna"),
                ("GGF2", "James"), ("GGM2", "Mary")
            ]):
                p = Person()
                p.set_handle(handle)
                p.set_gramps_id(f"I{i:04d}")
                p.set_gender(Person.MALE if "F" in handle else Person.FEMALE)
                n = Name()
                n.set_first_name(name)
                s = Surname()
                s.set_surname(f"Family{i//2}")
                n.add_surname(s)
                p.set_primary_name(n)
                people[handle] = p
            
            # Grandparents
            for i, (handle, name) in enumerate([
                ("GF1", "Hans"), ("GM1", "Emma"),
                ("GF2", "Robert"), ("GM2", "Sarah")
            ], start=4):
                p = Person()
                p.set_handle(handle)
                p.set_gramps_id(f"I{i:04d}")
                p.set_gender(Person.MALE if "F" in handle else Person.FEMALE)
                n = Name()
                n.set_first_name(name)
                s = Surname()
                s.set_surname(f"Family{i//2}")
                n.add_surname(s)
                p.set_primary_name(n)
                people[handle] = p
            
            # Parents
            father = Person()
            father.set_handle("FATHER")
            father.set_gramps_id("I0008")
            father.set_gender(Person.MALE)
            n = Name()
            n.set_first_name("John")
            s = Surname()
            s.set_surname("Smith")
            n.add_surname(s)
            father.set_primary_name(n)
            people["FATHER"] = father
            
            mother = Person()
            mother.set_handle("MOTHER")
            mother.set_gramps_id("I0009")
            mother.set_gender(Person.FEMALE)
            n = Name()
            n.set_first_name("Jane")
            s = Surname()
            s.set_surname("Doe")
            n.add_surname(s)
            mother.set_primary_name(n)
            people["MOTHER"] = mother
            
            # Step-parent (father remarries)
            stepmother = Person()
            stepmother.set_handle("STEPMOTHER")
            stepmother.set_gramps_id("I0010")
            stepmother.set_gender(Person.FEMALE)
            n = Name()
            n.set_first_name("Susan")
            s = Surname()
            s.set_surname("Johnson")
            n.add_surname(s)
            stepmother.set_primary_name(n)
            people["STEPMOTHER"] = stepmother
            
            # Children
            for i, (handle, name) in enumerate([
                ("CHILD1", "Alice"), ("CHILD2", "Bob"), 
                ("CHILD3", "Carol"), ("STEPCHILD", "David")
            ], start=11):
                p = Person()
                p.set_handle(handle)
                p.set_gramps_id(f"I{i:04d}")
                p.set_gender(Person.FEMALE if i % 2 == 1 else Person.MALE)
                n = Name()
                n.set_first_name(name)
                s = Surname()
                s.set_surname("Smith")
                n.add_surname(s)
                p.set_primary_name(n)
                people[handle] = p
            
            # Create families with complex relationships
            
            # Great-grandparent families
            ggf1_family = Family()
            ggf1_family.set_handle("FAM_GG1")
            ggf1_family.set_gramps_id("F0001")
            ggf1_family.set_father_handle("GGF1")
            ggf1_family.set_mother_handle("GGM1")
            child_ref = ChildRef()
            child_ref.set_reference_handle("GF1")
            ggf1_family.add_child_ref(child_ref)
            families["FAM_GG1"] = ggf1_family
            
            ggf2_family = Family()
            ggf2_family.set_handle("FAM_GG2")
            ggf2_family.set_gramps_id("F0002")
            ggf2_family.set_father_handle("GGF2")
            ggf2_family.set_mother_handle("GGM2")
            child_ref = ChildRef()
            child_ref.set_reference_handle("GM1")
            ggf2_family.add_child_ref(child_ref)
            families["FAM_GG2"] = ggf2_family
            
            # Grandparent families
            gf1_family = Family()
            gf1_family.set_handle("FAM_G1")
            gf1_family.set_gramps_id("F0003")
            gf1_family.set_father_handle("GF1")
            gf1_family.set_mother_handle("GM1")
            child_ref = ChildRef()
            child_ref.set_reference_handle("FATHER")
            child_ref.set_father_relation(ChildRef.BIRTH)
            child_ref.set_mother_relation(ChildRef.BIRTH)
            gf1_family.add_child_ref(child_ref)
            families["FAM_G1"] = gf1_family
            
            gf2_family = Family()
            gf2_family.set_handle("FAM_G2")
            gf2_family.set_gramps_id("F0004")
            gf2_family.set_father_handle("GF2")
            gf2_family.set_mother_handle("GM2")
            child_ref = ChildRef()
            child_ref.set_reference_handle("MOTHER")
            gf2_family.add_child_ref(child_ref)
            families["FAM_G2"] = gf2_family
            
            # Parent family (original marriage)
            parent_family = Family()
            parent_family.set_handle("FAM_PARENTS")
            parent_family.set_gramps_id("F0005")
            parent_family.set_father_handle("FATHER")
            parent_family.set_mother_handle("MOTHER")
            parent_family.set_relationship(Family.MARRIED)
            
            # Add marriage event
            marriage = Event()
            marriage.set_handle("EVENT_MARRIAGE_001")
            marriage.set_type(EventType.MARRIAGE)
            marriage_date = Date()
            marriage_date.set(
                quality=Date.QUAL_NONE,
                modifier=Date.MOD_NONE,
                calendar=Date.CAL_GREGORIAN,
                value=(0, 1990, 6, 15, False)
            )
            marriage.set_date_object(marriage_date)
            
            event_ref = EventRef()
            event_ref.set_reference_handle(marriage.get_handle())
            event_ref.set_role("Family")
            parent_family.add_event_ref(event_ref)
            
            # Add children
            for child_handle in ["CHILD1", "CHILD2", "CHILD3"]:
                child_ref = ChildRef()
                child_ref.set_reference_handle(child_handle)
                child_ref.set_father_relation(ChildRef.BIRTH)
                child_ref.set_mother_relation(ChildRef.BIRTH)
                parent_family.add_child_ref(child_ref)
            
            families["FAM_PARENTS"] = parent_family
            
            # Divorce event
            divorce = Event()
            divorce.set_handle("EVENT_DIVORCE_001")
            divorce.set_type(EventType.DIVORCE)
            divorce_date = Date()
            divorce_date.set(
                quality=Date.QUAL_NONE,
                modifier=Date.MOD_NONE,
                calendar=Date.CAL_GREGORIAN,
                value=(0, 2005, 3, 1, False)
            )
            divorce.set_date_object(divorce_date)
            
            # Remarriage family
            remarriage_family = Family()
            remarriage_family.set_handle("FAM_REMARRIAGE")
            remarriage_family.set_gramps_id("F0006")
            remarriage_family.set_father_handle("FATHER")
            remarriage_family.set_mother_handle("STEPMOTHER")
            remarriage_family.set_relationship(Family.MARRIED)
            
            # Original children as step-children
            for child_handle in ["CHILD1", "CHILD2"]:
                child_ref = ChildRef()
                child_ref.set_reference_handle(child_handle)
                child_ref.set_father_relation(ChildRef.BIRTH)
                child_ref.set_mother_relation(ChildRef.STEPCHILD)
                remarriage_family.add_child_ref(child_ref)
            
            # New child from remarriage
            child_ref = ChildRef()
            child_ref.set_reference_handle("STEPCHILD")
            child_ref.set_father_relation(ChildRef.BIRTH)
            child_ref.set_mother_relation(ChildRef.BIRTH)
            remarriage_family.add_child_ref(child_ref)
            
            families["FAM_REMARRIAGE"] = remarriage_family
            
            # Calculate checksums before storage
            people_checksums_before = {
                handle: self.calculate_data_checksum(person)
                for handle, person in people.items()
            }
            family_checksums_before = {
                handle: self.calculate_data_checksum(family)
                for handle, family in families.items()
            }
            
            # Store everything
            with DbTxn("Store complex family tree", self.db) as trans:
                # Store all people
                for person in people.values():
                    self.db.add_person(person, trans)
                
                # Store events
                self.db.add_event(marriage, trans)
                self.db.add_event(divorce, trans)
                
                # Store all families
                for family in families.values():
                    self.db.add_family(family, trans)
            
            # Retrieve and verify
            retrieved_people = {}
            for handle in people:
                retrieved_people[handle] = self.db.get_person_from_handle(handle)
            
            retrieved_families = {}
            for handle in families:
                retrieved_families[handle] = self.db.get_family_from_handle(handle)
            
            # Calculate checksums after retrieval
            people_checksums_after = {
                handle: self.calculate_data_checksum(person)
                for handle, person in retrieved_people.items()
            }
            family_checksums_after = {
                handle: self.calculate_data_checksum(family)
                for handle, family in retrieved_families.items()
            }
            
            # Verify all checksums match
            people_match = all(
                people_checksums_before[h] == people_checksums_after[h]
                for h in people_checksums_before
            )
            families_match = all(
                family_checksums_before[h] == family_checksums_after[h]
                for h in family_checksums_before
            )
            
            # Verify specific relationships
            remarriage = retrieved_families.get("FAM_REMARRIAGE")
            relationship_checks = []
            if remarriage:
                children = remarriage.get_child_ref_list()
                # Check step-relationships preserved
                for child_ref in children:
                    if child_ref.get_reference_handle() == "CHILD1":
                        relationship_checks.append(
                            child_ref.get_mother_relation() == ChildRef.STEPCHILD
                        )
                    elif child_ref.get_reference_handle() == "STEPCHILD":
                        relationship_checks.append(
                            child_ref.get_mother_relation() == ChildRef.BIRTH
                        )
            
            all_checks = people_match and families_match and all(relationship_checks)
            
            if all_checks:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "details": f"4-generation tree with {len(people)} people and {len(families)} families preserved"
                }
                print(f"    ✓ {test_name} PASSED")
            else:
                self.results["failed"] += 1
                failures = []
                if not people_match: failures.append("Person data corrupted")
                if not families_match: failures.append("Family data corrupted")
                if not all(relationship_checks): failures.append("Step-relationships lost")
                
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
    
    def test_large_dataset_stress(self):
        """Test with thousands of people to verify performance and integrity."""
        test_name = "Large Dataset Stress Test"
        print(f"\n  Testing {test_name}...")
        
        try:
            num_people = 5000
            num_families = 1500
            
            print(f"    Creating {num_people} people and {num_families} families...")
            
            start_time = time.time()
            people_handles = []
            sample_checksums = {}  # Sample a subset for verification
            
            # Create people
            with DbTxn(f"Add {num_people} people", self.db) as trans:
                for i in range(num_people):
                    person = Person()
                    handle = f"STRESS_{i:06d}"
                    person.set_handle(handle)
                    person.set_gramps_id(f"I{i:06d}")
                    person.set_gender(Person.MALE if i % 2 == 0 else Person.FEMALE)
                    
                    name = Name()
                    name.set_first_name(f"Person{i}")
                    surname = Surname()
                    surname.set_surname(f"Family{i % 100}")
                    name.add_surname(surname)
                    person.set_primary_name(name)
                    
                    # Add some attributes to make it more realistic
                    attr = Attribute()
                    attr.set_type("ID")
                    attr.set_value(str(i))
                    person.add_attribute(attr)
                    
                    # Sample checksums for verification (every 100th person)
                    if i % 100 == 0:
                        sample_checksums[handle] = self.calculate_data_checksum(person)
                    
                    self.db.add_person(person, trans)
                    people_handles.append(handle)
            
            # Create families
            with DbTxn(f"Add {num_families} families", self.db) as trans:
                for i in range(num_families):
                    family = Family()
                    family.set_handle(f"FAM_STRESS_{i:06d}")
                    family.set_gramps_id(f"F{i:06d}")
                    
                    # Link people as parents
                    if i * 2 < len(people_handles):
                        family.set_father_handle(people_handles[i * 2])
                    if i * 2 + 1 < len(people_handles):
                        family.set_mother_handle(people_handles[i * 2 + 1])
                    
                    # Add children
                    base_child = i * 2 + 2
                    for j in range(min(3, len(people_handles) - base_child)):
                        child_ref = ChildRef()
                        child_ref.set_reference_handle(people_handles[base_child + j])
                        family.add_child_ref(child_ref)
                    
                    self.db.add_family(family, trans)
            
            creation_time = time.time() - start_time
            print(f"    Creation completed in {creation_time:.2f} seconds")
            
            # Test retrieval performance
            print(f"    Testing random retrieval...")
            retrieval_start = time.time()
            
            # Random access test
            for _ in range(500):
                random_handle = random.choice(people_handles)
                person = self.db.get_person_from_handle(random_handle)
                if person is None:
                    raise ValueError(f"Lost person {random_handle}")
            
            retrieval_time = time.time() - retrieval_start
            
            # Verify sampled data integrity
            print(f"    Verifying data integrity...")
            integrity_failures = []
            for handle, original_checksum in sample_checksums.items():
                person = self.db.get_person_from_handle(handle)
                if person:
                    new_checksum = self.calculate_data_checksum(person)
                    if original_checksum != new_checksum:
                        integrity_failures.append(handle)
                else:
                    integrity_failures.append(f"{handle} (not found)")
            
            # Count totals
            total_people = self.db.get_number_of_people()
            total_families = self.db.get_number_of_families()
            
            # Performance and integrity checks
            performance_ok = (
                creation_time < 120 and  # Should handle 5000 people in < 2 minutes
                retrieval_time < 5 and   # 500 random retrievals in < 5 seconds
                total_people == num_people and
                total_families == num_families and
                len(integrity_failures) == 0
            )
            
            if performance_ok:
                self.results["passed"] += 1
                self.results["test_details"][test_name] = {
                    "status": "PASSED",
                    "creation_time": f"{creation_time:.2f}s",
                    "retrieval_time": f"{retrieval_time:.2f}s",
                    "people": num_people,
                    "families": num_families
                }
                print(f"    ✓ {test_name} PASSED")
                print(f"      - Created {num_people} people in {creation_time:.2f}s")
                print(f"      - Retrieved 500 random people in {retrieval_time:.2f}s")
            else:
                self.results["failed"] += 1
                failures = []
                if creation_time >= 120: failures.append(f"Slow creation: {creation_time:.2f}s")
                if retrieval_time >= 5: failures.append(f"Slow retrieval: {retrieval_time:.2f}s")
                if total_people != num_people: failures.append(f"Lost people: {num_people - total_people}")
                if total_families != num_families: failures.append(f"Lost families: {num_families - total_families}")
                if integrity_failures: failures.append(f"Data corruption in {len(integrity_failures)} records")
                
                self.results["critical_failures"].append({
                    "test": test_name,
                    "failures": failures
                })
                print(f"    ✗ {test_name} FAILED")
                for failure in failures:
                    print(f"      - {failure}")
                    
        except Exception as e:
            self.results["failed"] += 1
            self.results["critical_failures"].append({
                "test": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"    ✗ {test_name} CRASHED: {e}")
            
        self.results["total_tests"] += 1
    
    def cleanup(self):
        """Clean up test database."""
        try:
            if self.db and self.db.is_open():
                self.db.close()
            
            # Note: To drop the test database, we'd need to connect as admin
            # For now, test databases will need manual cleanup
            print(f"\n  Note: Test database '{self.test_db_name}' may need manual cleanup")
            
        except Exception as e:
            print(f"  Cleanup error: {e}")
    
    def run_all_tests(self):
        """Run the complete test suite with REAL Gramps objects."""
        print("\n" + "=" * 80)
        print("REAL GRAMPS DATA INTEGRITY TEST SUITE")
        print("Testing with ACTUAL Gramps objects on REAL PostgreSQL server")
        print("=" * 80)
        
        # Setup database
        print("\nSetting up test database on remote server...")
        if not self.setup_database():
            print("❌ Failed to setup database - cannot proceed")
            return False
        
        print("\nRunning comprehensive data integrity tests...")
        
        # Run all tests
        self.test_person_complete_data_integrity()
        self.test_complex_family_relationships()
        self.test_large_dataset_stress()
        
        # Calculate reliability
        reliability = (
            (self.results["passed"] / self.results["total_tests"] * 100)
            if self.results["total_tests"] > 0 else 0
        )
        
        # Generate report
        print("\n" + "=" * 80)
        print("REAL DATA INTEGRITY RESULTS")
        print("=" * 80)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Data Integrity Reliability: {reliability:.2f}%")
        
        if reliability == 100:
            print("\n✅ TRULY BULLETPROOF - Real Gramps data integrity verified")
        elif reliability >= 90:
            print("\n⚠️ MOSTLY RELIABLE - Some data integrity issues remain")
        else:
            print("\n❌ NOT BULLETPROOF - Critical data integrity failures")
        
        if self.results["critical_failures"]:
            print("\nCRITICAL FAILURES:")
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
        report_file = f"REAL_GRAMPS_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nDetailed report saved: {report_file}")
        
        return reliability == 100

if __name__ == "__main__":
    tester = RealGrampsDataIntegrityTester()
    is_bulletproof = tester.run_all_tests()
    
    sys.exit(0 if is_bulletproof else 1)