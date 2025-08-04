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
PostgreSQL Enhanced schema management for Gramps

Handles:
- Schema creation with dual storage (blob + JSONB)
- Schema versioning and upgrades
- Index optimization
- PostgreSQL-specific features
"""

# -------------------------------------------------------------------------
#
# Standard python modules
#
# -------------------------------------------------------------------------
import logging
import pickle
import sys
import os
from psycopg.types.json import Jsonb
from psycopg import sql

# Add plugin directory to path for imports
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from schema_columns import REQUIRED_COLUMNS, REQUIRED_INDEXES

# -------------------------------------------------------------------------
#
# Gramps modules
#
# -------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

# -------------------------------------------------------------------------
#
# Constants
#
# -------------------------------------------------------------------------
SCHEMA_VERSION = 1

# Gramps object types
OBJECT_TYPES = [
    'person', 'family', 'event', 'place', 'source',
    'citation', 'media', 'repository', 'note', 'tag'
]

# -------------------------------------------------------------------------
#
# PostgreSQLSchema class
#
# -------------------------------------------------------------------------
class PostgreSQLSchema:
    """
    Manages PostgreSQL schema for Gramps Enhanced.
    
    Features:
    - Dual storage (blob + JSONB)
    - Automatic schema creation
    - Version management
    - Index optimization
    - Future upgrade support
    """
    
    def __init__(self, connection, use_jsonb=True):
        """
        Initialize schema manager.
        
        :param connection: PostgreSQLConnection instance
        :param use_jsonb: Whether to create JSONB columns
        """
        self.conn = connection
        self.use_jsonb = use_jsonb
        self.log = logging.getLogger(".PostgreSQLEnhanced.Schema")
    
    def check_and_init_schema(self):
        """
        Check if schema exists and initialize if needed.
        
        This is called automatically when a database is opened,
        similar to SQLite's automatic table creation.
        """
        # Check if metadata table exists
        if not self.conn.table_exists('metadata'):
            # First time setup - create all tables
            self.log.info("Creating new PostgreSQL Enhanced schema")
            self._create_schema()
        else:
            # Check schema version and upgrade if needed
            current_version = self._get_schema_version()
            if current_version < SCHEMA_VERSION:
                self.log.info(f"Upgrading schema from v{current_version} to v{SCHEMA_VERSION}")
                self._upgrade_schema(current_version)
    
    def _create_schema(self):
        """
        Create the initial database schema.
        
        Creates tables that match SQLite schema but with
        PostgreSQL enhancements.
        """
        # Create metadata table
        if self.use_jsonb:
            # Enhanced metadata with JSON support
            # JSONSerializer expects json_data column for metadata
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    setting VARCHAR(255) PRIMARY KEY,
                    value BYTEA,  -- Keep for compatibility
                    json_data JSONB,  -- JSONSerializer uses this
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Basic metadata (blob only)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    setting VARCHAR(255) PRIMARY KEY,
                    value BYTEA
                )
            """)
        
        # Create object tables
        for obj_type in OBJECT_TYPES:
            self._create_object_table(obj_type)
        
        # Create reference table (for backlinks)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reference (
                obj_handle VARCHAR(50),
                obj_class VARCHAR(50),
                ref_handle VARCHAR(50),
                ref_class VARCHAR(50),
                PRIMARY KEY (obj_handle, obj_class, ref_handle, ref_class)
            )
        """)
        
        # Create indexes for references
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reference_ref 
                ON reference (ref_handle, ref_class)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reference_obj 
                ON reference (obj_handle, obj_class)
        """)
        
        # Create gender stats table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gender_stats (
                given_name VARCHAR(255) PRIMARY KEY,
                male INTEGER DEFAULT 0,
                female INTEGER DEFAULT 0,
                unknown INTEGER DEFAULT 0
            )
        """)
        
        # Create surname list table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS surname (
                surname VARCHAR(255) PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        
        # Create name group table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS name_group (
                key VARCHAR(255) PRIMARY KEY,
                value VARCHAR(255)
            )
        """)
        
        # Create PostgreSQL-specific features FIRST (includes extensions)
        if self.use_jsonb:
            self._create_enhanced_features()
        
        # Set initial schema version
        self._set_schema_version(SCHEMA_VERSION)
        
        self.conn.commit()
        self.log.info("PostgreSQL Enhanced schema created successfully")
    
    def _create_object_table(self, obj_type):
        """Create a table for a specific object type."""
        if self.use_jsonb:
            # Build column definitions for secondary columns
            # These are needed for Gramps queries but we won't update them
            extra_columns = []
            if obj_type in REQUIRED_COLUMNS:
                for col_name, json_path in REQUIRED_COLUMNS[obj_type].items():
                    # Determine column type based on the field
                    col_type = "VARCHAR(255)"
                    if "INTEGER" in json_path:
                        col_type = "INTEGER"
                    elif "BOOLEAN" in json_path:
                        col_type = "BOOLEAN"
                    elif col_name in ['title', 'desc', 'description', 'author', 'pubinfo', 
                                      'abbrev', 'page', 'name', 'path', 'given_name', 'surname']:
                        col_type = "TEXT"
                    elif col_name in ['father_handle', 'mother_handle', 'source_handle', 
                                      'place', 'enclosed_by']:
                        col_type = "VARCHAR(50)"
                        
                    extra_columns.append(f"{col_name} {col_type}")
            
            # Join column definitions
            extra_cols_sql = ""
            if extra_columns:
                extra_cols_sql = ",\n                    " + ",\n                    ".join(extra_columns)
            
            # Enhanced table with JSONB and secondary columns for compatibility
            # JSONSerializer uses json_data, not blob_data
            self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {obj_type} (
                    handle VARCHAR(50) PRIMARY KEY,
                    json_data JSONB,  -- JSONSerializer stores here
                    blob_data BYTEA,  -- Keep for potential compatibility
                    change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP{extra_cols_sql}
                )
            """)
            
            # Create JSONB expression indexes for fields DBAPI expects
            if obj_type in REQUIRED_COLUMNS:
                for col_name, json_path in REQUIRED_COLUMNS[obj_type].items():
                    # Create expression index on the JSONB path
                    idx_name = f"idx_{obj_type}_{col_name}"
                    self.conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name}
                        ON {obj_type} (({json_path}))
                    """)
            
            # Create GIN index for general JSONB queries
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{obj_type}_json 
                    ON {obj_type} USING GIN (json_data)
            """)
            
            # Create object-specific indexes
            self._create_object_specific_indexes(obj_type)
            
            # Create trigger to sync secondary columns from JSONB
            self._create_sync_trigger(obj_type)
            
        else:
            # Basic table (blob only)
            self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {obj_type} (
                    handle VARCHAR(50) PRIMARY KEY,
                    blob_data BYTEA
                )
            """)
    
    def _create_object_specific_indexes(self, obj_type):
        """Create indexes specific to each object type."""
        
        # First, create all required indexes from DBAPI
        if obj_type in REQUIRED_INDEXES:
            for column in REQUIRED_INDEXES[obj_type]:
                if column != 'gramps_id':  # gramps_id index already created
                    self.conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{obj_type}_{column} 
                        ON {obj_type} ({column})
                    """)
        
        # Then add our enhanced indexes for better performance
        if obj_type == 'person':
            # Name searches
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_person_names 
                    ON person USING GIN ((json_data->'names'))
            """)
            
            # Birth/death dates
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_person_birth_date 
                    ON person ((json_data->'birth_ref_index'->>'date'))
            """)
            
        elif obj_type == 'family':
            # Parent searches
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_family_parents 
                    ON family USING GIN ((json_data->'parent_handles'))
            """)
            
        elif obj_type == 'event':
            # Event type and date
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_event_type_date 
                    ON event ((json_data->>'type'), (json_data->>'date'))
            """)
            
        elif obj_type == 'place':
            # Place hierarchy
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_place_hierarchy 
                    ON place USING GIN ((json_data->'placeref_list'))
            """)
            
        elif obj_type == 'source':
            # Source title
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_source_title 
                    ON source ((json_data->>'title'))
            """)
            
        elif obj_type == 'note':
            # Full-text search on notes
            try:
                # Check if pg_trgm is loaded
                cur = self.conn.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'
                    )
                """)
                if cur.fetchone()[0]:
                    self.conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_note_text_trgm
                            ON note USING GIN ((json_data->>'text') gin_trgm_ops)
                    """)
            except Exception as e:
                self.log.debug(f"Could not create trigram index on notes: {e}")
    
    def _create_sync_trigger(self, obj_type):
        """Create trigger to sync secondary columns from JSONB data."""
        if obj_type not in REQUIRED_COLUMNS:
            return
            
        # Build the SET clause for the trigger
        set_clauses = []
        for col_name, json_path in REQUIRED_COLUMNS[obj_type].items():
            # Replace json_data with NEW.json_data in the path
            trigger_path = json_path.replace('json_data', 'NEW.json_data')
            set_clauses.append(f"NEW.{col_name} = {trigger_path}")
        
        set_sql = ";\n        ".join(set_clauses)
        
        # Create the trigger function
        self.conn.execute(f"""
            CREATE OR REPLACE FUNCTION sync_{obj_type}_columns()
            RETURNS TRIGGER AS $$
            BEGIN
                {set_sql};
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Create the trigger
        self.conn.execute(f"""
            DROP TRIGGER IF EXISTS {obj_type}_sync_trigger ON {obj_type};
            
            CREATE TRIGGER {obj_type}_sync_trigger
            BEFORE INSERT OR UPDATE OF json_data ON {obj_type}
            FOR EACH ROW
            EXECUTE FUNCTION sync_{obj_type}_columns();
        """)
    
    def _create_enhanced_features(self):
        """Create PostgreSQL-specific enhanced features."""
        
        # Create custom functions for common queries
        self.conn.execute("""
            CREATE OR REPLACE FUNCTION get_person_name(json_data JSONB)
            RETURNS TEXT AS $$
            DECLARE
                name_obj JSONB;
            BEGIN
                name_obj := json_data->'names'->0;
                RETURN COALESCE(
                    name_obj->>'first_name' || ' ' || name_obj->>'surname',
                    name_obj->>'first_name',
                    name_obj->>'surname',
                    'Unknown'
                );
            END;
            $$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;
        """)
        
        # Create function for relationship queries
        self.conn.execute("""
            CREATE OR REPLACE FUNCTION get_family_members(family_handle TEXT)
            RETURNS TABLE(handle TEXT, role TEXT) AS $$
            BEGIN
                -- Get parents
                RETURN QUERY
                SELECT jsonb_array_elements_text(f.json_data->'parent_handles'), 'parent'::TEXT
                FROM family f
                WHERE f.handle = family_handle;
                
                -- Get children
                RETURN QUERY
                SELECT jsonb_array_elements_text(f.json_data->'child_ref_list'), 'child'::TEXT
                FROM family f
                WHERE f.handle = family_handle;
            END;
            $$ LANGUAGE plpgsql STABLE PARALLEL SAFE;
        """)
        
        # Enable extensions if available
        self._enable_useful_extensions()
    
    def _enable_useful_extensions(self):
        """Enable PostgreSQL extensions that benefit genealogy queries."""
        
        extensions = [
            ('pg_trgm', 'Trigram similarity searches'),
            ('btree_gin', 'Better GIN index performance'),
            ('intarray', 'Array operations'),
        ]
        
        for ext_name, description in extensions:
            if self._check_extension_available(ext_name):
                try:
                    self.conn.execute(f"CREATE EXTENSION IF NOT EXISTS {ext_name}")
                    self.log.info(f"Enabled {ext_name} extension: {description}")
                except Exception as e:
                    self.log.debug(f"Could not enable {ext_name}: {e}")
    
    def _check_extension_available(self, extension_name):
        """Check if a PostgreSQL extension is available."""
        self.conn.execute("""
            SELECT COUNT(*) FROM pg_available_extensions 
            WHERE name = %s
        """, [extension_name])
        return self.conn.fetchone()[0] > 0
    
    def _get_schema_version(self):
        """Get current schema version from metadata."""
        self.conn.execute(
            "SELECT value FROM metadata WHERE setting = 'schema_version'"
        )
        row = self.conn.fetchone()
        if row and row[0]:
            return pickle.loads(row[0])
        return 0
    
    def _set_schema_version(self, version):
        """Set schema version in metadata."""
        if self.use_jsonb:
            self.conn.execute("""
                INSERT INTO metadata (setting, value, json_value)
                VALUES ('schema_version', %s, %s)
                ON CONFLICT (setting) DO UPDATE
                SET value = EXCLUDED.value,
                    json_value = EXCLUDED.json_value,
                    updated_at = CURRENT_TIMESTAMP
            """, [pickle.dumps(version), Jsonb(version)])
        else:
            self.conn.execute("""
                INSERT INTO metadata (setting, value)
                VALUES ('schema_version', %s)
                ON CONFLICT (setting) DO UPDATE
                SET value = EXCLUDED.value
            """, [pickle.dumps(version)])
    
    def _upgrade_schema(self, from_version):
        """
        Upgrade schema from one version to another.
        
        This method will handle future schema upgrades.
        """
        # Future schema upgrades will be implemented here
        # For now, just update the version
        if from_version < 1:
            # Initial version - no upgrades needed yet
            pass
        
        # Update version
        self._set_schema_version(SCHEMA_VERSION)
        self.conn.commit()
    
    def get_schema_info(self):
        """Get information about the current schema."""
        info = {
            'version': self._get_schema_version(),
            'use_jsonb': self.use_jsonb,
            'tables': {}
        }
        
        # Get table information
        self.conn.execute("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size(table_schema||'.'||table_name)) as size,
                   (SELECT COUNT(*) FROM information_schema.columns c 
                    WHERE c.table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        for table_name, size, column_count in self.conn.fetchall():
            info['tables'][table_name] = {
                'size': size,
                'columns': column_count
            }
        
        return info