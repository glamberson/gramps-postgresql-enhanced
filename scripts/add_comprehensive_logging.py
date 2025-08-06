#!/usr/bin/env python3
"""
Add comprehensive logging to postgresqlenhanced.py
This script adds detailed logging to all critical methods
"""

import re

# Read the current file
with open('postgresqlenhanced.py', 'r') as f:
    content = f.read()

# Define logging additions for each method
logging_additions = {
    'def commit_person': '''        LOG.debug("=== COMMIT PERSON START ===")
        LOG.debug(f"Handle: {person.handle}, Gramps ID: {person.gramps_id}")
        LOG.debug(f"Primary name: {person.primary_name}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_family': '''        LOG.debug("=== COMMIT FAMILY START ===")
        LOG.debug(f"Handle: {family.handle}, Gramps ID: {family.gramps_id}")
        LOG.debug(f"Father: {family.father_handle}, Mother: {family.mother_handle}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_event': '''        LOG.debug("=== COMMIT EVENT START ===")
        LOG.debug(f"Handle: {event.handle}, Gramps ID: {event.gramps_id}")
        LOG.debug(f"Type: {event.get_type()}, Date: {event.get_date_object()}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_place': '''        LOG.debug("=== COMMIT PLACE START ===")
        LOG.debug(f"Handle: {place.handle}, Gramps ID: {place.gramps_id}")
        LOG.debug(f"Title: {place.get_title()}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_source': '''        LOG.debug("=== COMMIT SOURCE START ===")
        LOG.debug(f"Handle: {source.handle}, Gramps ID: {source.gramps_id}")
        LOG.debug(f"Title: {source.get_title()}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_citation': '''        LOG.debug("=== COMMIT CITATION START ===")
        LOG.debug(f"Handle: {citation.handle}, Gramps ID: {citation.gramps_id}")
        LOG.debug(f"Source handle: {citation.source_handle}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_repository': '''        LOG.debug("=== COMMIT REPOSITORY START ===")
        LOG.debug(f"Handle: {repository.handle}, Gramps ID: {repository.gramps_id}")
        LOG.debug(f"Name: {repository.get_name()}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_media': '''        LOG.debug("=== COMMIT MEDIA START ===")
        LOG.debug(f"Handle: {media.handle}, Gramps ID: {media.gramps_id}")
        LOG.debug(f"Path: {media.get_path()}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_note': '''        LOG.debug("=== COMMIT NOTE START ===")
        LOG.debug(f"Handle: {note.handle}, Gramps ID: {note.gramps_id}")
        LOG.debug(f"Type: {note.get_type()}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def commit_tag': '''        LOG.debug("=== COMMIT TAG START ===")
        LOG.debug(f"Handle: {tag.handle}")
        LOG.debug(f"Name: {tag.get_name()}, Color: {tag.get_color()}")
        LOG.debug(f"Change time: {change_time}")
''',
    'def _execute_sql': '''        LOG.debug("=== SQL EXECUTION ===")
        LOG.debug(f"Query: {sql}")
        LOG.debug(f"Params: {params}")
''',
    'def get_person_from_handle': '''        LOG.debug(f"Getting person with handle: {handle}")
''',
    'def get_family_from_handle': '''        LOG.debug(f"Getting family with handle: {handle}")
''',
    'def get_event_from_handle': '''        LOG.debug(f"Getting event with handle: {handle}")
''',
    'def get_place_from_handle': '''        LOG.debug(f"Getting place with handle: {handle}")
''',
    'def get_source_from_handle': '''        LOG.debug(f"Getting source with handle: {handle}")
''',
    'def get_citation_from_handle': '''        LOG.debug(f"Getting citation with handle: {handle}")
''',
    'def get_repository_from_handle': '''        LOG.debug(f"Getting repository with handle: {handle}")
''',
    'def get_media_from_handle': '''        LOG.debug(f"Getting media with handle: {handle}")
''',
    'def get_note_from_handle': '''        LOG.debug(f"Getting note with handle: {handle}")
''',
    'def get_tag_from_handle': '''        LOG.debug(f"Getting tag with handle: {handle}")
''',
    'def add_person': '''        LOG.debug(f"=== ADD PERSON ===")
        LOG.debug(f"Person handle: {person.handle}, Gramps ID: {person.gramps_id}")
''',
    'def add_family': '''        LOG.debug(f"=== ADD FAMILY ===")
        LOG.debug(f"Family handle: {family.handle}, Gramps ID: {family.gramps_id}")
''',
    'def add_event': '''        LOG.debug(f"=== ADD EVENT ===")
        LOG.debug(f"Event handle: {event.handle}, Gramps ID: {event.gramps_id}")
''',
    'def add_place': '''        LOG.debug(f"=== ADD PLACE ===")
        LOG.debug(f"Place handle: {place.handle}, Gramps ID: {place.gramps_id}")
''',
    'def add_source': '''        LOG.debug(f"=== ADD SOURCE ===")
        LOG.debug(f"Source handle: {source.handle}, Gramps ID: {source.gramps_id}")
''',
    'def add_citation': '''        LOG.debug(f"=== ADD CITATION ===")
        LOG.debug(f"Citation handle: {citation.handle}, Gramps ID: {citation.gramps_id}")
''',
    'def add_repository': '''        LOG.debug(f"=== ADD REPOSITORY ===")
        LOG.debug(f"Repository handle: {repository.handle}, Gramps ID: {repository.gramps_id}")
''',
    'def add_media': '''        LOG.debug(f"=== ADD MEDIA ===")
        LOG.debug(f"Media handle: {media.handle}, Gramps ID: {media.gramps_id}")
''',
    'def add_note': '''        LOG.debug(f"=== ADD NOTE ===")
        LOG.debug(f"Note handle: {note.handle}, Gramps ID: {note.gramps_id}")
''',
    'def add_tag': '''        LOG.debug(f"=== ADD TAG ===")
        LOG.debug(f"Tag handle: {tag.handle}, Name: {tag.get_name()}")
''',
    'def update_person': '''        LOG.debug(f"=== UPDATE PERSON ===")
        LOG.debug(f"Person handle: {person.handle}, Gramps ID: {person.gramps_id}")
''',
    'def update_family': '''        LOG.debug(f"=== UPDATE FAMILY ===")
        LOG.debug(f"Family handle: {family.handle}, Gramps ID: {family.gramps_id}")
''',
    'def update_event': '''        LOG.debug(f"=== UPDATE EVENT ===")
        LOG.debug(f"Event handle: {event.handle}, Gramps ID: {event.gramps_id}")
''',
    'def update_place': '''        LOG.debug(f"=== UPDATE PLACE ===")
        LOG.debug(f"Place handle: {place.handle}, Gramps ID: {place.gramps_id}")
''',
    'def update_source': '''        LOG.debug(f"=== UPDATE SOURCE ===")
        LOG.debug(f"Source handle: {source.handle}, Gramps ID: {source.gramps_id}")
''',
    'def update_citation': '''        LOG.debug(f"=== UPDATE CITATION ===")
        LOG.debug(f"Citation handle: {citation.handle}, Gramps ID: {citation.gramps_id}")
''',
    'def update_repository': '''        LOG.debug(f"=== UPDATE REPOSITORY ===")
        LOG.debug(f"Repository handle: {repository.handle}, Gramps ID: {repository.gramps_id}")
''',
    'def update_media': '''        LOG.debug(f"=== UPDATE MEDIA ===")
        LOG.debug(f"Media handle: {media.handle}, Gramps ID: {media.gramps_id}")
''',
    'def update_note': '''        LOG.debug(f"=== UPDATE NOTE ===")
        LOG.debug(f"Note handle: {note.handle}, Gramps ID: {note.gramps_id}")
''',
    'def update_tag': '''        LOG.debug(f"=== UPDATE TAG ===")
        LOG.debug(f"Tag handle: {tag.handle}, Name: {tag.get_name()}")
''',
    'def delete_person': '''        LOG.debug(f"=== DELETE PERSON ===")
        LOG.debug(f"Person handle: {handle}")
''',
    'def delete_family': '''        LOG.debug(f"=== DELETE FAMILY ===")
        LOG.debug(f"Family handle: {handle}")
''',
    'def delete_event': '''        LOG.debug(f"=== DELETE EVENT ===")
        LOG.debug(f"Event handle: {handle}")
''',
    'def delete_place': '''        LOG.debug(f"=== DELETE PLACE ===")
        LOG.debug(f"Place handle: {handle}")
''',
    'def delete_source': '''        LOG.debug(f"=== DELETE SOURCE ===")
        LOG.debug(f"Source handle: {handle}")
''',
    'def delete_citation': '''        LOG.debug(f"=== DELETE CITATION ===")
        LOG.debug(f"Citation handle: {handle}")
''',
    'def delete_repository': '''        LOG.debug(f"=== DELETE REPOSITORY ===")
        LOG.debug(f"Repository handle: {handle}")
''',
    'def delete_media': '''        LOG.debug(f"=== DELETE MEDIA ===")
        LOG.debug(f"Media handle: {handle}")
''',
    'def delete_note': '''        LOG.debug(f"=== DELETE NOTE ===")
        LOG.debug(f"Note handle: {handle}")
''',
    'def delete_tag': '''        LOG.debug(f"=== DELETE TAG ===")
        LOG.debug(f"Tag handle: {handle}")
''',
}

# Track what we've added
added_logging = []

# Add logging to each method
for method_signature, logging_code in logging_additions.items():
    # Find the method definition
    pattern = rf'({method_signature}[^:]*:\s*\n)'
    
    # Check if method exists
    if re.search(pattern, content):
        # Check if logging already exists (avoid duplicates)
        if not re.search(pattern + r'\s*LOG\.debug', content):
            # Add logging right after the method definition
            content = re.sub(
                pattern,
                r'\1' + logging_code,
                content,
                count=1
            )
            added_logging.append(method_signature)
        else:
            print(f"Logging already exists for {method_signature}")
    else:
        print(f"Method not found: {method_signature}")

# Write the modified content back
with open('postgresqlenhanced_with_logging.py', 'w') as f:
    f.write(content)

print(f"\nAdded logging to {len(added_logging)} methods:")
for method in added_logging:
    print(f"  - {method}")

print("\nNew file created: postgresqlenhanced_with_logging.py")
print("\nTo apply changes:")
print("  1. Review: diff postgresqlenhanced.py postgresqlenhanced_with_logging.py")
print("  2. Apply: mv postgresqlenhanced_with_logging.py postgresqlenhanced.py")
print("  3. Install: cp postgresqlenhanced.py ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/")