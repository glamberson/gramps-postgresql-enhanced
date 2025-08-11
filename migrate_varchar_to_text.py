#!/usr/bin/env python3
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
Migration script to convert VARCHAR(255) columns to TEXT
for existing PostgreSQL Enhanced databases.

This addresses the issue where long strings (names, metadata, etc.)
could be truncated when migrating from SQLite.

Usage:
    python3 migrate_varchar_to_text.py --database=<dbname> [options]
"""

import argparse
import sys
import logging
import psycopg
from psycopg import sql

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class VarcharToTextMigrator:
    """Migrates VARCHAR(255) columns to TEXT in PostgreSQL Enhanced databases."""
    
    def __init__(self, conn_params):
        """Initialize with connection parameters."""
        self.conn_params = conn_params
        self.conn = None
        self.migrations_needed = []
        
    def connect(self):
        """Connect to the database."""
        try:
            self.conn = psycopg.connect(**self.conn_params)
            logger.info(f"Connected to database: {self.conn_params.get('dbname', 'default')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
            
    def check_migrations_needed(self):
        """Check which columns need migration."""
        migrations = []
        
        with self.conn.cursor() as cur:
            # Query to find all VARCHAR(255) columns
            cur.execute("""
                SELECT 
                    table_name,
                    column_name,
                    data_type,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND data_type = 'character varying'
                    AND character_maximum_length = 255
                ORDER BY table_name, column_name
            """)
            
            for row in cur.fetchall():
                table, column, dtype, max_len = row
                migrations.append({
                    'table': table,
                    'column': column,
                    'current_type': f'VARCHAR({max_len})',
                    'new_type': 'TEXT'
                })
                
        self.migrations_needed = migrations
        return migrations
        
    def backup_warning(self):
        """Display backup warning."""
        print("\n" + "="*70)
        print("WARNING: Database Migration")
        print("="*70)
        print("\nThis script will modify your database schema.")
        print("It is STRONGLY recommended to backup your database first.")
        print("\nTo backup your PostgreSQL database, run:")
        print(f"  pg_dump {self.conn_params.get('dbname', 'your_database')} > backup.sql")
        print("\n" + "="*70)
        
        response = input("\nHave you backed up your database? (yes/no): ")
        return response.lower() in ['yes', 'y']
        
    def display_migrations(self):
        """Display planned migrations."""
        if not self.migrations_needed:
            print("\nNo migrations needed - database schema is already up to date!")
            return False
            
        print("\nThe following columns will be migrated from VARCHAR(255) to TEXT:")
        print("-" * 60)
        
        for m in self.migrations_needed:
            print(f"  Table: {m['table']:20} Column: {m['column']:20}")
            
        print("-" * 60)
        print(f"Total columns to migrate: {len(self.migrations_needed)}")
        return True
        
    def perform_migration(self, dry_run=False):
        """Perform the actual migration."""
        if dry_run:
            print("\nDRY RUN MODE - No changes will be made")
            
        success_count = 0
        error_count = 0
        
        with self.conn.cursor() as cur:
            for migration in self.migrations_needed:
                table = migration['table']
                column = migration['column']
                
                # Build ALTER TABLE statement
                alter_sql = sql.SQL(
                    "ALTER TABLE {} ALTER COLUMN {} TYPE TEXT"
                ).format(
                    sql.Identifier(table),
                    sql.Identifier(column)
                )
                
                try:
                    if dry_run:
                        logger.info(f"Would execute: {alter_sql.as_string(cur)}")
                    else:
                        logger.info(f"Migrating {table}.{column} to TEXT...")
                        cur.execute(alter_sql)
                        
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate {table}.{column}: {e}")
                    error_count += 1
                    if not dry_run:
                        # Rollback this change
                        self.conn.rollback()
                        raise
                        
        if not dry_run:
            # Commit all changes
            self.conn.commit()
            logger.info("All migrations committed successfully")
            
        return success_count, error_count
        
    def verify_migration(self):
        """Verify that migration was successful."""
        with self.conn.cursor() as cur:
            # Check for any remaining VARCHAR(255) columns
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND data_type = 'character varying'
                    AND character_maximum_length = 255
            """)
            
            remaining = cur.fetchone()[0]
            
            if remaining == 0:
                logger.info("✓ Migration verified - all VARCHAR(255) columns converted to TEXT")
                return True
            else:
                logger.warning(f"⚠ {remaining} VARCHAR(255) columns still remain")
                return False
                
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate VARCHAR(255) columns to TEXT in PostgreSQL Enhanced databases'
    )
    
    # Connection parameters
    parser.add_argument('--host', default='localhost',
                       help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432,
                       help='Database port (default: 5432)')
    parser.add_argument('--database', '--dbname', required=True,
                       help='Database name')
    parser.add_argument('--user', default='postgres',
                       help='Database user (default: postgres)')
    parser.add_argument('--password', 
                       help='Database password (will prompt if not provided)')
    
    # Operation modes
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Skip backup confirmation prompt')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check what needs migration, don\'t migrate')
    
    args = parser.parse_args()
    
    # Build connection parameters
    conn_params = {
        'host': args.host,
        'port': args.port,
        'dbname': args.database,
        'user': args.user,
    }
    
    if args.password:
        conn_params['password'] = args.password
    else:
        # Prompt for password if not provided
        import getpass
        password = getpass.getpass(f"Password for {args.user}@{args.host}: ")
        if password:
            conn_params['password'] = password
            
    # Create migrator
    migrator = VarcharToTextMigrator(conn_params)
    
    # Connect to database
    if not migrator.connect():
        sys.exit(1)
        
    try:
        # Check what needs migration
        migrator.check_migrations_needed()
        
        if args.check_only:
            # Just display what would be migrated
            migrator.display_migrations()
            sys.exit(0)
            
        # Display migrations
        if not migrator.display_migrations():
            # Nothing to do
            sys.exit(0)
            
        # Backup warning (unless forced or dry-run)
        if not args.dry_run and not args.force:
            if not migrator.backup_warning():
                print("Migration cancelled.")
                sys.exit(0)
                
        # Get confirmation
        if not args.dry_run and not args.force:
            response = input("\nProceed with migration? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Migration cancelled.")
                sys.exit(0)
                
        # Perform migration
        print("\nStarting migration...")
        success, errors = migrator.perform_migration(dry_run=args.dry_run)
        
        print(f"\nMigration complete:")
        print(f"  ✓ Successfully migrated: {success} columns")
        if errors > 0:
            print(f"  ✗ Failed: {errors} columns")
            
        # Verify if not dry-run
        if not args.dry_run and success > 0:
            migrator.verify_migration()
            
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
        
    finally:
        migrator.close()
        

if __name__ == '__main__':
    main()