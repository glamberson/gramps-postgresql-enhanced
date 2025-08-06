#!/usr/bin/env python3
"""Fix f-strings in Python files for Gramps compatibility."""

import re
import sys

def fix_fstrings(filename):
    """Fix f-strings in a file."""
    with open(filename, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern to match f-strings with single variables
    # f"text {var}" -> "text %s" % var
    content = re.sub(
        r'f"([^"]*?)\{([^}:]+)\}([^"]*?)"',
        r'"\1%s\3" % \2',
        content
    )
    
    # Handle f-strings with multiple variables
    # This is more complex - would need manual review
    
    # Pattern for f-strings with dotted access
    # f"text {obj.attr}" -> "text %s" % obj.attr
    content = re.sub(
        r'f"([^"]*?)\{([^}:]+\.[^}:]+)\}([^"]*?)"',
        r'"\1%s\3" % \2',
        content
    )
    
    # Single quotes version
    content = re.sub(
        r"f'([^']*?)\{([^}:]+)\}([^']*?)'",
        r"'\1%s\3' % \2",
        content
    )
    
    if content != original:
        with open(filename, 'w') as f:
            f.write(content)
        print(f"Fixed {filename}")
        return True
    return False

files = ['connection.py', 'schema.py', 'migration.py', 'queries.py']
for f in files:
    if fix_fstrings(f):
        print(f"  ✓ {f}")
    else:
        print(f"  - {f} unchanged")