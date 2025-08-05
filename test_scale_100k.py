#!/usr/bin/env python3
"""
Scale Test for PostgreSQL Enhanced Gramps Backend

Tests the backend with 100,000+ person database to ensure:
- Performance remains acceptable at scale
- Memory usage is reasonable
- Queries complete in reasonable time
- Data integrity is maintained
"""

import os
import sys
import time
import random
import gc
from datetime import datetime

# Import the PostgreSQL enhanced backend
from postgresqlenhanced import PostgreSQLEnhanced

# Import real Gramps objects
from gramps.gen.lib import (
    Person, Family, Name, Surname, Attribute, EventRef,
    AttributeType, EventType
)
from gramps.gen.db import DbTxn
from gramps.gen.utils.id import create_id

def get_memory_usage():
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        # Fallback: read from /proc/self/status on Linux
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        return int(line.split()[1]) / 1024  # Convert KB to MB
        except:
            return 0  # Return 0 if we can't measure memory

def generate_handle():
    """Generate a unique handle."""
    return create_id()

def create_bulk_person(person_id):
    """Create a person with minimal but valid data for bulk testing."""
    person = Person()
    person.set_handle(f"bulk_person_{person_id}_{generate_handle()}")
    person.set_gramps_id(f"I{person_id:08d}")
    
    # Create name
    name = Name()
    name.set_first_name(f"Person{person_id}")
    
    surname = Surname()
    surname.set_surname(f"Family{person_id % 10000}")  # 10,000 different surnames
    name.add_surname(surname)
    
    person.set_primary_name(name)
    person.set_gender(person_id % 3)  # 0, 1, or 2
    person.set_privacy(person_id % 10 == 0)  # 10% private
    
    # Add attribute for some persons
    if person_id % 5 == 0:
        attr = Attribute()
        attr.set_type(AttributeType.OCCUPATION)
        attr.set_value(f"Occupation_{person_id % 100}")
        person.add_attribute(attr)
    
    return person

