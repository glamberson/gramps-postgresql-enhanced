#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025       Greg Lamberson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

"""
Verification script for PostgreSQL Enhanced addon.

Checks that the addon follows all Gramps standards.
"""

# -------------------------------------------------------------------------
#
# Standard python modules
#
# -------------------------------------------------------------------------
import os
import re
import sys
from pathlib import Path


def check_file_headers(directory):
    """Check all Python files have proper headers."""
    issues = []
    
    for filepath in Path(directory).rglob("*.py"):
        if "__pycache__" in str(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for proper copyright header
        if not content.startswith("#\n# Gramps"):
            issues.append(f"{filepath}: Missing proper Gramps header")
            
        # Check for copyright line format
        if not re.search(r"# Copyright \(C\) \d{4}\s+", content):
            issues.append(f"{filepath}: Improper copyright format")
            
        # Check for GPL license
        if "GNU General Public License" not in content:
            issues.append(f"{filepath}: Missing GPL license")
            
        # Check section headers
        if "# ------" in content and not "# -----" in content:
            issues.append(f"{filepath}: Section headers should use '# -----'")
            
    return issues


def check_imports(directory):
    """Check import organization."""
    issues = []
    
    for filepath in Path(directory).rglob("*.py"):
        if "__pycache__" in str(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for import sections
        if "import " in content and "# Standard python modules" not in content:
            issues.append(f"{filepath}: Missing standard python modules section")
            
    return issues


def check_gpr_file(directory):
    """Check .gpr.py registration file."""
    issues = []
    gpr_files = list(Path(directory).glob("*.gpr.py"))
    
    if not gpr_files:
        issues.append("Missing .gpr.py registration file")
    elif len(gpr_files) > 1:
        issues.append("Multiple .gpr.py files found")
    else:
        with open(gpr_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check required fields
        required = ['register(', 'id=', 'name=', 'version=', 
                   'gramps_target_version=', 'status=', 'fname=',
                   'databaseclass=']
        
        for field in required:
            if field not in content:
                issues.append(f"Missing required field: {field}")
                
    return issues


def check_translations(directory):
    """Check translation files."""
    issues = []
    po_dir = Path(directory) / "po"
    
    if not po_dir.exists():
        issues.append("Missing po/ directory")
    else:
        pot_files = list(po_dir.glob("*.pot"))
        if not pot_files:
            issues.append("Missing template.pot file")
            
    return issues


def check_manifest(directory):
    """Check MANIFEST file."""
    issues = []
    manifest_file = Path(directory) / "MANIFEST"
    
    if not manifest_file.exists():
        issues.append("Missing MANIFEST file")
        
    return issues


def main():
    """Run all checks."""
    directory = Path(__file__).parent
    
    print("Verifying PostgreSQL Enhanced addon...")
    print("=" * 50)
    
    all_issues = []
    
    # Run checks
    checks = [
        ("File headers", check_file_headers),
        ("Import organization", check_imports),
        ("GPR registration", check_gpr_file),
        ("Translations", check_translations),
        ("MANIFEST", check_manifest),
    ]
    
    for check_name, check_func in checks:
        print(f"\nChecking {check_name}...")
        issues = check_func(directory)
        
        if issues:
            print(f"  ❌ Found {len(issues)} issue(s):")
            for issue in issues:
                print(f"    - {issue}")
            all_issues.extend(issues)
        else:
            print("  ✅ OK")
            
    print("\n" + "=" * 50)
    
    if all_issues:
        print(f"\n❌ Total issues found: {len(all_issues)}")
        return 1
    else:
        print("\n✅ All checks passed!")
        return 0


if __name__ == '__main__':
    sys.exit(main())