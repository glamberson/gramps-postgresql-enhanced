#!/usr/bin/env python3
"""
BULLETPROOF TEST FOR ALL GRAMPS OBJECT TYPES (FIXED API)
Tests every Gramps object type with comprehensive data using correct API methods.
"""

import os
import sys
import time
import random
from datetime import datetime

# Add Gramps to path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Import real Gramps objects
from gramps.gen.lib import (
    Person, Family, Event, Place, Source, Citation, Repository, Media, Note, Tag,
    Name, Surname, Address, Url, Attribute, EventRef, PlaceRef, PlaceName,
    MediaRef, ChildRef, PersonRef, Date, StyledText, StyledTextTag,
    Location, EventType, FamilyRelType, NameType, UrlType, AttributeType,
    EventRoleType, RepositoryType, NoteType,
    StyledTextTagType, MarkerType, ChildRefType, RepoRef
)
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

def create_comprehensive_person():
    """Create a Person with ALL possible fields populated using correct API."""
    person = Person()
    person.set_handle(generate_handle())
    person.set_gramps_id(f"I{random.randint(1000, 9999)}")
    
    # Primary name with unicode and special characters
    name = Name()
    name.set_type(NameType.BIRTH)
    name.set_first_name("José María 李明 Владимир")
    name.set_suffix("Jr., Ph.D., M.D.")
    name.set_title("Dr. Prof. Sir")
    # Use set_nick_name instead of set_nick
    name.set_nick_name("Joey '\"<>&' Test")
    name.set_call_name("Joe")
    name.set_group_as("Test Family")
    name.set_sort_as(Name.LNFN)
    
    # Multiple surnames
    surname1 = Surname()
    surname1.set_surname("O'Brien-García")
    surname1.set_prefix("von der")
    surname1.set_primary(True)
    name.add_surname(surname1)
    
    surname2 = Surname()
    surname2.set_surname("李")
    surname2.set_origintype("Patronymic")
    name.add_surname(surname2)
    
    person.set_primary_name(name)
    
    # Alternate names
    alt_name = Name()
    alt_name.set_first_name("Joseph")
    alt_name.set_type(NameType.AKA)
    person.add_alternate_name(alt_name)
    
    # Gender
    person.set_gender(Person.MALE)
    
    # Addresses
    address = Address()
    address.set_street("123 Main St., Apt. #456")
    address.set_city("São Paulo")
    address.set_state("SP")
    address.set_country("Brazil")
    address.set_postal_code("01234-567")
    address.set_phone("+55 11 98765-4321")
    person.add_address(address)
    
    # URLs
    url = Url()
    url.set_path("https://example.com/person?id=123&name=test")
    url.set_description("Personal website with <html> tags")
    url.set_type(UrlType.WEB_HOME)
    person.add_url(url)
    
    # Attributes with SQL injection attempt
    attr = Attribute()
    attr.set_type(AttributeType.OCCUPATION)
    attr.set_value("Software Engineer; DROP TABLE persons; --")
    person.add_attribute(attr)
    
    # Notes
    note_handle = generate_handle()
    person.add_note(note_handle)
    
    # Tags
    person.add_tag("Important")
    person.add_tag("Review")
    
    # Privacy
    person.set_privacy(True)
    
    return person

def create_comprehensive_family():
    """Create a Family with complex relationships."""
    family = Family()
    family.set_handle(generate_handle())
    family.set_gramps_id(f"F{random.randint(1000, 9999)}")
    
    # Set relationship type
    family.set_relationship(FamilyRelType.MARRIED)
    
    # Father and Mother handles
    family.set_father_handle(generate_handle())
    family.set_mother_handle(generate_handle())
    
    # Multiple children with different relationships
    child1 = ChildRef()
    child1.set_reference_handle(generate_handle())
    child1.set_father_relation(ChildRefType.BIRTH)
    child1.set_mother_relation(ChildRefType.BIRTH)
    family.add_child_ref(child1)
    
    child2 = ChildRef()
    child2.set_reference_handle(generate_handle())
    child2.set_father_relation(ChildRefType.ADOPTED)
    child2.set_mother_relation(ChildRefType.BIRTH)
    family.add_child_ref(child2)
    
    # Step child
    child3 = ChildRef()
    child3.set_reference_handle(generate_handle())
    child3.set_father_relation(ChildRefType.STEPCHILD)
    child3.set_mother_relation(ChildRefType.NONE)
    family.add_child_ref(child3)
    
    # Event references
    event_ref = EventRef()
    event_ref.set_reference_handle(generate_handle())
    event_ref.set_role(EventRoleType.FAMILY)
    family.add_event_ref(event_ref)
    
    # Attributes with XSS attempt
    attr = Attribute()
    attr.set_type(AttributeType.CUSTOM)
    attr.set_value("Test <script>alert('XSS')</script> attribute")
    family.add_attribute(attr)
    
    return family

