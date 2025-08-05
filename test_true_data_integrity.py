#!/usr/bin/env python3
"""
TRUE Data Integrity Test - Accounts for expected change_time updates
"""
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, '/usr/lib/python3/dist-packages')
from gramps.gen.lib import Person, Name, Surname
from gramps.gen.db import DbTxn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from postgresqlenhanced import PostgreSQLEnhanced

DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def compare_ignoring_change_time(data1, data2):
    """Compare serialized data ignoring change_time field."""
    if len(data1) != len(data2):
        return False
    
    for i, (d1, d2) in enumerate(zip(data1, data2)):
        if i == 17:  # Skip change_time field
            continue
        if d1 != d2:
            return False
    return True

print("=" * 80)
print("TRUE DATA INTEGRITY TEST")
print("Properly accounting for change_time updates")
print("=" * 80)

# Setup database
db = PostgreSQLEnhanced()
test_db_name = f"integrity_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
test_dir = tempfile.mkdtemp(prefix="integrity_test_")

settings_file = os.path.join(test_dir, "connection_info.txt")
with open(settings_file, 'w') as f:
    f.write(f"host={DB_CONFIG['host']}\n")
    f.write(f"port={DB_CONFIG['port']}\n")
    f.write(f"user={DB_CONFIG['user']}\n")
    f.write(f"password={DB_CONFIG['password']}\n")
    f.write(f"database_name={test_db_name}\n")
    f.write("database_mode=separate\n")

db.load(directory=test_dir, callback=None, mode="w")

print("\nTesting 100 people for TRUE data integrity...")
corrupted = []

for i in range(100):
    person = Person()
    handle = f"TEST{i:03d}"
    person.set_handle(handle)
    person.set_gramps_id(f"I{i:04d}")
    person.set_gender(Person.MALE if i % 2 == 0 else Person.FEMALE)
    
    name = Name()
    name.set_first_name(f"Person{i}")
    surname = Surname()
    surname.set_surname(f"Family{i % 10}")
    name.add_surname(surname)
    person.set_primary_name(name)
    
    # Store original (ignoring change_time)
    original = person.serialize()
    
    # Store in database
    with DbTxn(f"Store {handle}", db) as trans:
        db.add_person(person, trans)
    
    # Retrieve
    retrieved = db.get_person_from_handle(handle)
    
    if not retrieved:
        corrupted.append(f"{handle} - not retrieved")
    else:
        retrieved_data = retrieved.serialize()
        
        # Compare ignoring change_time
        if not compare_ignoring_change_time(original, retrieved_data):
            corrupted.append(handle)
            print(f"  Real corruption in {handle}:")
            for j, (o, r) in enumerate(zip(original, retrieved_data)):
                if j != 17 and o != r:  # Skip change_time
                    print(f"    Field {j}: {o} -> {r}")

# Results
print("\n" + "=" * 80)
if corrupted:
    print(f"❌ TRUE CORRUPTION FOUND in {len(corrupted)}/100 records:")
    for c in corrupted[:5]:
        print(f"  - {c}")
else:
    print("✅ NO TRUE CORRUPTION - All data preserved perfectly!")
    print("   (change_time updates are expected behavior)")

if db.is_open():
    db.close()

print(f"\nTest database: {test_db_name}")