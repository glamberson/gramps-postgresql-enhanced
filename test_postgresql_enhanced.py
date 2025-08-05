#!/usr/bin/env python3
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025 Greg Lamberson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

"""
Comprehensive test suite for PostgreSQL Enhanced addon
"""

import sys
import os
import logging

# Suppress gramps locale debug messages
logging.getLogger("gramps.gen.utils.grampslocale").setLevel(logging.WARNING)

import time
import random
import string
import json
from datetime import datetime

# Add plugin directory to path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# Import PostgreSQL modules
import psycopg
from psycopg import sql

# Import Gramps modules
sys.path.insert(0, "/usr/lib/python3/dist-packages")
from gramps.gen.lib import (
    Person,
    Family,
    Event,
    Place,
    Source,
    Citation,
    Repository,
    Media,
    Note,
    Tag,
)
from gramps.gen.lib import Name, Surname, Date, EventRef, EventType, ChildRef
from gramps.gen.lib import Attribute, AttributeType, Url, UrlType
from gramps.gen.lib.serialize import JSONSerializer
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.db import DbTxn

# Import our addon
from postgresqlenhanced import PostgreSQLEnhanced


class TestResult:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.start_time = time.time()

    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ FAIL: {test_name}: {error}")

    def summary(self):
        elapsed = time.time() - self.start_time
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.passed}/{total} passed ({elapsed:.2f}s)")
        if self.errors:
            print(f"\nFailed tests:")
            for test, error in self.errors:
                print(f"  - {test}: {error}")
        print(f"{'='*60}\n")
        return self.failed == 0