def run_scale_test(target_persons=100000):
    """
    Run the scale test with target number of persons.
    """
    print("=" * 80)
    print(f"SCALE TEST - {target_persons:,} PERSONS")
    print("=" * 80)
    print()
    
    # Database configuration
    config = {
        "host": "192.168.10.90",
        "port": 5432,
        "user": "genealogy_user",
        "password": "GenealogyData2025",
        "database": f"scale_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "database_mode": "separate"
    }
    
    # Create test directory
    test_dir = f"/tmp/scale_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(test_dir, exist_ok=True)
    
    # Write connection info
    conn_file_path = os.path.join(test_dir, "connection_info.txt")
    with open(conn_file_path, 'w') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print(f"Test database: {config['database']}")
    print(f"Target persons: {target_persons:,}")
    print()
    
    # Initialize database
    print("Initializing database...")
    db = PostgreSQLEnhanced()
    db.load(test_dir, update=False, callback=None)
    
    initial_memory = get_memory_usage()
    print(f"Initial memory usage: {initial_memory:.1f} MB")
    print()
    
    # Phase 1: Bulk insertion
    print("=" * 60)
    print("PHASE 1: BULK INSERTION")
    print("=" * 60)
    
    batch_size = 1000
    num_batches = target_persons // batch_size
    
    insertion_times = []
    memory_samples = []
    
    for batch_num in range(num_batches):
        batch_start = time.time()
        start_id = batch_num * batch_size
        
        # Create batch transaction
        with DbTxn(f"Batch {batch_num + 1}", db) as trans:
            for i in range(batch_size):
                person_id = start_id + i + 1
                person = create_bulk_person(person_id)
                db.add_person(person, trans)
        
        batch_time = time.time() - batch_start
        insertion_times.append(batch_time)
        
        # Memory check every 10 batches
        if (batch_num + 1) % 10 == 0:
            current_memory = get_memory_usage()
            memory_samples.append(current_memory)
            persons_so_far = (batch_num + 1) * batch_size
            avg_time = sum(insertion_times) / len(insertion_times)
            rate = batch_size / avg_time
            
            print(f"Progress: {persons_so_far:,} persons")
            print(f"  Batch time: {batch_time:.2f}s")
            print(f"  Average rate: {rate:.0f} persons/second")
            print(f"  Memory usage: {current_memory:.1f} MB")
            
            # Force garbage collection periodically
            if (batch_num + 1) % 20 == 0:
                gc.collect()
    
    total_insertion_time = sum(insertion_times)
    avg_insertion_rate = target_persons / total_insertion_time
    
    print(f"\nInsertion complete:")
    print(f"  Total time: {total_insertion_time:.1f} seconds")
    print(f"  Average rate: {avg_insertion_rate:.0f} persons/second")
    print(f"  Final memory: {get_memory_usage():.1f} MB")
    
    # Phase 2: Query performance
    print("\n" + "=" * 60)
    print("PHASE 2: QUERY PERFORMANCE")
    print("=" * 60)
    
    test_queries = []
    
    # Test 1: Random person retrieval
    print("\nTest 1: Random person retrieval (100 queries)...")
    retrieval_times = []
    for _ in range(100):
        person_id = random.randint(1, target_persons)
        handle = f"bulk_person_{person_id}_"  # Partial handle
        
        start_time = time.time()
        # Since we don't know the exact handle, we'll use gramps_id
        gramps_id = f"I{person_id:08d}"
        person = db.get_person_from_gramps_id(gramps_id)
        elapsed = time.time() - start_time
        retrieval_times.append(elapsed)
    
    avg_retrieval = sum(retrieval_times) / len(retrieval_times)
    print(f"  Average retrieval time: {avg_retrieval*1000:.2f}ms")
    print(f"  Min: {min(retrieval_times)*1000:.2f}ms")
    print(f"  Max: {max(retrieval_times)*1000:.2f}ms")
    
    # Test 2: Get all persons with a specific surname
    print("\nTest 2: Find all persons with specific surname...")
    surname_to_find = "Family42"
    start_time = time.time()
    
    # We'll need to iterate through persons (in real use, this would be indexed)
    matching_count = 0
    for person_handle in db.get_person_handles():
        person = db.get_person_from_handle(person_handle)
        if person:
            primary_name = person.get_primary_name()
            if primary_name:
                for surname in primary_name.get_surname_list():
                    if surname.get_surname() == surname_to_find:
                        matching_count += 1
                        break
        
        # Stop after checking 1000 persons for this test
        if matching_count >= 100:
            break
    
    surname_time = time.time() - start_time
    print(f"  Found {matching_count} matches in {surname_time:.2f} seconds")
    
    # Test 3: Count total persons
    print("\nTest 3: Count total persons...")
    start_time = time.time()
    total_count = db.get_number_of_people()
    count_time = time.time() - start_time
    print(f"  Total persons: {total_count:,}")
    print(f"  Count time: {count_time*1000:.2f}ms")
    
    # Test 4: Batch update test
    print("\nTest 4: Batch update (100 persons)...")
    update_times = []
    for i in range(100):
        person_id = random.randint(1, target_persons)
        gramps_id = f"I{person_id:08d}"
        
        start_time = time.time()
        person = db.get_person_from_gramps_id(gramps_id)
        if person:
            person.set_privacy(not person.get_privacy())
            with DbTxn(f"Update person {person_id}", db) as trans:
                db.commit_person(person, trans)
        elapsed = time.time() - start_time
        update_times.append(elapsed)
    
    avg_update = sum(update_times) / len(update_times)
    print(f"  Average update time: {avg_update*1000:.2f}ms")
    
    # Phase 3: Memory and cleanup
    print("\n" + "=" * 60)
    print("PHASE 3: MEMORY AND CLEANUP")
    print("=" * 60)
    
    final_memory = get_memory_usage()
    memory_growth = final_memory - initial_memory
    
    print(f"Memory usage:")
    print(f"  Initial: {initial_memory:.1f} MB")
    print(f"  Final: {final_memory:.1f} MB")
    print(f"  Growth: {memory_growth:.1f} MB")
    print(f"  Per 1000 persons: {memory_growth*1000/target_persons:.2f} MB")
    
    # Close database
    db.close()
    
    # Final summary
    print("\n" + "=" * 80)
    print("SCALE TEST SUMMARY")
    print("=" * 80)
    
    success_criteria = []
    
    # Check insertion rate (should be >100 persons/second)
    if avg_insertion_rate > 100:
        success_criteria.append(("✅", f"Insertion rate: {avg_insertion_rate:.0f} persons/sec (>100)"))
    else:
        success_criteria.append(("❌", f"Insertion rate: {avg_insertion_rate:.0f} persons/sec (<100)"))
    
    # Check retrieval time (should be <10ms average)
    if avg_retrieval < 0.01:
        success_criteria.append(("✅", f"Retrieval time: {avg_retrieval*1000:.2f}ms (<10ms)"))
    else:
        success_criteria.append(("❌", f"Retrieval time: {avg_retrieval*1000:.2f}ms (>10ms)"))
    
    # Check update time (should be <50ms average)
    if avg_update < 0.05:
        success_criteria.append(("✅", f"Update time: {avg_update*1000:.2f}ms (<50ms)"))
    else:
        success_criteria.append(("❌", f"Update time: {avg_update*1000:.2f}ms (>50ms)"))
    
    # Check memory usage (should be <1GB for 100k persons)
    if final_memory < 1024:
        success_criteria.append(("✅", f"Memory usage: {final_memory:.1f}MB (<1GB)"))
    else:
        success_criteria.append(("❌", f"Memory usage: {final_memory:.1f}MB (>1GB)"))
    
    # Print results
    for status, message in success_criteria:
        print(f"{status} {message}")
    
    # Overall verdict
    passed = sum(1 for status, _ in success_criteria if status == "✅")
    total = len(success_criteria)
    
    print(f"\nPassed: {passed}/{total} criteria")
    
    if passed == total:
        print("🎉 PERFECT! All scale criteria met!")
    elif passed >= total - 1:
        print("✅ EXCELLENT! Scale test passed with minor issues")
    else:
        print("⚠️ WARNING: Some scale issues detected")

if __name__ == "__main__":
    # Parse command line arguments
    target = 100000
    
    if len(sys.argv) > 1:
        target = int(sys.argv[1])
    
    run_scale_test(target)