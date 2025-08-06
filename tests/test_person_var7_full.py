#!/usr/bin/env python3

import sys
import os
from datetime import datetime
import tempfile

from test_valid_stress import create_valid_person_variations, compare_ignoring_change_time
from postgresqlenhanced import PostgreSQLEnhanced
from gramps.gen.db import DbTxn

# Get Person-Var7
variations = create_valid_person_variations()
for label, person in variations:
    if label == 'Person-Var7':
        print(f'Testing {label}')
        
        # Get original data
        orig_data = person.serialize()
        primary_name = person.get_primary_name()
        orig_first_name = primary_name.get_first_name()
        print(f'Original first name: {repr(orig_first_name)}')
        print(f'Original serialization[5]: {orig_data[5]}')
        
        # Database configuration
        config = {
            'host': '192.168.10.90',
            'port': 5432,
            'user': 'genealogy_user',
            'password': 'GenealogyData2025',
            'database': f'test_var7_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'database_mode': 'separate'
        }
        
        # Initialize database
        db = PostgreSQLEnhanced()
        
        # Write connection info
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for key, value in config.items():
                f.write(f'{key}={value}\n')
            conn_file = f.name
        
        test_dir = f'/tmp/test_var7_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(test_dir, exist_ok=True)
        
        conn_file_path = os.path.join(test_dir, 'connection_info.txt')
        os.rename(conn_file, conn_file_path)
        
        try:
            db.load(test_dir, update=False, callback=None)
            
            # Store in database
            handle = person.get_handle()
            with DbTxn(f"Add {label}", db) as trans:
                db.add_person(person, trans)
            
            # Check if the person object was modified
            post_add_data = person.serialize()
            post_add_first_name = person.get_primary_name().get_first_name()
            print(f'After add first name: {repr(post_add_first_name)}')
            print(f'After add serialization[5]: {post_add_data[5]}')
            
            # Retrieve from database
            retrieved = db.get_person_from_handle(handle)
            if retrieved:
                retr_data = retrieved.serialize()
                retr_first_name = retrieved.get_primary_name().get_first_name()
                print(f'Retrieved first name: {repr(retr_first_name)}')
                print(f'Retrieved serialization[5]: {retr_data[5]}')
                
                # Compare
                if compare_ignoring_change_time(person, retrieved, label):
                    print(f'✅ {label}: Data preserved correctly')
                else:
                    print(f'❌ {label}: Data changed unexpectedly')
                    # Show differences
                    for i, (o, r) in enumerate(zip(orig_data, retr_data)):
                        if i == 17:  # Skip change_time
                            continue
                        if o != r:
                            print(f'  Field {i}: {repr(o)} -> {repr(r)}')
            else:
                print(f'❌ Failed to retrieve {label}')
                
        finally:
            db.close()