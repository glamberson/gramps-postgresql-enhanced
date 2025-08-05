#!/usr/bin/env python3
"""Fix mock_gramps.py by adding missing methods."""

import re

# Read the current mock_gramps.py
with open('mock_gramps.py', 'r') as f:
    content = f.read()

# Find the MockPerson class and add missing methods
person_additions = '''
    def add_url(self, url):
        """Add URL to person."""
        pass
    
    def add_event_ref(self, event_ref):
        """Add event reference."""
        pass
'''

# Find the MockName class and add missing methods
name_additions = '''
    def get_first_name(self):
        return self.first_name
    
    def get_surname_list(self):
        return self.surname_list
'''

# Find the MockSurname class and add missing methods
surname_additions = '''
    def get_surname(self):
        return self.surname
'''

# Find the MockChildRef class and add missing methods
childref_additions = '''
    def set_reference_handle(self, handle):
        self.ref = handle
'''

# Find the MockSource class and add missing methods
source_additions = '''
    def set_publication_info(self, info):
        self.pubinfo = info
'''

# Find the MockRepository class and add missing methods
repository_additions = '''
    def set_name(self, name):
        self.name = name
'''

# Find the MockMedia class and add missing methods
media_additions = '''
    def set_path(self, path):
        self.path = path
'''

# Find the MockNote class and add missing methods
note_additions = '''
    def set_styledtext(self, text):
        self.text = text
'''

# Find the MockTag class and add missing methods
tag_additions = '''
    def set_color(self, color):
        self.color = color
'''

# Find the MockEvent class and add MARRIAGE constant
event_fix = '''class MockEvent:
    # Event type constants
    BIRTH = 1
    DEATH = 2
    MARRIAGE = 3
    
    def __init__(self):'''

# Find the MockFamily class and add missing methods
family_additions = '''
    def get_handle(self):
        return self.handle
    
    def get_father_handle(self):
        return self.father_handle
    
    def get_mother_handle(self):
        return self.mother_handle
    
    def get_child_ref_list(self):
        return self.child_ref_list
    
    def add_event_ref(self, event_ref):
        pass
'''

# Find the MockEvent class and add missing methods
event_additions = '''
    def get_handle(self):
        return self.handle
    
    def set_place_handle(self, handle):
        self.place_handle = handle
    
    def get_place_handle(self):
        return getattr(self, 'place_handle', None)
'''

# Find the MockPlace class and add missing methods
place_additions = '''
    def set_name(self, name):
        self.name = name
'''

# Apply fixes
# Fix MockPerson
content = re.sub(
    r'(class MockPerson:.*?def get_gender\(self\):\s+return self\.gender)',
    r'\1' + person_additions,
    content,
    flags=re.DOTALL
)

# Fix MockName
content = re.sub(
    r'(class MockName:.*?def add_surname\(self, surname\):\s+self\.surname_list\.append\(surname\))',
    r'\1' + name_additions,
    content,
    flags=re.DOTALL
)

# Fix MockSurname
content = re.sub(
    r'(class MockSurname:.*?def set_surname\(self, surname\):\s+self\.surname = surname)',
    r'\1' + surname_additions,
    content,
    flags=re.DOTALL
)

# Fix MockChildRef
content = re.sub(
    r'(class MockChildRef:.*?self\.ref = None)',
    r'\1' + childref_additions,
    content,
    flags=re.DOTALL
)

# Fix MockSource
content = re.sub(
    r'(class MockSource:.*?def get_author\(self\):\s+return self\.author)',
    r'\1' + source_additions,
    content,
    flags=re.DOTALL
)

# Fix MockRepository
content = re.sub(
    r'(class MockRepository:.*?def set_gramps_id\(self, gramps_id\):\s+self\.gramps_id = gramps_id)',
    r'\1' + repository_additions,
    content,
    flags=re.DOTALL
)

# Fix MockMedia
content = re.sub(
    r'(class MockMedia:.*?def set_gramps_id\(self, gramps_id\):\s+self\.gramps_id = gramps_id)',
    r'\1' + media_additions,
    content,
    flags=re.DOTALL
)

# Fix MockNote
content = re.sub(
    r'(class MockNote:.*?def set_gramps_id\(self, gramps_id\):\s+self\.gramps_id = gramps_id)',
    r'\1' + note_additions,
    content,
    flags=re.DOTALL
)

# Fix MockTag
content = re.sub(
    r'(class MockTag:.*?def get_name\(self\):\s+return self\.name)',
    r'\1' + tag_additions,
    content,
    flags=re.DOTALL
)

# Fix MockEvent - add MARRIAGE constant
content = re.sub(
    r'class MockEvent:\s+def __init__\(self\):',
    event_fix,
    content
)

# Fix MockFamily
content = re.sub(
    r'(class MockFamily:.*?def add_child_ref\(self, ref\):\s+self\.child_ref_list\.append\(ref\))',
    r'\1' + family_additions,
    content,
    flags=re.DOTALL
)

# Add more methods to MockEvent
content = re.sub(
    r'(class MockEvent:.*?def get_description\(self\):\s+return self\.description)',
    r'\1' + event_additions,
    content,
    flags=re.DOTALL
)

# Fix MockPlace
content = re.sub(
    r'(class MockPlace:.*?def get_code\(self\):\s+return self\.code)',
    r'\1' + place_additions,
    content,
    flags=re.DOTALL
)

# Add iter_people to MockDBAPI
dbapi_additions = '''
        # Add iterator methods for people
        self.iter_people = MagicMock(return_value=iter([]))
'''

content = re.sub(
    r'(self\.iter_source_handles = MagicMock\(return_value=iter\(\[\]\)\))',
    r'\1' + dbapi_additions,
    content
)

# Write the fixed content
with open('mock_gramps.py', 'w') as f:
    f.write(content)

print("Fixed mock_gramps.py with missing methods")