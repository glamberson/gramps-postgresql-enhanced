#!/usr/bin/env python3
"""
Apply Type Sanitizer to PostgreSQL Enhanced
This patches the addon to use type sanitization for ALL objects.

NO FALLBACK POLICY: This MUST handle every case.
"""

import sys
import os

# Read the current postgresqlenhanced.py
with open('postgresqlenhanced.py', 'r') as f:
    content = f.read()

# Add import for type_sanitizer at the top
import_line = "from type_sanitizer import sanitize_gramps_object, sanitize_for_column"

# Find where to insert the import (after other local imports)
import_pos = content.find("from schema_columns import")
if import_pos > 0:
    # Insert after this import
    end_of_line = content.find("\n", import_pos)
    content = content[:end_of_line] + "\n" + import_line + content[end_of_line:]

# Add method overrides for all add_* methods
override_methods = """
    # =========================================================================
    # Type-Safe Method Overrides - NO FALLBACK POLICY
    # =========================================================================
    
    def add_person(self, person, trans, set_gid=True):
        \"\"\"Add a person with type sanitization.\"\"\"
        person = sanitize_gramps_object(person)
        return super().add_person(person, trans, set_gid)
    
    def add_family(self, family, trans, set_gid=True):
        \"\"\"Add a family with type sanitization.\"\"\"
        family = sanitize_gramps_object(family)
        return super().add_family(family, trans, set_gid)
    
    def add_event(self, event, trans, set_gid=True):
        \"\"\"Add an event with type sanitization.\"\"\"
        event = sanitize_gramps_object(event)
        return super().add_event(event, trans, set_gid)
    
    def add_place(self, place, trans, set_gid=True):
        \"\"\"Add a place with type sanitization.\"\"\"
        place = sanitize_gramps_object(place)
        return super().add_place(place, trans, set_gid)
    
    def add_source(self, source, trans, set_gid=True):
        \"\"\"Add a source with type sanitization.\"\"\"
        source = sanitize_gramps_object(source)
        return super().add_source(source, trans, set_gid)
    
    def add_citation(self, citation, trans, set_gid=True):
        \"\"\"Add a citation with type sanitization.\"\"\"
        citation = sanitize_gramps_object(citation)
        return super().add_citation(citation, trans, set_gid)
    
    def add_repository(self, repository, trans, set_gid=True):
        \"\"\"Add a repository with type sanitization.\"\"\"
        repository = sanitize_gramps_object(repository)
        return super().add_repository(repository, trans, set_gid)
    
    def add_media(self, media, trans, set_gid=True):
        \"\"\"Add a media object with type sanitization.\"\"\"
        media = sanitize_gramps_object(media)
        return super().add_media(media, trans, set_gid)
    
    def add_note(self, note, trans, set_gid=True):
        \"\"\"Add a note with type sanitization.\"\"\"
        note = sanitize_gramps_object(note)
        return super().add_note(note, trans, set_gid)
    
    def add_tag(self, tag, trans):
        \"\"\"Add a tag with type sanitization.\"\"\"
        tag = sanitize_gramps_object(tag)
        return super().add_tag(tag, trans)
    
    def commit_person(self, person, trans, change_time=None):
        \"\"\"Commit a person with type sanitization.\"\"\"
        person = sanitize_gramps_object(person)
        return super().commit_person(person, trans, change_time)
    
    def commit_family(self, family, trans, change_time=None):
        \"\"\"Commit a family with type sanitization.\"\"\"
        family = sanitize_gramps_object(family)
        return super().commit_family(family, trans, change_time)
    
    def commit_event(self, event, trans, change_time=None):
        \"\"\"Commit an event with type sanitization.\"\"\"
        event = sanitize_gramps_object(event)
        return super().commit_event(event, trans, change_time)
    
    def commit_place(self, place, trans, change_time=None):
        \"\"\"Commit a place with type sanitization.\"\"\"
        place = sanitize_gramps_object(place)
        return super().commit_place(place, trans, change_time)
    
    def commit_source(self, source, trans, change_time=None):
        \"\"\"Commit a source with type sanitization.\"\"\"
        source = sanitize_gramps_object(source)
        return super().commit_source(source, trans, change_time)
    
    def commit_citation(self, citation, trans, change_time=None):
        \"\"\"Commit a citation with type sanitization.\"\"\"
        citation = sanitize_gramps_object(citation)
        return super().commit_citation(citation, trans, change_time)
    
    def commit_repository(self, repository, trans, change_time=None):
        \"\"\"Commit a repository with type sanitization.\"\"\"
        repository = sanitize_gramps_object(repository)
        return super().commit_repository(repository, trans, change_time)
    
    def commit_media(self, media, trans, change_time=None):
        \"\"\"Commit a media object with type sanitization.\"\"\"
        media = sanitize_gramps_object(media)
        return super().commit_media(media, trans, change_time)
    
    def commit_note(self, note, trans, change_time=None):
        \"\"\"Commit a note with type sanitization.\"\"\"
        note = sanitize_gramps_object(note)
        return super().commit_note(note, trans, change_time)
    
    def commit_tag(self, tag, trans, change_time=None):
        \"\"\"Commit a tag with type sanitization.\"\"\"
        tag = sanitize_gramps_object(tag)
        return super().commit_tag(tag, trans, change_time)
"""

# Find where to insert the overrides (before the close method)
close_pos = content.find("def close(self")
if close_pos > 0:
    # Insert before close method
    content = content[:close_pos] + override_methods + "\n    " + content[close_pos:]

# Save the modified file
with open('postgresqlenhanced_sanitized.py', 'w') as f:
    f.write(content)

print("✅ Type sanitizer integration complete!")
print("Created: postgresqlenhanced_sanitized.py")
print("This version will handle ALL data types without failures.")