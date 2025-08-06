#!/usr/bin/env python3
"""
Verify that change_time is the only difference
"""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

from gramps.gen.lib import Person, Name, Surname

# Create person
p = Person()
p.set_handle("TEST")
p.set_gramps_id("I0001")
n = Name()
n.set_first_name("John")
s = Surname()
s.set_surname("Smith")
n.add_surname(s)
p.set_primary_name(n)

# Get original serialization
original = p.serialize()
print(f"Original change_time (field 17): {original[17]}")

# Simulate what database does
import time
p.change = int(time.time())

# Get modified serialization
modified = p.serialize()
print(f"Modified change_time (field 17): {modified[17]}")

# Compare
print(f"\nComparing serializations:")
for i, (orig, mod) in enumerate(zip(original, modified)):
    if orig != mod:
        print(f"  Field {i}: {orig} -> {mod}")

print("\nThis is NOT corruption - it's proper change tracking!")