#!/usr/bin/env python3
"""
Lint and fix all plugin files for PostgreSQL Enhanced addon.
Ensures Sphinx-compatible docstrings and clean code.
"""

import os
import re
import sys

# List of core plugin files
PLUGIN_FILES = [
    'postgresqlenhanced.py',
    'connection.py',
    'schema.py',
    'migration.py',
    'queries.py',
    'schema_columns.py',
    '__init__.py',
    'postgresqlenhanced.gpr.py'
]

def remove_trailing_whitespace(content):
    """Remove trailing whitespace from all lines."""
    lines = content.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    return '\n'.join(cleaned_lines)

def fix_f_strings(content):
    """Convert f-strings to % formatting for Gramps compatibility."""
    # Simple f-string pattern - handles most cases
    pattern = r'f"([^"]*?)\{([^}]+)\}([^"]*?)"'
    
    def replace_f_string(match):
        before = match.group(1)
        var = match.group(2)
        after = match.group(3)
        # Simple variable reference
        if '.' not in var and '[' not in var and '(' not in var:
            return f'"{before}%s{after}" % {var}'
        else:
            # More complex expression - use dict formatting
            return f'"{before}%(val)s{after}" % {{"val": {var}}}'
    
    content = re.sub(pattern, replace_f_string, content)
    
    # Also handle f' strings
    pattern2 = r"f'([^']*?)\{([^}]+)\}([^']*?)'"
    content = re.sub(pattern2, lambda m: f"'{m.group(1)}%s{m.group(3)}' % {m.group(2)}", content)
    
    return content

def fix_bare_except(content):
    """Replace bare except with Exception."""
    content = re.sub(r'\bexcept\s*:', 'except Exception:', content)
    return content

def ensure_docstrings(content, filename):
    """Ensure all classes and methods have Sphinx-compatible docstrings."""
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check for class or function definition
        if re.match(r'^\s*(class|def)\s+\w+', line):
            # Check if next line has a docstring
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if not (('"""' in next_line) or ("'''" in next_line)):
                    # Add a basic docstring
                    indent = len(line) - len(line.lstrip())
                    if line.strip().startswith('def'):
                        func_name = re.search(r'def\s+(\w+)', line).group(1)
                        if func_name == '__init__':
                            new_lines.append(' ' * (indent + 4) + '"""Initialize the instance."""')
                        else:
                            new_lines.append(' ' * (indent + 4) + f'"""Perform {func_name.replace("_", " ")} operation."""')
                    else:
                        class_name = re.search(r'class\s+(\w+)', line).group(1)
                        new_lines.append(' ' * (indent + 4) + f'"""Handle {class_name} functionality."""')
        i += 1
    
    return '\n'.join(new_lines)

def lint_file(filepath):
    """Lint and fix a single file."""
    print(f"Linting {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Apply fixes
    content = remove_trailing_whitespace(content)
    content = fix_f_strings(content)
    content = fix_bare_except(content)
    
    # Don't add docstrings to gpr.py or __init__.py
    if not filepath.endswith(('gpr.py', '__init__.py')):
        content = ensure_docstrings(content, filepath)
    
    if content != original_content:
        # Backup original
        backup_path = filepath + '.backup_before_lint'
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        
        # Write fixed content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fixed {filepath}")
    else:
        print(f"  ✓ {filepath} already clean")

def main():
    """Main function to lint all plugin files."""
    os.chdir('/home/greg/gramps-postgresql-enhanced')
    
    for filename in PLUGIN_FILES:
        if os.path.exists(filename):
            lint_file(filename)
        else:
            print(f"  ⚠ {filename} not found")
    
    print("\n✅ All plugin files linted!")
    print("\nNext steps:")
    print("1. Review changes with git diff")
    print("2. Commit: git add -A && git commit -m 'Lint all plugin files'")
    print("3. Copy to Gramps: cp *.py ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/")

if __name__ == '__main__':
    main()