def create_comprehensive_event():
    """Create an Event with all fields populated."""
    event = Event()
    event.set_handle(generate_handle())
    event.set_gramps_id(f"E{random.randint(1000, 9999)}")
    
    # Event type and description
    event.set_type(EventType.MARRIAGE)
    event.set_description("Wedding ceremony with 'quotes' and \"double quotes\"")
    
    # Date with modifiers
    date = Date()
    date.set_yr_mon_day(1975, 7, 20)
    date.set_modifier(Date.MOD_ABOUT)
    date.set_quality(Date.QUAL_ESTIMATED)
    event.set_date_object(date)
    
    # Place reference
    event.set_place_handle(generate_handle())
    
    # Attributes with special characters
    attr = Attribute()
    attr.set_type(AttributeType.WITNESS)
    attr.set_value("John & Jane O'Brien, José García-López")
    event.add_attribute(attr)
    
    return event

def create_comprehensive_place():
    """Create a Place with hierarchies and coordinates using correct API."""
    place = Place()
    place.set_handle(generate_handle())
    place.set_gramps_id(f"P{random.randint(1000, 9999)}")
    
    # Place names using PlaceName object
    place_name = PlaceName()
    place_name.set_value("München / Munich / 慕尼黑")
    place.set_name(place_name)
    
    # Additional place names
    alt_name = PlaceName()
    alt_name.set_value("Monaco di Baviera")
    alt_name.set_language("it")
    place.add_alternative_name(alt_name)
    
    place.set_title("Capital of Bavaria")
    place.set_code("MUC")
    
    # GPS coordinates
    place.set_latitude("48.1351")
    place.set_longitude("11.5820")
    
    # Place hierarchy (enclosed by)
    parent_ref = PlaceRef()
    parent_ref.set_reference_handle(generate_handle())
    place.add_placeref(parent_ref)
    
    # Alternate locations
    location = Location()
    location.set_street("Marienplatz 1")
    location.set_city("München")
    location.set_state("Bayern")
    location.set_country("Deutschland")
    location.set_postal_code("80331")
    place.add_alternate_location(location)
    
    # URLs
    url = Url()
    url.set_path("https://maps.google.com/?q=48.1351,11.5820")
    url.set_description("Google Maps location")
    url.set_type(UrlType.WEB_SEARCH)
    place.add_url(url)
    
    return place

def create_comprehensive_source():
    """Create a Source with all fields using correct API."""
    source = Source()
    source.set_handle(generate_handle())
    source.set_gramps_id(f"S{random.randint(1000, 9999)}")
    
    # Source details with special characters
    source.set_title("Birth Records: St. Mary's Church (1850-1900)")
    source.set_author("O'Brien, Patrick & García, José")
    source.set_publication_info("London: Church Records Ltd., ©1950")
    source.set_abbreviation("StMary-BR-1850")
    
    # Repository references - use correct media type
    repo_ref = RepoRef()
    repo_ref.set_reference_handle(generate_handle())
    repo_ref.set_call_number("Microfilm #12345")
    # Use a valid SourceMediaType value
    repo_ref.set_media_type("Microfilm")
    source.add_repo_reference(repo_ref)
    
    # Attributes
    attr = Attribute()
    attr.set_type(AttributeType.CUSTOM)
    attr.set_value("Quality: Good; Condition: Some water damage")
    source.add_attribute(attr)
    
    # Notes
    source.add_note(generate_handle())
    
    return source

def create_comprehensive_citation():
    """Create a Citation with confidence levels."""
    citation = Citation()
    citation.set_handle(generate_handle())
    citation.set_gramps_id(f"C{random.randint(1000, 9999)}")
    
    # Reference to source
    citation.set_reference_handle(generate_handle())
    
    # Page with special formatting
    citation.set_page("pp. 123-125, \"Entry #456\", line 7-8")
    
    # Confidence level
    citation.set_confidence_level(Citation.CONF_HIGH)
    
    # Date accessed
    date = Date()
    date.set_yr_mon_day(2024, 3, 15)
    citation.set_date_object(date)
    
    # Notes
    citation.add_note(generate_handle())
    
    return citation

