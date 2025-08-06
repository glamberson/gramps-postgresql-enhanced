#!/usr/bin/env python3
"""
Fix for the table prefix double-application bug.

The problem:
1. Schema._table_name() creates: "prefix_tablename" (with quotes)
2. TablePrefixWrapper tries to add prefix again to unquoted table names
3. This causes queries to fail because the wrapper doesn't recognize already-prefixed tables

The solution:
1. Make TablePrefixWrapper skip already-quoted table names
2. OR make it handle quoted table names properly
3. Ensure no double-prefixing occurs
"""

import re

def analyze_query_patterns():
    """Analyze the query patterns that need fixing."""
    
    # Example queries that are failing
    failing_queries = [
        'INSERT INTO "smith_family_metadata" (setting, value, json_data)',
        'SELECT value FROM "jones_research_metadata" WHERE setting = %s',
        'CREATE TABLE IF NOT EXISTS "prefix_person" (...)',
    ]
    
    # Patterns that TablePrefixWrapper is using
    current_patterns = [
        r"\b(INSERT\s+INTO)\s+(metadata)\b",  # Won't match "prefix_metadata"
        r"\b(FROM)\s+(metadata)\b",
        r"\b(CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS)\s+(metadata)\b",
    ]
    
    print("PROBLEM ANALYSIS:")
    print("=" * 60)
    print("\nFailing queries (already prefixed and quoted):")
    for q in failing_queries:
        print(f"  - {q}")
    
    print("\nCurrent regex patterns (looking for unquoted tables):")
    for p in current_patterns:
        print(f"  - {p}")
    
    print("\nThe patterns won't match because:")
    print("  1. Table names are already quoted")
    print("  2. Table names are already prefixed")
    print("  3. Regex is looking for word boundaries around bare table names")
    
    return failing_queries, current_patterns

def create_fixed_table_prefix_wrapper():
    """Create the fixed version of TablePrefixWrapper."""
    
    fixed_code = '''class TablePrefixWrapper:
    """
    Wrapper that adds table prefixes for monolithic mode.
    
    FIXED VERSION: Handles already-quoted and already-prefixed table names.
    """

    # Tables that need prefixes in monolithic mode
    PREFIXED_TABLES = {
        "person",
        "family", 
        "event",
        "place",
        "repository",
        "source",
        "citation",
        "media",
        "note",
        "tag",
        "metadata",
        "reference",
        "gender_stats",
    }

    # Tables that are shared (no prefix)
    SHARED_TABLES = {"name_group", "surname"}

    def __init__(self, connection, table_prefix):
        """Initialize wrapper with connection and prefix."""
        self._connection = connection
        self._prefix = table_prefix

    def execute(self, query, params=None):
        """Execute query with table prefixes added."""
        # Check if query already contains prefixed table names
        if self._query_already_prefixed(query):
            # Query is already prefixed, pass through unchanged
            return self._connection.execute(query, params)
        
        # Add prefixes to table names in the query
        modified_query = self._add_table_prefixes(query)

        # Log for debugging
        import logging
        LOG = logging.getLogger(".PostgreSQLEnhanced.TablePrefixWrapper")
        if query != modified_query:
            LOG.debug("Query modified: %s -> %s", query, modified_query)

        return self._connection.execute(modified_query, params)

    def cursor(self):
        """Return a wrapped cursor that prefixes queries."""
        return CursorPrefixWrapper(self._connection.cursor(), self._prefix)

    def fetchone(self):
        """Fetch one row from the last executed query."""
        return self._connection.fetchone()

    def fetchall(self):
        """Fetch all rows from the last executed query."""
        return self._connection.fetchall()

    def _query_already_prefixed(self, query):
        """
        Check if query already contains prefixed table names.
        
        This handles queries coming from Schema class which already
        have prefixed and quoted table names like "prefix_tablename".
        """
        # If query contains quoted table names with our prefix, it's already processed
        if self._prefix and f'"{self._prefix}' in query:
            return True
        
        # Check for quoted table names that might be prefixed
        import re
        for table in self.PREFIXED_TABLES:
            # Check if table appears quoted with prefix
            pattern = rf'"{re.escape(self._prefix)}{re.escape(table)}"'
            if re.search(pattern, query):
                return True
        
        return False

    def _add_table_prefixes(self, query):
        """Add table prefixes to a query that doesn't already have them."""
        import re

        modified = query

        for table in self.PREFIXED_TABLES:
            # Only match unquoted table names (not already prefixed)
            patterns = [
                # Basic patterns - only match unquoted tables
                (rf'\\b(FROM)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(JOIN)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(INTO)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(UPDATE)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(DELETE\\s+FROM)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(INSERT\\s+INTO)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(ALTER\\s+TABLE)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(DROP\\s+TABLE\\s+IF\\s+EXISTS)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(CREATE\\s+TABLE\\s+IF\\s+NOT\\s+EXISTS)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                (rf'\\b(CREATE\\s+TABLE)\\s+(?!")({table})\\b(?!")', rf'\\1 {self._prefix}\\2'),
                # Table.column references (unquoted)
                (rf'\\b(?!")({table})\\.', rf'{self._prefix}\\1.'),
            ]

            for pattern, replacement in patterns:
                modified = re.sub(
                    pattern, replacement, modified, flags=re.IGNORECASE | re.DOTALL
                )

        return modified
'''
    
    return fixed_code

def main():
    """Main function to generate the fix."""
    print("TABLE PREFIX FIX ANALYSIS")
    print("=" * 60)
    
    # Analyze the problem
    analyze_query_patterns()
    
    print("\n\nPROPOSED FIX:")
    print("=" * 60)
    print("\nThe fix adds a _query_already_prefixed() check that:")
    print("  1. Detects if query contains quoted table names with prefix")
    print("  2. Skips prefix addition for already-prefixed queries")
    print("  3. Only adds prefixes to unquoted table names")
    
    print("\n\nFIXED CODE:")
    print("=" * 60)
    fixed_code = create_fixed_table_prefix_wrapper()
    print(fixed_code)
    
    print("\n\nIMPLEMENTATION STEPS:")
    print("=" * 60)
    print("1. Backup current postgresqlenhanced.py")
    print("2. Replace TablePrefixWrapper class with fixed version")
    print("3. Test both separate and monolithic modes")
    print("4. Verify no double-prefixing occurs")

if __name__ == "__main__":
    main()