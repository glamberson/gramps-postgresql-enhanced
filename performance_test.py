#!/usr/bin/env python3
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025 Greg Lamberson
#

"""
Comprehensive performance testing for PostgreSQL Enhanced addon.

Tests various workloads and measures performance metrics.
"""

import os
import sys
import time
import random
import string
import statistics
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Add plugin directory to path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# Import Gramps modules
from gramps.gen.lib import Person, Family, Event, Place, Source, Citation
from gramps.gen.lib import Name, Surname, Date, EventRef, EventType
from gramps.gen.db import DbTxn
from gramps.gen.lib.serialize import JSONSerializer

# Import PostgreSQL Enhanced
from postgresqlenhanced import PostgreSQLEnhanced

class PerformanceTester:
    """Comprehensive performance testing for PostgreSQL Enhanced."""
    
    def __init__(self, db_name=None):
        self.db_name = db_name or f"perf_test_{int(time.time())}"
        self.results = defaultdict(list)
        self.db = None
        
    def setup(self):
        """Set up test database."""
        print(f"Setting up performance test database: {self.db_name}")
        
        # Create temp directory for config
        import tempfile
        self.test_dir = tempfile.mkdtemp(prefix='gramps_perf_')
        
        # Create connection config
        config_path = os.path.join(self.test_dir, 'connection_info.txt')
        with open(config_path, 'w') as f:
            f.write("""# Performance test configuration
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = separate
""")
        
        # Initialize database
        self.db = PostgreSQLEnhanced()
        self.db.load(self.test_dir, None, None)
        
    def teardown(self):
        """Clean up test database."""
        if self.db:
            self.db.close()
            
        # Drop test database
        import psycopg
        try:
            conn = psycopg.connect(
                "postgresql://genealogy_user:GenealogyData2025@192.168.10.90:5432/postgres"
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS {self.db_name}")
            conn.close()
        except:
            pass
            
        # Clean up temp directory
        import shutil
        if hasattr(self, 'test_dir'):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def generate_random_person(self):
        """Generate a random person with realistic data."""
        person = Person()
        
        # Random name
        first_names = ['John', 'Jane', 'William', 'Mary', 'James', 'Sarah', 
                       'Robert', 'Emma', 'Michael', 'Olivia']
        surnames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 
                   'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        name = Name()
        name.set_first_name(random.choice(first_names))
        surname = Surname()
        surname.set_surname(random.choice(surnames))
        name.add_surname(surname)
        person.set_primary_name(name)
        
        # Random gender
        person.set_gender(random.choice([Person.MALE, Person.FEMALE]))
        
        # Random birth year
        birth_year = random.randint(1800, 2020)
        
        # Random gramps_id
        person.set_gramps_id(f"I{random.randint(10000, 99999)}")
        
        return person
    
    def test_bulk_insert(self, count=1000):
        """Test bulk person insertion."""
        print(f"\n=== Testing bulk insert of {count} persons ===")
        
        persons = [self.generate_random_person() for _ in range(count)]
        
        start_time = time.time()
        
        with DbTxn(f"Bulk insert {count} persons", self.db) as trans:
            for person in persons:
                self.db.add_person(person, trans)
        
        duration = time.time() - start_time
        rate = count / duration
        
        print(f"Inserted {count} persons in {duration:.2f}s ({rate:.1f} persons/sec)")
        
        self.results['bulk_insert'].append({
            'count': count,
            'duration': duration,
            'rate': rate
        })
        
        return persons
    
    def test_individual_inserts(self, count=100):
        """Test individual person insertions with separate transactions."""
        print(f"\n=== Testing individual insert of {count} persons ===")
        
        persons = [self.generate_random_person() for _ in range(count)]
        
        start_time = time.time()
        
        for i, person in enumerate(persons):
            with DbTxn(f"Insert person {i+1}", self.db) as trans:
                self.db.add_person(person, trans)
        
        duration = time.time() - start_time
        rate = count / duration
        
        print(f"Inserted {count} persons individually in {duration:.2f}s ({rate:.1f} persons/sec)")
        
        self.results['individual_insert'].append({
            'count': count,
            'duration': duration,
            'rate': rate
        })
    
    def test_search_performance(self, search_count=100):
        """Test search performance."""
        print(f"\n=== Testing search performance ({search_count} searches) ===")
        
        # Get all person handles
        handles = list(self.db.iter_person_handles())
        if not handles:
            print("No persons to search!")
            return
            
        # Test handle lookups
        start_time = time.time()
        for _ in range(search_count):
            handle = random.choice(handles)
            person = self.db.get_person_from_handle(handle)
        
        duration = time.time() - start_time
        rate = search_count / duration
        
        print(f"Handle lookups: {search_count} in {duration:.2f}s ({rate:.1f} lookups/sec)")
        
        self.results['handle_lookup'].append({
            'count': search_count,
            'duration': duration,
            'rate': rate
        })
        
        # Test surname searches
        start_time = time.time()
        surnames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
        
        for surname in surnames:
            count = 0
            for handle in self.db.iter_person_handles():
                person = self.db.get_person_from_handle(handle)
                if person.get_primary_name().get_surname() == surname:
                    count += 1
        
        duration = time.time() - start_time
        
        print(f"Surname searches: {len(surnames)} surnames in {duration:.2f}s")
        
        self.results['surname_search'].append({
            'surnames': len(surnames),
            'duration': duration
        })
    
    def test_update_performance(self, update_count=100):
        """Test update performance."""
        print(f"\n=== Testing update performance ({update_count} updates) ===")
        
        handles = list(self.db.iter_person_handles())[:update_count]
        if len(handles) < update_count:
            print(f"Only {len(handles)} persons available for update")
            update_count = len(handles)
        
        start_time = time.time()
        
        for i, handle in enumerate(handles):
            person = self.db.get_person_from_handle(handle)
            # Update name
            person.get_primary_name().set_first_name(f"Updated{i}")
            
            with DbTxn(f"Update person {i}", self.db) as trans:
                self.db.commit_person(person, trans)
        
        duration = time.time() - start_time
        rate = update_count / duration
        
        print(f"Updated {update_count} persons in {duration:.2f}s ({rate:.1f} updates/sec)")
        
        self.results['update'].append({
            'count': update_count,
            'duration': duration,
            'rate': rate
        })
    
    def test_family_performance(self, family_count=100):
        """Test family creation and relationship performance."""
        print(f"\n=== Testing family performance ({family_count} families) ===")
        
        # Get person handles
        handles = list(self.db.iter_person_handles())
        if len(handles) < family_count * 2:
            print(f"Not enough persons for {family_count} families")
            return
        
        start_time = time.time()
        
        for i in range(family_count):
            family = Family()
            family.set_gramps_id(f"F{i:04d}")
            
            # Set parents
            father_handle = handles[i*2]
            mother_handle = handles[i*2 + 1]
            family.set_father_handle(father_handle)
            family.set_mother_handle(mother_handle)
            
            with DbTxn(f"Create family {i}", self.db) as trans:
                self.db.add_family(family, trans)
                
                # Update parent references
                father = self.db.get_person_from_handle(father_handle)
                father.add_family_handle(family.handle)
                self.db.commit_person(father, trans)
                
                mother = self.db.get_person_from_handle(mother_handle)
                mother.add_family_handle(family.handle)
                self.db.commit_person(mother, trans)
        
        duration = time.time() - start_time
        rate = family_count / duration
        
        print(f"Created {family_count} families in {duration:.2f}s ({rate:.1f} families/sec)")
        
        self.results['family_create'].append({
            'count': family_count,
            'duration': duration,
            'rate': rate
        })
    
    def test_complex_queries(self):
        """Test complex query performance."""
        print(f"\n=== Testing complex query performance ===")
        
        # Test 1: Count persons by gender
        start_time = time.time()
        
        male_count = 0
        female_count = 0
        for handle in self.db.iter_person_handles():
            person = self.db.get_person_from_handle(handle)
            if person.get_gender() == Person.MALE:
                male_count += 1
            elif person.get_gender() == Person.FEMALE:
                female_count += 1
        
        duration = time.time() - start_time
        
        print(f"Gender count: {male_count} males, {female_count} females in {duration:.2f}s")
        
        self.results['gender_count'].append({
            'duration': duration,
            'male_count': male_count,
            'female_count': female_count
        })
        
        # Test 2: Find all persons with same surname
        start_time = time.time()
        
        surname_groups = defaultdict(list)
        for handle in self.db.iter_person_handles():
            person = self.db.get_person_from_handle(handle)
            surname = person.get_primary_name().get_surname()
            if surname:
                surname_groups[surname].append(handle)
        
        duration = time.time() - start_time
        
        # Find largest surname group
        largest_surname = max(surname_groups.keys(), 
                            key=lambda s: len(surname_groups[s]))
        
        print(f"Surname grouping: {len(surname_groups)} surnames in {duration:.2f}s")
        print(f"Largest group: {largest_surname} with {len(surname_groups[largest_surname])} persons")
        
        self.results['surname_grouping'].append({
            'duration': duration,
            'unique_surnames': len(surname_groups),
            'largest_group': len(surname_groups[largest_surname])
        })
    
    def test_concurrent_access(self, concurrent_readers=5):
        """Test concurrent read access."""
        print(f"\n=== Testing concurrent access ({concurrent_readers} readers) ===")
        
        import threading
        import queue
        
        handles = list(self.db.iter_person_handles())
        if not handles:
            print("No persons for concurrent test")
            return
        
        results_queue = queue.Queue()
        
        def reader_thread(thread_id, count=100):
            """Reader thread function."""
            thread_start = time.time()
            
            # Create separate connection
            import psycopg
            conn = psycopg.connect(
                f"postgresql://genealogy_user:GenealogyData2025@192.168.10.90:5432/{self.db_name}"
            )
            
            for _ in range(count):
                handle = random.choice(handles)
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT json_data FROM person WHERE handle = %s",
                        [handle]
                    )
                    result = cur.fetchone()
            
            conn.close()
            
            thread_duration = time.time() - thread_start
            results_queue.put({
                'thread_id': thread_id,
                'duration': thread_duration,
                'reads': count
            })
        
        # Start threads
        threads = []
        start_time = time.time()
        
        for i in range(concurrent_readers):
            t = threading.Thread(target=reader_thread, args=(i,))
            t.start()
            threads.append(t)
        
        # Wait for completion
        for t in threads:
            t.join()
        
        total_duration = time.time() - start_time
        
        # Collect results
        thread_results = []
        while not results_queue.empty():
            thread_results.append(results_queue.get())
        
        total_reads = sum(r['reads'] for r in thread_results)
        avg_duration = statistics.mean(r['duration'] for r in thread_results)
        
        print(f"Concurrent reads: {total_reads} total in {total_duration:.2f}s")
        print(f"Average thread duration: {avg_duration:.2f}s")
        print(f"Effective rate: {total_reads/total_duration:.1f} reads/sec")
        
        self.results['concurrent_reads'].append({
            'readers': concurrent_readers,
            'total_duration': total_duration,
            'total_reads': total_reads,
            'rate': total_reads/total_duration
        })
    
    def generate_report(self):
        """Generate performance report."""
        print("\n" + "="*60)
        print("PERFORMANCE TEST REPORT")
        print("="*60)
        print(f"Database: {self.db_name}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Summary statistics
        if 'bulk_insert' in self.results:
            bulk_rates = [r['rate'] for r in self.results['bulk_insert']]
            print(f"Bulk Insert Rate: {statistics.mean(bulk_rates):.1f} persons/sec")
        
        if 'individual_insert' in self.results:
            ind_rates = [r['rate'] for r in self.results['individual_insert']]
            print(f"Individual Insert Rate: {statistics.mean(ind_rates):.1f} persons/sec")
        
        if 'handle_lookup' in self.results:
            lookup_rates = [r['rate'] for r in self.results['handle_lookup']]
            print(f"Handle Lookup Rate: {statistics.mean(lookup_rates):.1f} lookups/sec")
        
        if 'update' in self.results:
            update_rates = [r['rate'] for r in self.results['update']]
            print(f"Update Rate: {statistics.mean(update_rates):.1f} updates/sec")
        
        if 'family_create' in self.results:
            family_rates = [r['rate'] for r in self.results['family_create']]
            print(f"Family Creation Rate: {statistics.mean(family_rates):.1f} families/sec")
        
        # Save detailed results
        report_path = f"performance_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(dict(self.results), f, indent=2)
        
        print(f"\nDetailed results saved to: {report_path}")
    
    def run_all_tests(self):
        """Run all performance tests."""
        try:
            self.setup()
            
            # Warm up
            print("Warming up database...")
            self.test_bulk_insert(100)
            
            # Main tests
            self.test_bulk_insert(1000)
            self.test_bulk_insert(5000)
            self.test_individual_inserts(100)
            self.test_search_performance(1000)
            self.test_update_performance(500)
            self.test_family_performance(200)
            self.test_complex_queries()
            self.test_concurrent_access(5)
            
            # Generate report
            self.generate_report()
            
        finally:
            self.teardown()


def main():
    """Run performance tests."""
    print("PostgreSQL Enhanced Performance Testing")
    print("=====================================")
    
    tester = PerformanceTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()