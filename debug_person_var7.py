#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from test_valid_stress import create_valid_person_variations, compare_ignoring_change_time
from postgresqlenhanced import PostgreSQLEnhanced
from gramps.gen.db import DbTxn
import tempfile
import os
from datetime import datetime

# Get Person-Var7
variations = create_valid_person_variations()
for label, person in variations:
    if label == 'Person-Var7':
        print(f'Testing {label}')
        
        # Get original serialization
        orig_data = person.serialize()
        print(f'Original serialization field 5 (primary name): {orig_data[5]}')
        
        # Simulate what our fix does
        primary_name = person.get_primary_name()
        first_name = primary_name.get_first_name()
        print(f'Original first name: {repr(first_name)}')
        
        # Temporarily modify
        primary_name.set_first_name('')
        temp_data = person.serialize()
        print(f'After setting to empty: field 5 = {temp_data[5]}')
        
        # Restore
        primary_name.set_first_name(None)
        restored_data = person.serialize()
        print(f'After restoring to None: field 5 = {restored_data[5]}')
        
        # Check if they're the same
        if orig_data == restored_data:
            print('✅ Data preserved after temporary modification')
        else:
            print('❌ Data changed after temporary modification')
            for i, (o, r) in enumerate(zip(orig_data, restored_data)):
                if o != r:
                    print(f'  Field {i}: {o} -> {r}')