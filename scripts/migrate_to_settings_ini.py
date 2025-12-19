#!/usr/bin/env python3
"""
Migrate from connection_info.txt to per-tree settings.ini files.

Creates settings.ini in each PostgreSQL Enhanced tree directory
based on the central connection_info.txt configuration.
"""

import os
import sys

def get_gramps_db_dir():
    """Get Gramps database directory."""
    return os.path.expanduser("~/.local/share/gramps/grampsdb")

def get_plugin_dir():
    """Get PostgreSQL Enhanced plugin directory."""
    return os.path.expanduser("~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced")

def read_connection_info():
    """Read connection_info.txt from plugin directory."""
    config_file = os.path.join(get_plugin_dir(), 'connection_info.txt')

    if not os.path.exists(config_file):
        return None

    config = {}
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()

    return config

def create_settings_ini(tree_dir, connection_config, tree_name):
    """Create settings.ini in tree directory using ConfigManager."""
    sys.path.insert(0, os.path.expanduser('~/.local/share/gramps'))
    from gramps.gen.utils.configmanager import ConfigManager

    settings_file = os.path.join(tree_dir, 'settings.ini')

    if os.path.exists(settings_file):
        return False  # Already exists

    # Create ConfigManager for this tree
    config_mgr = ConfigManager(settings_file)

    # Register with proper types (port is int!)
    config_mgr.register('database.host', 'localhost')
    config_mgr.register('database.port', 5432)
    config_mgr.register('database.user', 'gramps_user')
    config_mgr.register('database.shared-database', 'gramps_shared')
    config_mgr.register('database.pool-size', 5)

    # Set values from connection_info.txt
    config_mgr.set('database.host', connection_config.get('host', 'localhost'))
    config_mgr.set('database.port', int(connection_config.get('port', '5432')))
    config_mgr.set('database.user', connection_config.get('user', 'gramps_user'))
    config_mgr.set('database.shared-database',
                   connection_config.get('shared_database_name', 'gramps_shared'))
    config_mgr.set('database.pool-size', int(connection_config.get('pool_size', '5')))

    # Save the configuration
    config_mgr.save()

    return True

def main():
    """Main migration function."""
    db_dir = get_gramps_db_dir()

    if not os.path.exists(db_dir):
        print(f"Gramps database directory not found: {db_dir}")
        return 1

    # Read connection_info.txt
    connection_config = read_connection_info()
    if not connection_config:
        print("No connection_info.txt found in plugin directory.")
        print(f"Expected: {get_plugin_dir()}/connection_info.txt")
        print()
        print("This is OK if you're using Gramps preferences instead.")
        return 0

    print("PostgreSQL Enhanced Config Migration")
    print("=" * 60)
    print("Source: connection_info.txt")
    print(f"Host: {connection_config.get('host', 'localhost')}")
    print(f"Port: {connection_config.get('port', '5432')}")
    print()

    migrated = []

    for tree_id in os.listdir(db_dir):
        tree_dir = os.path.join(db_dir, tree_id)
        if not os.path.isdir(tree_dir):
            continue

        # Check if this is a PostgreSQL Enhanced tree
        database_txt = os.path.join(tree_dir, 'database.txt')
        if not os.path.exists(database_txt):
            continue

        with open(database_txt, 'r') as f:
            backend = f.read().strip()

        if not backend.startswith('postgresqlenhanced'):
            continue  # Not our backend

        # Get tree name
        name_txt = os.path.join(tree_dir, 'name.txt')
        tree_name = "Unknown"
        if os.path.exists(name_txt):
            with open(name_txt, 'r') as f:
                tree_name = f.read().strip()

        # Create settings.ini
        if create_settings_ini(tree_dir, connection_config, tree_name):
            migrated.append({
                'tree_id': tree_id,
                'name': tree_name,
                'backend': backend
            })

    if not migrated:
        print("No trees needed migration (all already have settings.ini)")
        return 0

    print(f"Created settings.ini for {len(migrated)} tree(s):")
    print()

    for m in migrated:
        print(f"  Tree: {m['name']}")
        print(f"    ID: {m['tree_id']}")
        print(f"    Backend: {m['backend']}")
        print(f"    File: ~/.local/share/gramps/grampsdb/{m['tree_id']}/settings.ini")
        print()

    print("Migration complete!")
    print()
    print("Next steps:")
    print("  1. You can now set host/port in Edit → Preferences → Database")
    print("  2. New trees will inherit from global preferences")
    print("  3. Existing trees use migrated settings.ini")
    print("  4. Password will be prompted by Gramps (not stored in settings.ini)")
    print()
    print("Optional: You can now delete connection_info.txt from plugin directory")
    print(f"  rm {get_plugin_dir()}/connection_info.txt")

    return 0

if __name__ == "__main__":
    sys.exit(main())
