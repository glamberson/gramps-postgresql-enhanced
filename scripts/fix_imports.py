#!/usr/bin/env python3
"""Fix relative imports in the PostgreSQL Enhanced plugin."""

import os
import re

# Files to fix
files_to_fix = [
    "postgresqlenhanced.py",
    "schema.py",
    "connection.py",
    "migration.py",
    "queries.py",
    "debug_utils.py"
]

# Pattern to match relative imports
relative_import_pattern = re.compile(r'^from \.([\w_]+) import (.+)$', re.MULTILINE)

def fix_imports_in_file(filepath):
    """Fix relative imports in a single file."""
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} - file not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace relative imports with absolute imports
    def replace_import(match):
        module_name = match.group(1)
        import_items = match.group(2)
        return f'from {module_name} import {import_items}'
    
    new_content = relative_import_pattern.sub(replace_import, content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Fixed imports in {filepath}")
    else:
        print(f"No relative imports found in {filepath}")

def main():
    """Fix all imports."""
    print("Fixing relative imports in PostgreSQL Enhanced plugin...")
    
    for filename in files_to_fix:
        fix_imports_in_file(filename)
    
    print("\nDone! All relative imports have been converted to absolute imports.")

if __name__ == "__main__":
    main()