def create_comprehensive_repository():
    """Create a Repository with archive information."""
    repo = Repository()
    repo.set_handle(generate_handle())
    repo.set_gramps_id(f"R{random.randint(1000, 9999)}")
    
    # Repository details
    repo.set_type(RepositoryType.ARCHIVE)
    repo.set_name("National Archives & Records Administration")
    
    # Address
    address = Address()
    address.set_street("700 Pennsylvania Avenue NW")
    address.set_city("Washington")
    address.set_state("DC")
    address.set_country("United States")
    address.set_postal_code("20408")
    address.set_phone("+1-866-272-6272")
    repo.add_address(address)
    
    # URLs
    url = Url()
    url.set_path("https://www.archives.gov/")
    url.set_description("Official website")
    url.set_type(UrlType.WEB_HOME)
    repo.add_url(url)
    
    # Notes
    repo.add_note(generate_handle())
    
    return repo

def create_comprehensive_media():
    """Create a Media object with all fields."""
    media = Media()
    media.set_handle(generate_handle())
    media.set_gramps_id(f"O{random.randint(1000, 9999)}")
    
    # File path with spaces and special characters
    media.set_path("/home/user/Family Photos/Grand-père's 90th Birthday.jpg")
    media.set_mime_type("image/jpeg")
    media.set_description("Birthday celebration © 2020")
    
    # Date
    date = Date()
    date.set_yr_mon_day(2020, 8, 15)
    media.set_date_object(date)
    
    # Attributes
    attr = Attribute()
    attr.set_type(AttributeType.CUSTOM)
    attr.set_value("Camera: Nikon D850; f/2.8; ISO 400")
    media.add_attribute(attr)
    
    # Tags
    media.add_tag("Family")
    media.add_tag("Birthday")
    media.add_tag("2020")
    
    # Notes
    media.add_note(generate_handle())
    
    return media

def create_comprehensive_note():
    """Create a Note with formatted text using correct API."""
    note = Note()
    note.set_handle(generate_handle())
    note.set_gramps_id(f"N{random.randint(1000, 9999)}")
    
    # Note type
    note.set_type(NoteType.RESEARCH)
    
    # Complex formatted text with unicode and special characters
    text = """Research Notes - García-O'Brien Family Connection

This note contains various special characters and formatting:
• Unicode: 李明 (Li Ming), Владимир, José María, François
• Quotes: "double" and 'single' and `backticks`
• HTML-like: <b>bold</b> & <i>italic</i>
• SQL injection attempt: '; DROP TABLE notes; --
• XSS attempt: <script>alert('XSS')</script>
• Math symbols: ∑ ∏ ∫ ≈ ≠ ≤ ≥ ± × ÷
• Emojis: 👨‍👩‍👧‍👦 🎂 📷 🏛️
• Line breaks and tabs:
\tIndented text
\t\tDouble indented
• Very long line: """ + "A" * 500 + """
• Backslashes: C:\\Users\\Test\\Documents\\
• URLs: https://example.com/search?q=test&lang=en
• Email: john.obrien@example.com

End of comprehensive test note."""
    
    # Create StyledText with tags using correct API
    styled_text = StyledText(text)
    
    # Add styled tags with correct API
    tag1 = StyledTextTag()
    tag1.name = StyledTextTagType.BOLD
    tag1.ranges = [(0, 45)]  # Make title bold
    styled_text.add_tag(tag1)
    
    tag2 = StyledTextTag()
    tag2.name = StyledTextTagType.ITALIC
    tag2.ranges = [(50, 70)]  # Make some text italic
    styled_text.add_tag(tag2)
    
    # Add a link tag
    tag3 = StyledTextTag()
    tag3.name = StyledTextTagType.LINK
    tag3.value = "https://example.com"
    tag3.ranges = [(600, 620)]
    styled_text.add_tag(tag3)
    
    note.set_styledtext(styled_text)
    
    # Set format
    note.set_format(Note.FORMATTED)
    
    # Add tags
    note.add_tag("Research")
    note.add_tag("Important")
    
    return note

def create_comprehensive_tag():
    """Create a Tag with color and priority."""
    tag = Tag()
    tag.set_handle(generate_handle())
    tag.set_name("High Priority - Review ASAP! 📌")
    tag.set_color("#FF0000")  # Red color
    tag.set_priority(1)  # Highest priority
    return tag

