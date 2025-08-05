#!/usr/bin/env python3
"""
Concurrent Access Test for PostgreSQL Enhanced Gramps Backend

Tests the backend with 100+ simultaneous threads performing various operations
to ensure thread-safety and proper transaction isolation.
"""

import os
import sys
import time
import random
import threading
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# Import the PostgreSQL enhanced backend
from postgresqlenhanced import PostgreSQLEnhanced

# Import real Gramps objects
from gramps.gen.lib import (
    Person, Family, Event, Place, Source, Citation, 
    Repository, Media, Note, Tag, Name, Surname, 
    Address, Url, Attribute, EventRef, PlaceRef,
    EventType, AttributeType, NoteType
)
from gramps.gen.db import DbTxn
from gramps.gen.utils.id import create_id

# Thread-safe counters
class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value
    
    def get(self):
        with self.lock:
            return self.value

# Global counters
total_operations = ThreadSafeCounter()
successful_operations = ThreadSafeCounter()
failed_operations = ThreadSafeCounter()
operation_times = []
operation_times_lock = threading.Lock()

def generate_handle():
    """Generate a unique handle."""
    return create_id()

def create_random_person(thread_id, person_num):
    """Create a person with random but valid data."""
    person = Person()
    person.set_handle(f"thread{thread_id}_person{person_num}_{generate_handle()}")
    person.set_gramps_id(f"I{thread_id:03d}{person_num:05d}")
    
    # Create name with potential NULL values (testing our fix)
    name = Name()
    if random.random() > 0.1:  # 90% have first name
        name.set_first_name(f"Thread{thread_id}_{person_num}")
    else:
        name.set_first_name(None)  # Test NULL first name handling
    
    surname = Surname()
    surname.set_surname(f"Surname{thread_id}")
    name.add_surname(surname)
    
    person.set_primary_name(name)
    person.set_gender(random.choice([0, 1, 2]))
    person.set_privacy(random.choice([True, False]))
    
    # Add some attributes
    if random.random() > 0.5:
        attr = Attribute()
        attr.set_type(AttributeType.OCCUPATION)
        attr.set_value(f"Job_{thread_id}_{person_num}")
        person.add_attribute(attr)
    
    return person

def create_random_family(thread_id, family_num):
    """Create a family with random data."""
    family = Family()
    family.set_handle(f"thread{thread_id}_family{family_num}_{generate_handle()}")
    family.set_gramps_id(f"F{thread_id:03d}{family_num:05d}")
    
    # Random parents
    if random.random() > 0.3:
        family.set_father_handle(f"father_{generate_handle()}")
    if random.random() > 0.3:
        family.set_mother_handle(f"mother_{generate_handle()}")
    
    family.set_privacy(random.choice([True, False]))
    
    return family

def create_random_note(thread_id, note_num):
    """Create a note with random content."""
    note = Note()
    note.set_handle(f"thread{thread_id}_note{note_num}_{generate_handle()}")
    note.set_gramps_id(f"N{thread_id:03d}{note_num:05d}")
    
    text = f"Note from thread {thread_id}, number {note_num}\n"
    text += "Random content: " + "x" * random.randint(10, 1000)
    note.set(text)
    
    note.set_type(random.choice([NoteType.GENERAL, NoteType.RESEARCH]))
    note.set_format(random.choice([0, 1]))
    
    return note

def worker_thread(thread_id, db_path, num_operations, operation_mix):
    """
    Worker thread that performs various database operations.
    
    operation_mix: dict with operation types and their weights
    """
    results = {
        'thread_id': thread_id,
        'success': 0,
        'failed': 0,
        'errors': [],
        'times': []
    }
    
    # Add small random delay to prevent connection storms
    time.sleep(random.uniform(0, 0.5))
    
    # Initialize database connection for this thread
    db = PostgreSQLEnhanced()
    
    try:
        # Load the database with retries
        max_retries = 3
        for retry in range(max_retries):
            try:
                db.load(db_path, update=False, callback=None)
                break
            except Exception as e:
                if retry < max_retries - 1:
                    time.sleep(random.uniform(0.1, 0.5))
                else:
                    raise e
        
        # Perform operations
        for op_num in range(num_operations):
            # Choose operation type based on weights
            op_type = random.choices(
                list(operation_mix.keys()),
                weights=list(operation_mix.values())
            )[0]
            
            start_time = time.time()
            try:
                if op_type == 'add_person':
                    person = create_random_person(thread_id, op_num)
                    with DbTxn(f"Thread {thread_id} add person", db) as trans:
                        db.add_person(person, trans)
                    
                elif op_type == 'add_family':
                    family = create_random_family(thread_id, op_num)
                    with DbTxn(f"Thread {thread_id} add family", db) as trans:
                        db.add_family(family, trans)
                    
                elif op_type == 'add_note':
                    note = create_random_note(thread_id, op_num)
                    with DbTxn(f"Thread {thread_id} add note", db) as trans:
                        db.add_note(note, trans)
                    
                elif op_type == 'read_person':
                    # Try to read a random person
                    handle = f"thread{random.randint(0, 100)}_person{random.randint(0, 100)}_{generate_handle()}"
                    person = db.get_person_from_handle(handle)
                    # It's OK if it returns None (our fix ensures this)
                    
                elif op_type == 'update_person':
                    # Create and update a person
                    person = create_random_person(thread_id, op_num)
                    handle = person.get_handle()
                    
                    with DbTxn(f"Thread {thread_id} add for update", db) as trans:
                        db.add_person(person, trans)
                    
                    # Retrieve it fresh (to avoid stale data issues)
                    person = db.get_person_from_handle(handle)
                    if person:
                        # Now update it
                        person.set_privacy(not person.get_privacy())
                        with DbTxn(f"Thread {thread_id} update person", db) as trans:
                            db.commit_person(person, trans)
                
                elapsed = time.time() - start_time
                results['times'].append(elapsed)
                results['success'] += 1
                successful_operations.increment()
                
            except Exception as e:
                import traceback
                elapsed = time.time() - start_time
                results['failed'] += 1
                error_msg = f"{op_type}: {str(e)}"
                results['errors'].append(error_msg)
                failed_operations.increment()
                # Print error immediately for debugging with traceback
                print(f"Thread {thread_id} error in {op_type}: {str(e)}")
                if "concatenate" in str(e):
                    print(f"  Traceback for concatenate error:")
                    traceback.print_exc()
            
            total_operations.increment()
            
    except Exception as e:
        results['errors'].append(f"Thread initialization: {str(e)}")
        results['failed'] = num_operations
        print(f"Thread {thread_id} initialization failed: {str(e)}")
        
    finally:
        try:
            db.close()
        except:
            pass
    
    return results

