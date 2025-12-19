#!/usr/bin/env python3
"""
Migrate existing PostgreSQL Enhanced trees to new dual backend system.

Updates database.txt from 'postgresqlenhanced' to either:
- 'postgresqlenhanced-monolithic'
- 'postgresqlenhanced-separate'

Based on how the tree was actually configured.
"""

import os
import sys

def get_gramps_db_dir():
    """Get Gramps database directory."""
    return os.path.expanduser("~/.local/share/gramps/grampsdb")

def get_tree_mode(tree_dir):
    """
    Determine if tree was using monolithic or separate mode.

    Check if settings.ini exists and has mode setting,
    otherwise assume monolithic (the default).
    """
    settings_file = os.path.join(tree_dir, "settings.ini")

    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            for line in f:
                if 'mode' in line and '=' in line:
                    if 'separate' in line.lower():
                        return 'separate'

    # Default to monolithic (was the common configuration)
    return 'monolithic'

def migrate_tree(tree_dir, tree_id):
    """Migrate a single tree."""
    database_txt = os.path.join(tree_dir, "database.txt")
    name_txt = os.path.join(tree_dir, "name.txt")

    if not os.path.exists(database_txt):
        return None

    # Read current backend
    with open(database_txt, 'r') as f:
        backend = f.read().strip()

    if backend != "postgresqlenhanced":
        return None  # Already migrated or different backend

    # Get tree name
    tree_name = "Unknown"
    if os.path.exists(name_txt):
        with open(name_txt, 'r') as f:
            tree_name = f.read().strip()

    # Determine mode
    mode = get_tree_mode(tree_dir)
    new_backend = f"postgresqlenhanced-{mode}"

    # Backup original
    backup_file = database_txt + ".backup"
    with open(backup_file, 'w') as f:
        f.write(backend)

    # Write new backend
    with open(database_txt, 'w') as f:
        f.write(new_backend)

    return {
        'tree_id': tree_id,
        'name': tree_name,
        'old': backend,
        'new': new_backend,
        'mode': mode
    }

def main():
    """Main migration function."""
    db_dir = get_gramps_db_dir()

    if not os.path.exists(db_dir):
        print(f"Gramps database directory not found: {db_dir}")
        return 1

    print("PostgreSQL Enhanced Backend Migration")
    print("=" * 60)
    print(f"Database directory: {db_dir}")
    print()

    migrated = []

    for tree_id in os.listdir(db_dir):
        tree_dir = os.path.join(db_dir, tree_id)
        if not os.path.isdir(tree_dir):
            continue

        result = migrate_tree(tree_dir, tree_id)
        if result:
            migrated.append(result)

    if not migrated:
        print("No trees found needing migration.")
        print("All trees are either already migrated or use different backends.")
        return 0

    print(f"Migrated {len(migrated)} tree(s):")
    print()

    for m in migrated:
        print(f"  Tree: {m['name']}")
        print(f"    ID: {m['tree_id']}")
        print(f"    Mode: {m['mode']}")
        print(f"    Backend: {m['old']} → {m['new']}")
        print(f"    Backup: database.txt.backup")
        print()

    print("Migration complete!")
    print()
    print("Next steps:")
    print("  1. Restart Gramps")
    print("  2. Your trees will now use the correct backend ID")
    print("  3. If any issues, restore from database.txt.backup")

    return 0

if __name__ == "__main__":
    sys.exit(main())
