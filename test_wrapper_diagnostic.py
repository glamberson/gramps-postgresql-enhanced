#!/usr/bin/env python3
"""
Diagnostic to test if TablePrefixWrapper is working correctly
"""

import re

class TablePrefixWrapper:
    """Test version of our wrapper"""
    
    PREFIXED_TABLES = {
        "person", "family", "event", "place", "repository",
        "source", "citation", "media", "note", "tag",
        "metadata", "reference", "gender_stats", "name_group", "surname"
    }
    
    def __init__(self, prefix):
        self._prefix = prefix
    
    def _add_table_prefixes(self, query):
        """Add table prefixes to a query."""
        modified = query
        
        for table in self.PREFIXED_TABLES:
            patterns = [
                # The pattern that should catch DBAPI queries
                (rf"\b(FROM)\s+({table})\b", rf"\1 {self._prefix}\2"),
                (rf"\b(JOIN)\s+({table})\b", rf"\1 {self._prefix}\2"),
                (rf"\b(INTO)\s+({table})\b", rf"\1 {self._prefix}\2"),
                (rf"\b(UPDATE)\s+({table})\b", rf"\1 {self._prefix}\2"),
                (rf"\b(DELETE\s+FROM)\s+({table})\b", rf"\1 {self._prefix}\2"),
                (rf"\b(INSERT\s+INTO)\s+({table})\b", rf"\1 {self._prefix}\2"),
            ]
            
            for pattern, replacement in patterns:
                modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
        
        return modified

# Test with actual DBAPI queries
wrapper = TablePrefixWrapper("tree_6892fe9f_")

test_queries = [
    # Query from DBAPI._get_raw_data (line 1040)
    "SELECT json_data FROM person WHERE handle = ?",
    # Query from DBAPI._get_raw_from_id_data
    "SELECT json_data FROM person WHERE gramps_id = ?",
    # Query from DBAPI._iter_handles
    "SELECT handle FROM person",
    # Query from DBAPI._has_handle
    "SELECT 1 FROM person WHERE handle = ?",
    # Query from DBAPI commit
    "UPDATE person SET json_data = ? WHERE handle = ?",
    "INSERT INTO person (handle, json_data) VALUES (?, ?)",
    # Count query
    "SELECT count(1) FROM person",
]

print("Testing TablePrefixWrapper with DBAPI query patterns:\n")
for query in test_queries:
    modified = wrapper._add_table_prefixes(query)
    if query != modified:
        print(f"✓ WORKS: {query}")
        print(f"  → {modified}")
    else:
        print(f"✗ FAILS: {query}")
        print(f"  → (unchanged)")
    print()