def run_concurrent_test(num_threads=100, operations_per_thread=10):
    """
    Run the concurrent access test.
    """
    print("=" * 80)
    print("CONCURRENT ACCESS TEST")
    print(f"Threads: {num_threads}")
    print(f"Operations per thread: {operations_per_thread}")
    print(f"Total operations: {num_threads * operations_per_thread}")
    print("=" * 80)
    print()
    
    # Database configuration
    config = {
        "host": "192.168.10.90",
        "port": 5432,
        "user": "genealogy_user",
        "password": "GenealogyData2025",
        "database": f"concurrent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "database_mode": "separate"
    }
    
    # Create test directory
    test_dir = f"/tmp/concurrent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(test_dir, exist_ok=True)
    
    # Write connection info
    conn_file_path = os.path.join(test_dir, "connection_info.txt")
    with open(conn_file_path, 'w') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print(f"Test database: {config['database']}")
    print(f"Test directory: {test_dir}")
    print()
    
    # Initialize the database once
    print("Initializing database...")
    init_db = PostgreSQLEnhanced()
    init_db.load(test_dir, update=False, callback=None)
    init_db.close()
    print("Database initialized")
    print()
    
    # Operation mix (weights for different operations)
    operation_mix = {
        'add_person': 40,      # 40% adds
        'add_family': 20,      # 20% family adds  
        'add_note': 10,        # 10% note adds
        'read_person': 20,     # 20% reads
        'update_person': 10    # 10% updates
    }
    
    # Start concurrent threads
    print(f"Starting {num_threads} threads...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for thread_id in range(num_threads):
            future = executor.submit(
                worker_thread,
                thread_id,
                test_dir,
                operations_per_thread,
                operation_mix
            )
            futures.append(future)
        
        # Wait for all threads to complete
        thread_results = []
        errors_by_type = defaultdict(int)
        
        for future in as_completed(futures):
            try:
                result = future.result(timeout=60)
                thread_results.append(result)
                
                # Count error types
                for error in result['errors']:
                    error_type = error.split(':')[0]
                    errors_by_type[error_type] += 1
                    
            except Exception as e:
                print(f"Thread failed with exception: {e}")
    
    elapsed_time = time.time() - start_time
    
    # Analyze results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    total_ops = total_operations.get()
    successful_ops = successful_operations.get()
    failed_ops = failed_operations.get()
    
    print(f"Total operations attempted: {total_ops}")
    print(f"Successful operations: {successful_ops}")
    print(f"Failed operations: {failed_ops}")
    print(f"Success rate: {successful_ops/total_ops*100:.1f}%")
    print(f"Total time: {elapsed_time:.2f} seconds")
    print(f"Operations per second: {total_ops/elapsed_time:.0f}")
    print()
    
    # Show error breakdown if any
    if errors_by_type:
        print("Error breakdown:")
        for error_type, count in sorted(errors_by_type.items()):
            print(f"  {error_type}: {count}")
        print()
    
    # Thread completion stats
    completed_threads = len([r for r in thread_results if r['failed'] == 0])
    print(f"Threads completed without errors: {completed_threads}/{num_threads}")
    
    # Performance stats
    all_times = []
    for result in thread_results:
        all_times.extend(result['times'])
    
    if all_times:
        avg_time = sum(all_times) / len(all_times)
        min_time = min(all_times)
        max_time = max(all_times)
        print(f"\nOperation timing:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Min: {min_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")
    
    # Final verdict
    print("\n" + "=" * 60)
    if failed_ops == 0:
        print("✅ PERFECT! No failures with concurrent access!")
    elif successful_ops/total_ops > 0.99:
        print("✅ EXCELLENT! >99% success rate with concurrent access")
    elif successful_ops/total_ops > 0.95:
        print("⚠️ GOOD: >95% success rate, but some issues detected")
    else:
        print("❌ FAILED: Significant issues with concurrent access")
    print("=" * 60)

if __name__ == "__main__":
    # Parse command line arguments
    num_threads = 100
    ops_per_thread = 10
    
    if len(sys.argv) > 1:
        num_threads = int(sys.argv[1])
    if len(sys.argv) > 2:
        ops_per_thread = int(sys.argv[2])
    
    run_concurrent_test(num_threads, ops_per_thread)