def test_all_object_types():
    """Main test function for all object types."""
    print("=" * 80)
    print("BULLETPROOF TEST FOR ALL GRAMPS OBJECT TYPES (FIXED API)")
    print("Testing data integrity for all 9 Gramps object types")
    print("=" * 80)
    print()
    
    # Database configuration
    config = {
        "host": "192.168.10.90",
        "port": 5432,
        "user": "genealogy_user",
        "password": "GenealogyData2025",
        "database": f"bulletproof_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
    test_dir = f"/tmp/test_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(test_dir, exist_ok=True)
    
    # Move connection file to proper location
    conn_file_path = os.path.join(test_dir, "connection_info.txt")
    os.rename(conn_file, conn_file_path)
    
    db.load(test_dir, update=False, callback=None)
    
    results = {
        "Person": {"created": 0, "verified": 0, "failed": 0},
        "Family": {"created": 0, "verified": 0, "failed": 0},
        "Event": {"created": 0, "verified": 0, "failed": 0},
        "Place": {"created": 0, "verified": 0, "failed": 0},
        "Source": {"created": 0, "verified": 0, "failed": 0},
        "Citation": {"created": 0, "verified": 0, "failed": 0},
        "Repository": {"created": 0, "verified": 0, "failed": 0},
        "Media": {"created": 0, "verified": 0, "failed": 0},
        "Note": {"created": 0, "verified": 0, "failed": 0},
        "Tag": {"created": 0, "verified": 0, "failed": 0}
    }
    
    try:
        # Test each object type
        test_functions = [
            ("Person", create_comprehensive_person, db.add_person, db.get_person_from_handle),
            ("Family", create_comprehensive_family, db.add_family, db.get_family_from_handle),
            ("Event", create_comprehensive_event, db.add_event, db.get_event_from_handle),
            ("Place", create_comprehensive_place, db.add_place, db.get_place_from_handle),
            ("Source", create_comprehensive_source, db.add_source, db.get_source_from_handle),
            ("Citation", create_comprehensive_citation, db.add_citation, db.get_citation_from_handle),
            ("Repository", create_comprehensive_repository, db.add_repository, db.get_repository_from_handle),
            ("Media", create_comprehensive_media, db.add_media, db.get_media_from_handle),
            ("Note", create_comprehensive_note, db.add_note, db.get_note_from_handle),
            ("Tag", create_comprehensive_tag, db.add_tag, db.get_tag_from_handle)
        ]
        
        for obj_type, create_func, add_func, get_func in test_functions:
            print(f"\n{'='*60}")
            print(f"Testing {obj_type} objects...")
            print(f"{'='*60}")
            
            # Test 10 instances of each type
            for i in range(10):
                try:
                    # Create object
                    obj = create_func()
                    handle = obj.get_handle()
                    results[obj_type]["created"] += 1
                    
                    # Store in database
                    with DbTxn(f"Add {obj_type}", db) as trans:
                        add_func(obj, trans)
                    
                    # Retrieve from database
                    retrieved = get_func(handle)
                    
                    # Verify data integrity
                    if compare_ignoring_change_time(obj, retrieved, f"{obj_type} #{i+1}"):
                        results[obj_type]["verified"] += 1
                        print(f"  ✅ {obj_type} #{i+1}: Data integrity verified")
                    else:
                        results[obj_type]["failed"] += 1
                        print(f"  ❌ {obj_type} #{i+1}: Data corruption detected!")
                        
                except Exception as e:
                    results[obj_type]["failed"] += 1
                    print(f"  ❌ {obj_type} #{i+1}: Exception - {str(e)}")
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_created = 0
        total_verified = 0
        total_failed = 0
        
        for obj_type, stats in results.items():
            total_created += stats["created"]
            total_verified += stats["verified"]
            total_failed += stats["failed"]
            
            status = "✅ PASS" if stats["failed"] == 0 else "❌ FAIL"
            print(f"{obj_type:12} - Created: {stats['created']:3}, Verified: {stats['verified']:3}, Failed: {stats['failed']:3} {status}")
        
        print("-"*80)
        print(f"{'TOTAL':12} - Created: {total_created:3}, Verified: {total_verified:3}, Failed: {total_failed:3}")
        
        if total_failed == 0:
            print("\n" + "🎉"*20)
            print("✅ ALL OBJECT TYPES PASSED - DATABASE IS BULLETPROOF!")
            print("🎉"*20)
        else:
            print("\n" + "⚠️"*20)
            print(f"❌ {total_failed} FAILURES DETECTED - NEEDS INVESTIGATION")
            print("⚠️"*20)
            
    finally:
        # Close database
        db.close()
        print(f"\nTest database: {config['database']}")
    
    return total_failed == 0

if __name__ == "__main__":
    success = test_all_object_types()
    sys.exit(0 if success else 1)