class PostgreSQLEnhancedTester:
    """Comprehensive test suite for PostgreSQL Enhanced addon"""

    def __init__(self):
        self.db = None
        self.test_db_name = f"test_gramps_{int(time.time())}"
        self.results = TestResult()
        self.test_handles = {}  # Store handles for cross-test reference

    def setup(self):
        """Set up test database"""
        print(f"\n🔧 Setting up test database: {self.test_db_name}")

        # Create test directory
        self.test_dir = f"/tmp/gramps_test_{int(time.time())}"
        os.makedirs(self.test_dir, exist_ok=True)

        # Create connection_info.txt
        config_path = os.path.join(self.test_dir, "connection_info.txt")
        with open(config_path, "w") as f:
            f.write(
                """# Test configuration
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = separate
"""
            )

        # Initialize database
        self.db = PostgreSQLEnhanced()
        self.db.load(self.test_dir, None, None)
        print(f"✅ Database initialized")

    def teardown(self):
        """Clean up test database"""
        print(f"\n🧹 Cleaning up test database")
        if self.db:
            self.db.close()

        # Drop test database
        try:
            conn = psycopg.connect(
                f"postgresql://genealogy_user:GenealogyData2025@192.168.10.90:5432/postgres"
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(
                        sql.Identifier(self.test_db_name)
                    )
                )
            conn.close()
            print(f"✅ Test database dropped")
        except Exception as e:
            print(f"⚠️  Could not drop test database: {e}")

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n🚀 Running PostgreSQL Enhanced Test Suite")
        print(f"{'='*60}")

        try:
            self.setup()

            # Core functionality tests
            self.test_person_crud()
            self.test_family_crud()
            self.test_event_crud()
            self.test_place_crud()
            self.test_source_citation_crud()
            self.test_repository_crud()
            self.test_media_crud()
            self.test_note_crud()
            self.test_tag_crud()

            # Secondary column tests
            self.test_secondary_columns_person()
            self.test_secondary_columns_all_types()

            # Search and filter tests
            self.test_search_operations()
            self.test_filter_operations()

            # Relationship tests
            self.test_family_relationships()
            self.test_person_references()

            # Performance tests
            self.test_bulk_operations()
            self.test_concurrent_access()

            # Edge cases
            self.test_edge_cases()
            self.test_error_handling()

        finally:
            self.teardown()
            self.results.summary()

    def test_person_crud(self):
        """Test Person CRUD operations"""
        test_name = "Person CRUD"
        try:
            # Create
            person = Person()
            person.set_gramps_id("I0001")

            # Set primary name
            name = Name()
            name.set_first_name("Test")
            surname = Surname()
            surname.set_surname("Person")
            name.add_surname(surname)
            person.set_primary_name(name)

            # Set attributes
            person.set_gender(Person.MALE)

            # Add URL
            url = Url()
            url.set_path("https://example.com")
            url.set_type(UrlType.WEB_HOME)
            person.add_url(url)

            # Add attribute
            attr = Attribute()
            attr.set_type(AttributeType.NICKNAME)
            attr.set_value("Testy")
            person.add_attribute(attr)

            # Save
            with DbTxn("Create test person", self.db) as trans:
                self.db.add_person(person, trans)
                handle = person.handle
                self.test_handles["person1"] = handle
                print(f"DEBUG: Created person with handle: {handle}")

            # Verify person exists in database
            self.db.dbapi.execute(
                "SELECT handle, json_data FROM person WHERE handle = %s", [handle]
            )
            result = self.db.dbapi.fetchone()
            if result:
                print(f"DEBUG: Person found in DB with handle: {result[0]}")
            else:
                print(f"DEBUG: Person NOT found in DB with handle: {handle}")

            # Read
            print(f"DEBUG: Calling get_person_from_handle({handle})")
            print(f"DEBUG: db type: {type(self.db)}")
            print(f"DEBUG: has method: {hasattr(self.db, 'get_person_from_handle')}")

            person2 = self.db.get_person_from_handle(handle)
            if person2 is None:
                raise Exception(
                    f"Person with handle {handle} was not found after creation"
                )
            assert person2.get_gramps_id() == "I0001"
            assert person2.get_primary_name().get_first_name() == "Test"
            assert person2.get_primary_name().get_surname() == "Person"

            # Update
            person2.get_primary_name().set_first_name("Updated")
            with DbTxn("Update test person", self.db) as trans:
                self.db.commit_person(person2, trans)

            # Verify update
            person3 = self.db.get_person_from_handle(handle)
            assert person3.get_primary_name().get_first_name() == "Updated"

            # Delete
            with DbTxn("Delete test person", self.db) as trans:
                self.db.remove_person(handle, trans)

            # Verify deletion
            try:
                deleted_person = self.db.get_person_from_handle(handle)
                assert deleted_person is None
            except Exception as e:
                print(
                    f"DEBUG: Exception when getting deleted person: {type(e).__name__}: {e}"
                )
                # If DBAPI raises exception for missing handles, that's also acceptable
                if "not found" not in str(e).lower():
                    raise

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_family_crud(self):
        """Test Family CRUD operations"""
        test_name = "Family CRUD"
        try:
            # Create test people first
            father = Person()
            father.set_gramps_id("I0002")
            name = Name()
            name.set_first_name("John")
            surname = Surname()
            surname.set_surname("Smith")
            name.add_surname(surname)
            father.set_primary_name(name)
            father.set_gender(Person.MALE)

            mother = Person()
            mother.set_gramps_id("I0003")
            name = Name()
            name.set_first_name("Jane")
            surname = Surname()
            surname.set_surname("Doe")
            name.add_surname(surname)
            mother.set_primary_name(name)
            mother.set_gender(Person.FEMALE)

            child = Person()
            child.set_gramps_id("I0004")
            name = Name()
            name.set_first_name("Baby")
            surname = Surname()
            surname.set_surname("Smith")
            name.add_surname(surname)
            child.set_primary_name(name)

            with DbTxn("Create test people", self.db) as trans:
                self.db.add_person(father, trans)
                self.db.add_person(mother, trans)
                self.db.add_person(child, trans)
                self.test_handles["father"] = father.handle
                self.test_handles["mother"] = mother.handle
                self.test_handles["child"] = child.handle

            # Create family
            family = Family()
            family.set_gramps_id("F0001")
            family.set_father_handle(father.handle)
            family.set_mother_handle(mother.handle)

            # Add child
            childref = ChildRef()
            childref.set_reference_handle(child.handle)
            family.add_child_ref(childref)

            # Save family
            with DbTxn("Create test family", self.db) as trans:
                self.db.add_family(family, trans)
                handle = family.handle
                self.test_handles["family1"] = handle

            # Read
            family2 = self.db.get_family_from_handle(handle)
            assert family2.get_gramps_id() == "F0001"
            assert family2.get_father_handle() == father.handle
            assert family2.get_mother_handle() == mother.handle
            assert len(family2.get_child_ref_list()) == 1

            # Update
            family2.set_gramps_id("F0001-Updated")
            with DbTxn("Update test family", self.db) as trans:
                self.db.commit_family(family2, trans)

            # Verify update
            family3 = self.db.get_family_from_handle(handle)
            assert family3.get_gramps_id() == "F0001-Updated"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_event_crud(self):
        """Test Event CRUD operations"""
        test_name = "Event CRUD"
        try:
            # Create event
            event = Event()
            event.set_gramps_id("E0001")
            event.set_type(EventType.BIRTH)
            event.set_description("Test birth event")

            # Set date
            date = Date()
            date.set_yr_mon_day(1900, 1, 1)
            event.set_date_object(date)

            # Save
            with DbTxn("Create test event", self.db) as trans:
                self.db.add_event(event, trans)
                handle = event.handle
                self.test_handles["event1"] = handle

            # Read
            event2 = self.db.get_event_from_handle(handle)
            assert event2.get_gramps_id() == "E0001"
            assert event2.get_description() == "Test birth event"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_place_crud(self):
        """Test Place CRUD operations"""
        test_name = "Place CRUD"
        try:
            # Create place
            place = Place()
            place.set_gramps_id("P0001")
            place.set_title("Test City")
            place.set_code("TC")

            # Save
            with DbTxn("Create test place", self.db) as trans:
                self.db.add_place(place, trans)
                handle = place.handle
                self.test_handles["place1"] = handle

            # Read
            place2 = self.db.get_place_from_handle(handle)
            assert place2.get_gramps_id() == "P0001"
            assert place2.get_title() == "Test City"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_source_citation_crud(self):
        """Test Source and Citation CRUD operations"""
        test_name = "Source/Citation CRUD"
        try:
            # Create source
            source = Source()
            source.set_gramps_id("S0001")
            source.set_title("Test Source")
            source.set_author("Test Author")
            source.set_publication_info("Test Publisher, 2025")
            source.set_abbreviation("TS")

            with DbTxn("Create test source", self.db) as trans:
                self.db.add_source(source, trans)
                source_handle = source.handle
                self.test_handles["source1"] = source_handle

            # Create citation
            citation = Citation()
            citation.set_gramps_id("C0001")
            citation.set_page("Page 123")
            citation.set_confidence_level(Citation.CONF_HIGH)
            citation.set_reference_handle(source_handle)

            with DbTxn("Create test citation", self.db) as trans:
                self.db.add_citation(citation, trans)
                citation_handle = citation.handle
                self.test_handles["citation1"] = citation_handle

            # Read
            source2 = self.db.get_source_from_handle(source_handle)
            citation2 = self.db.get_citation_from_handle(citation_handle)

            assert source2.get_title() == "Test Source"
            assert citation2.get_page() == "Page 123"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_repository_crud(self):
        """Test Repository CRUD operations"""
        test_name = "Repository CRUD"
        try:
            repo = Repository()
            repo.set_gramps_id("R0001")
            repo.set_name("Test Repository")

            with DbTxn("Create test repository", self.db) as trans:
                self.db.add_repository(repo, trans)
                handle = repo.handle

            repo2 = self.db.get_repository_from_handle(handle)
            assert repo2.get_name() == "Test Repository"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_media_crud(self):
        """Test Media CRUD operations"""
        test_name = "Media CRUD"
        try:
            media = Media()
            media.set_gramps_id("M0001")
            media.set_path("/test/image.jpg")
            media.set_mime_type("image/jpeg")
            media.set_description("Test image")

            with DbTxn("Create test media", self.db) as trans:
                self.db.add_media(media, trans)
                handle = media.handle

            media2 = self.db.get_media_from_handle(handle)
            assert media2.get_path() == "/test/image.jpg"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_note_crud(self):
        """Test Note CRUD operations"""
        test_name = "Note CRUD"
        try:
            note = Note()
            note.set_gramps_id("N0001")
            # StyledText is required, not plain string
            from gramps.gen.lib import StyledText

            styled_text = StyledText("This is a test note")
            note.set_styledtext(styled_text)
            note.set_format(Note.FORMATTED)

            with DbTxn("Create test note", self.db) as trans:
                self.db.add_note(note, trans)
                handle = note.handle

            note2 = self.db.get_note_from_handle(handle)
            assert "test note" in str(note2.get_styledtext())

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_tag_crud(self):
        """Test Tag CRUD operations"""
        test_name = "Tag CRUD"
        try:
            tag = Tag()
            tag.set_name("TestTag")
            tag.set_color("#FF0000")
            tag.set_priority(1)

            with DbTxn("Create test tag", self.db) as trans:
                self.db.add_tag(tag, trans)
                handle = tag.handle

            tag2 = self.db.get_tag_from_handle(handle)
            assert tag2.get_name() == "TestTag"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_secondary_columns_person(self):
        """Test secondary column population for Person"""
        test_name = "Person secondary columns"
        try:
            # Create person with various names
            person = Person()
            person.set_gramps_id("I0010")

            name = Name()
            name.set_first_name("William")
            surname = Surname()
            surname.set_surname("Shakespeare")
            name.add_surname(surname)
            person.set_primary_name(name)

            with DbTxn("Create person for secondary test", self.db) as trans:
                self.db.add_person(person, trans)

            # Check secondary columns directly in database
            # Use the existing connection from self.db.dbapi
            self.db.dbapi.execute(
                """
                SELECT gramps_id, given_name, surname 
                FROM person 
                WHERE gramps_id = 'I0010'
            """
            )
            row = self.db.dbapi.fetchone()
            assert row[0] == "I0010"
            assert row[1] == "William"
            assert row[2] == "Shakespeare"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_secondary_columns_all_types(self):
        """Test secondary columns for all object types"""
        test_name = "All secondary columns"
        try:
            # We'll check that the required columns exist and can be populated
            # Use the existing connection from self.db.dbapi

            # Check each table has expected columns
            tables_columns = {
                "person": ["gramps_id", "given_name", "surname", "gender"],
                "family": ["gramps_id", "father_handle", "mother_handle"],
                "event": ["gramps_id", "description", "place"],
                "place": ["gramps_id", "title", "code"],
                "source": ["gramps_id", "title", "author"],
                "citation": ["gramps_id", "page", "source_handle"],
                "repository": ["gramps_id", "name"],
                "media": [
                    "gramps_id",
                    "path",
                    "desc_",
                ],  # desc is a reserved word, so it's desc_
                "note": ["gramps_id"],
                "tag": ["name", "color"],
            }

            for table, columns in tables_columns.items():
                # First, let's see what columns the table actually has
                self.db.dbapi.execute(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """,
                    [table],
                )
                actual_columns = [row[0] for row in self.db.dbapi.fetchall()]
                print(f"DEBUG: {table} has columns: {actual_columns}")

                for column in columns:
                    if column not in actual_columns:
                        raise Exception(f"Column {column} missing from {table}")

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_search_operations(self):
        """Test search functionality"""
        test_name = "Search operations"
        try:
            # Create test data
            names = [
                ("John", "Smith"),
                ("Jane", "Smith"),
                ("John", "Doe"),
                ("Mary", "Johnson"),
                ("James", "Johnson"),
                ("Jennifer", "Jones"),
            ]

            for i, (first, last) in enumerate(names):
                person = Person()
                person.set_gramps_id(f"I{i:04d}")
                name = Name()
                name.set_first_name(first)
                surname = Surname()
                surname.set_surname(last)
                name.add_surname(surname)
                person.set_primary_name(name)

                with DbTxn(f"Create {first} {last}", self.db) as trans:
                    self.db.add_person(person, trans)

            # Test surname search
            # Count how many Smiths we have (should be at least 2 from this test)
            smiths = list(self.db.iter_person_handles())
            smith_count = 0
            our_smith_count = 0
            for handle in smiths:
                person = self.db.get_person_from_handle(handle)
                if person.get_primary_name().get_surname() == "Smith":
                    smith_count += 1
                    # Check if it's one of our test Smiths
                    gramps_id = person.get_gramps_id()
                    if gramps_id in ["I0000", "I0001"]:  # John and Jane Smith
                        our_smith_count += 1

            # We should have at least our 2 Smiths
            assert (
                our_smith_count == 2
            ), f"Expected 2 test Smiths, found {our_smith_count}"
            # The total count may be higher due to other tests
            assert (
                smith_count >= 2
            ), f"Expected at least 2 Smiths total, found {smith_count}"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_filter_operations(self):
        """Test filter functionality"""
        test_name = "Filter operations"
        try:
            # This would test Gramps filter rules
            # For now, just verify we can iterate and filter manually
            males = 0
            females = 0

            for handle in self.db.iter_person_handles():
                person = self.db.get_person_from_handle(handle)
                if person.get_gender() == Person.MALE:
                    males += 1
                elif person.get_gender() == Person.FEMALE:
                    females += 1

            # We should have some of each from previous tests
            assert males > 0 or females > 0

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_family_relationships(self):
        """Test family relationship integrity"""
        test_name = "Family relationships"
        try:
            # Use the family we created earlier
            if "family1" in self.test_handles:
                family = self.db.get_family_from_handle(self.test_handles["family1"])

                # Check parent handles
                father = self.db.get_person_from_handle(family.get_father_handle())
                mother = self.db.get_person_from_handle(family.get_mother_handle())

                assert father is not None
                assert mother is not None

                # Check child references
                for childref in family.get_child_ref_list():
                    child = self.db.get_person_from_handle(
                        childref.get_reference_handle()
                    )
                    assert child is not None

                self.results.add_pass(test_name)
            else:
                self.results.add_fail(test_name, "No family created in previous tests")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_person_references(self):
        """Test person reference integrity"""
        test_name = "Person references"
        try:
            # Create person with event reference
            person = Person()
            person.set_gramps_id("I0100")
            name = Name()
            name.set_first_name("Event")
            surname = Surname()
            surname.set_surname("Tester")
            name.add_surname(surname)
            person.set_primary_name(name)

            # Create and add event
            event = Event()
            event.set_type(EventType.BIRTH)
            event.set_description("Birth of Event Tester")

            with DbTxn("Create event", self.db) as trans:
                self.db.add_event(event, trans)
                event_handle = event.handle

            # Add event reference to person
            event_ref = EventRef()
            event_ref.set_reference_handle(event_handle)
            person.add_event_ref(event_ref)

            with DbTxn("Create person with event", self.db) as trans:
                self.db.add_person(person, trans)

            # Verify reference integrity
            person2 = self.db.get_person_from_gramps_id("I0100")
            assert len(person2.get_event_ref_list()) == 1
            event_ref2 = person2.get_event_ref_list()[0]
            event2 = self.db.get_event_from_handle(event_ref2.get_reference_handle())
            assert event2.get_description() == "Birth of Event Tester"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_bulk_operations(self):
        """Test bulk insert performance"""
        test_name = "Bulk operations"
        try:
            start_time = time.time()
            count = 100

            # Bulk create people
            for i in range(count):
                person = Person()
                person.set_gramps_id(f"I{1000+i:04d}")
                name = Name()
                name.set_first_name(f"Bulk{i}")
                surname = Surname()
                surname.set_surname("Test")
                name.add_surname(surname)
                person.set_primary_name(name)

                with DbTxn(f"Bulk create {i}", self.db) as trans:
                    self.db.add_person(person, trans)

            elapsed = time.time() - start_time
            rate = count / elapsed

            print(f"  Bulk insert rate: {rate:.1f} persons/second")

            # Verify all were created
            bulk_count = 0
            for handle in self.db.iter_person_handles():
                person = self.db.get_person_from_handle(handle)
                if person.get_primary_name().get_surname() == "Test":
                    bulk_count += 1

            assert (
                bulk_count >= count
            ), f"Expected {count} bulk persons, found {bulk_count}"

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_concurrent_access(self):
        """Test concurrent database access"""
        test_name = "Concurrent access"
        try:
            # This is a simple test - real concurrent testing would use threads
            # For now, just verify we can have multiple connections

            # Get the current database name from connection info
            self.db.dbapi.execute("SELECT current_database()")
            db_name = self.db.dbapi.fetchone()[0]

            conn1 = psycopg.connect(
                f"postgresql://genealogy_user:GenealogyData2025@192.168.10.90:5432/{db_name}"
            )
            conn2 = psycopg.connect(
                f"postgresql://genealogy_user:GenealogyData2025@192.168.10.90:5432/{db_name}"
            )

            # Both connections should work
            with conn1.cursor() as cur1:
                cur1.execute("SELECT COUNT(*) FROM person")
                count1 = cur1.fetchone()[0]

            with conn2.cursor() as cur2:
                cur2.execute("SELECT COUNT(*) FROM person")
                count2 = cur2.fetchone()[0]

            assert count1 == count2

            conn1.close()
            conn2.close()

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_edge_cases(self):
        """Test edge cases"""
        test_name = "Edge cases"
        try:
            # Test empty names
            person = Person()
            person.set_gramps_id("I9999")
            name = Name()
            # No first name or surname set
            person.set_primary_name(name)

            with DbTxn("Create person with empty name", self.db) as trans:
                self.db.add_person(person, trans)

            # Test very long names
            person2 = Person()
            person2.set_gramps_id("I9998")
            name2 = Name()
            name2.set_first_name("A" * 200)  # Very long name
            surname2 = Surname()
            surname2.set_surname("B" * 200)
            name2.add_surname(surname2)
            person2.set_primary_name(name2)

            with DbTxn("Create person with long name", self.db) as trans:
                self.db.add_person(person2, trans)

            # Test special characters
            person3 = Person()
            person3.set_gramps_id("I9997")
            name3 = Name()
            name3.set_first_name("Jean-François")
            surname3 = Surname()
            surname3.set_surname("O'Brien-Smith")
            name3.add_surname(surname3)
            person3.set_primary_name(name3)

            with DbTxn("Create person with special chars", self.db) as trans:
                self.db.add_person(person3, trans)

            # Verify all were created
            for gramps_id in ["I9999", "I9998", "I9997"]:
                person = self.db.get_person_from_gramps_id(gramps_id)
                assert person is not None

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    def test_error_handling(self):
        """Test error handling"""
        test_name = "Error handling"
        try:
            # Test duplicate gramps_id
            person1 = Person()
            person1.set_gramps_id("I8888")
            name = Name()
            name.set_first_name("Duplicate")
            person1.set_primary_name(name)

            person2 = Person()
            person2.set_gramps_id("I8888")  # Same ID
            name2 = Name()
            name2.set_first_name("Duplicate2")
            person2.set_primary_name(name2)

            with DbTxn("Create first person", self.db) as trans:
                self.db.add_person(person1, trans)

            # This should work - Gramps allows duplicate gramps_ids
            # but different handles
            with DbTxn("Create duplicate gramps_id", self.db) as trans:
                self.db.add_person(person2, trans)

            # Test invalid handle
            try:
                invalid_person = self.db.get_person_from_handle("invalid_handle_12345")
                assert invalid_person is None
            except Exception as e:
                # DBAPI raises HandleError for missing handles
                assert "not found" in str(e).lower()

            # Test transaction rollback
            try:
                with DbTxn("Test rollback", self.db) as trans:
                    person3 = Person()
                    person3.set_gramps_id("I7777")
                    self.db.add_person(person3, trans)
                    # Force an error
                    raise Exception("Test rollback")
            except:
                pass

            # Person should not exist due to rollback
            person3_check = self.db.get_person_from_gramps_id("I7777")
            assert person3_check is None

            self.results.add_pass(test_name)

        except Exception as e:
            self.results.add_fail(test_name, str(e))


def main():
    """Run the test suite"""
    tester = PostgreSQLEnhancedTester()
    tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if tester.results.failed == 0 else 1)


if __name__ == "__main__":
    main()
