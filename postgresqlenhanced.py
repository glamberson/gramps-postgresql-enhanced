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
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
PostgreSQL Enhanced Database Backend for Gramps

This backend provides advanced PostgreSQL features including:
- JSONB storage for powerful queries
- Full compatibility with existing Gramps data
- Migration from SQLite and standard PostgreSQL backends
- Advanced relationship queries using recursive CTEs
- Full-text search capabilities
- Optional extensions support (pgvector, Apache AGE, PostGIS)
"""

# -------------------------------------------------------------------------
#
# Standard python modules
#
# -------------------------------------------------------------------------
import logging
import os
import re
import pickle
import json
from urllib.parse import urlparse, parse_qs

# -------------------------------------------------------------------------
#
# PostgreSQL modules
#
# -------------------------------------------------------------------------
try:
    import psycopg
    from psycopg import sql
    from psycopg.types.json import Jsonb
    from psycopg.rows import dict_row
    PSYCOPG_AVAILABLE = True
    PSYCOPG_VERSION = tuple(map(int, psycopg.__version__.split('.')[:2]))
except ImportError:
    PSYCOPG_AVAILABLE = False
    PSYCOPG_VERSION = (0, 0)

# -------------------------------------------------------------------------
#
# Gramps modules
#
# -------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.db.dbconst import ARRAYSIZE
from gramps.plugins.db.dbapi.dbapi import DBAPI
from gramps.gen.db.exceptions import DbConnectionError
from gramps.gen.lib.serialize import BlobSerializer, JSONSerializer

# Get translation function for addon
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

# Import local modules - use absolute imports for Gramps plugins
import sys
import os
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from connection import PostgreSQLConnection
from schema import PostgreSQLSchema
from migration import MigrationManager
from queries import EnhancedQueries
from schema_columns import REQUIRED_COLUMNS

# -------------------------------------------------------------------------
#
# Constants
#
# -------------------------------------------------------------------------
MIN_PSYCOPG_VERSION = (3, 1)
MIN_POSTGRESQL_VERSION = 15

# Import debugging utilities
try:
    from .debug_utils import (
        DebugContext, timed_method, format_sql_query, 
        QueryProfiler, TransactionTracker, ConnectionMonitor
    )
    DEBUG_AVAILABLE = True
except ImportError:
    # Fallback if debug_utils not available
    DEBUG_AVAILABLE = False
    def timed_method(func):
        return func

# Create logger
LOG = logging.getLogger(".PostgreSQLEnhanced")

# Enable debug logging if environment variable is set
DEBUG_ENABLED = os.environ.get('GRAMPS_POSTGRESQL_DEBUG')
if DEBUG_ENABLED:
    LOG.setLevel(logging.DEBUG)
    # Also add a file handler for detailed debugging
    debug_handler = logging.FileHandler(
        os.path.expanduser('~/.gramps/postgresql_enhanced_debug.log')
    )
    debug_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    ))
    LOG.addHandler(debug_handler)
    LOG.debug("Debug logging enabled for PostgreSQL Enhanced")
    
    if DEBUG_AVAILABLE:
        LOG.debug("Advanced debugging features available")

# -------------------------------------------------------------------------
#
# PostgreSQLEnhanced class
#
# -------------------------------------------------------------------------
class PostgreSQLEnhanced(DBAPI):
    """
    PostgreSQL Enhanced interface for Gramps.
    
    Provides advanced PostgreSQL features while maintaining
    full compatibility with the standard Gramps DBAPI interface.
    """

    def __init__(self):
        """Initialize the PostgreSQL Enhanced backend."""
        super().__init__()
        # Check psycopg3 availability
        if not PSYCOPG_AVAILABLE:
            raise ImportError(
                _("psycopg3 is required for PostgreSQL Enhanced support. "
                  "Install with: pip install 'psycopg[binary]'"))
        
        # Check psycopg3 version
        if PSYCOPG_VERSION < MIN_PSYCOPG_VERSION:
            raise ImportError(
                _("psycopg3 version %(installed)s is too old. "
                  "Version %(required)s or newer is required.") % {
                    'installed': '.'.join(map(str, PSYCOPG_VERSION)),
                    'required': '.'.join(map(str, MIN_PSYCOPG_VERSION))})
        # Initialize components
        self.migration_manager = None
        self.enhanced_queries = None
        self._use_jsonb = True  # Default to using JSONB
        
        # Initialize debug context if available
        self._debug_context = None
        if DEBUG_ENABLED and DEBUG_AVAILABLE:
            self._debug_context = DebugContext(LOG)
            LOG.debug("Debug context initialized")
    
    def get_summary(self):
        """
        Return a dictionary of information about this database backend.
        """
        summary = super().get_summary()
        
        # Basic info
        summary.update({
            _("Database Backend"): "PostgreSQL Enhanced",
            _("Database module"): f"psycopg {psycopg.__version__}",
            _("Database module location"): psycopg.__file__,
            _("JSONB support"): _("Yes") if self._use_jsonb else _("No"),
        })
        
        # Get PostgreSQL version and features if connected
        if hasattr(self, 'dbapi') and self.dbapi:
            try:
                # PostgreSQL version
                self.dbapi.execute("SELECT version()")
                version_str = self.dbapi.fetchone()[0]
                match = re.search(r'PostgreSQL (\d+)\.(\d+)', version_str)
                if match:
                    pg_version = f"{match.group(1)}.{match.group(2)}"
                    pg_major = int(match.group(1))
                else:
                    pg_version = "Unknown"
                    pg_major = 0
                
                summary[_("Database version")] = pg_version
                
                # Check if version meets requirements
                if pg_major < MIN_POSTGRESQL_VERSION:
                    summary[_("Version warning")] = _(
                        "PostgreSQL %(version)s is below recommended "
                        "version %(recommended)s") % {
                            'version': pg_major,
                            'recommended': MIN_POSTGRESQL_VERSION
                        }
                
                # Check for extensions
                self.dbapi.execute("""
                    SELECT extname, extversion 
                    FROM pg_extension 
                    WHERE extname IN ('pgvector', 'age', 'postgis', 'hstore', 'pg_trgm')
                    ORDER BY extname
                """)
                extensions = [f"{name} {ver}" for name, ver in self.dbapi.fetchall()]
                if extensions:
                    summary[_("Extensions")] = ", ".join(extensions)
                
                # Database statistics
                self.dbapi.execute("""
                    SELECT 
                        pg_database_size(current_database()) as db_size,
                        (SELECT count(*) FROM person) as person_count,
                        (SELECT count(*) FROM family) as family_count,
                        (SELECT count(*) FROM event) as event_count
                """)
                stats = self.dbapi.fetchone()
                if stats and stats[0]:
                    # Format size nicely
                    size_mb = stats[0] / (1024 * 1024)
                    if size_mb < 1024:
                        size_str = f"{size_mb:.1f} MB"
                    else:
                        size_str = f"{size_mb/1024:.1f} GB"
                    
                    summary[_("Database size")] = size_str
                    if stats[1] is not None:
                        summary[_("Statistics")] = _(
                            "%(persons)d persons, %(families)d families, "
                            "%(events)d events") % {
                                'persons': stats[1] or 0,
                                'families': stats[2] or 0,
                                'events': stats[3] or 0
                            }
                
            except Exception as e:
                LOG.debug(f"Error getting database info: {e}")
        
        return summary
    
    def _initialize(self, directory, username, password):
        """
        Initialize the PostgreSQL Enhanced database connection.
        
        The 'directory' parameter contains connection information:
        - postgresql://user:pass@host:port/dbname
        - host:port:dbname:schema
        - dbname (for local connection)
        
        Special features can be enabled via query parameters:
        - ?use_jsonb=false  (disable JSONB, use blob only)
        - ?pool_size=10     (connection pool size)
        """
        # Check if this is a Gramps file-based path (like /home/user/.local/share/gramps/grampsdb/xxx)
        # or a test directory with connection_info.txt
        config_file = os.path.join(directory, 'connection_info.txt') if directory else None
        if directory and os.path.isabs(directory) and (
            '/grampsdb/' in directory or 
            (config_file and os.path.exists(config_file))
        ):
            # Extract tree name from path
            path_parts = directory.rstrip('/').split('/')
            tree_name = path_parts[-1] if path_parts else 'gramps_default'
            
            # Store directory for config file lookup
            self.directory = directory
            
            # Load connection configuration
            config = self._load_connection_config(directory)
            
            if config['database_mode'] == 'separate':
                # Separate database per tree
                db_name = tree_name
                self.table_prefix = ""
                self.shared_db_mode = False
                
                # Try to create database if it doesn't exist
                if config.get('user') and config.get('password'):
                    self._ensure_database_exists(db_name, config)
            else:
                # Shared database with table prefixes
                db_name = config.get('shared_database_name', 'gramps_shared')
                # Sanitize tree name for use as table prefix
                self.table_prefix = re.sub(r'[^a-zA-Z0-9_]', '_', tree_name) + "_"
                self.shared_db_mode = True
                LOG.info(f"Using shared database mode with prefix: {self.table_prefix}")
            
            # Build connection string
            connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{db_name}"
            
            LOG.info(f"Tree name: '{tree_name}', Database: '{db_name}', Mode: '{config['database_mode']}'")
        else:
            # Direct connection string
            connection_string = directory
            self.table_prefix = ""
            self.shared_db_mode = False
        
        # Parse connection options
        self._parse_connection_options(connection_string)
        
        # Store path for compatibility
        self.path = directory
        
        # Create connection
        try:
            self.dbapi = PostgreSQLConnection(connection_string, username, password)
            
            # In monolithic mode, wrap the connection to add table prefixes
            if hasattr(self, 'table_prefix') and self.table_prefix:
                self.dbapi = TablePrefixWrapper(self.dbapi, self.table_prefix)
                
        except Exception as e:
            raise DbConnectionError(str(e), connection_string)
        
        # Set serializer - DBAPI expects JSONSerializer
        # JSONSerializer has object_to_data method that DBAPI needs
        self.serializer = JSONSerializer()
        
        # Initialize schema with table prefix if in shared mode
        schema = PostgreSQLSchema(self.dbapi, use_jsonb=self._use_jsonb, 
                                table_prefix=getattr(self, 'table_prefix', ''))
        schema.check_and_init_schema()
        
        # Initialize migration manager
        self.migration_manager = MigrationManager(self.dbapi)
        
        # Initialize enhanced queries if JSONB is enabled
        if self._use_jsonb:
            self.enhanced_queries = EnhancedQueries(self.dbapi)
        
        # Log successful initialization
        LOG.info("PostgreSQL Enhanced initialized successfully")
        
        # Set database as writable
        self.readonly = False
        self._is_open = True
    
    def is_open(self):
        """Return True if the database is open."""
        return getattr(self, '_is_open', False)
    
    def open(self, value=None):
        """Open database - compatibility method for Gramps."""
        # Database is already open from load()
        return True
    
    def load(self, directory, callback=None, mode=None, force_schema_upgrade=False, 
             force_bsddb_upgrade=False, force_bsddb_downgrade=False, 
             force_python_upgrade=False, user=None, password=None, 
             username=None, *args, **kwargs):
        """
        Load database - Gramps compatibility method.
        
        Gramps calls this with various parameters, we only need directory, username, and password.
        """
        # Handle both 'user' and 'username' parameters
        actual_username = username or user or None
        actual_password = password or None
        
        # Call our initialize method
        self._initialize(directory, actual_username, actual_password)
        
        # Set up the undo manager without calling parent's full load
        # which tries to run upgrades on non-existent files
        from gramps.gen.db.generic import DbGenericUndo
        self.undolog = None
        self.undodb = DbGenericUndo(self, self.undolog)
        self.undodb.open()
        
        # Set proper version to avoid upgrade prompts
        self._set_metadata("version", "21")
    
    def _load_connection_config(self, directory):
        """Load connection configuration from connection_info.txt."""
        config_path = os.path.join(directory, 'connection_info.txt')
        config = {
            'host': 'localhost',
            'port': '5432', 
            'user': 'gramps_user',
            'password': 'gramps',
            'database_mode': 'separate',
            'shared_database_name': 'gramps_shared'
        }
        
        if os.path.exists(config_path):
            LOG.info(f"Loading connection config from: {config_path}")
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        else:
            LOG.warning(f"No connection_info.txt found at {config_path}, using defaults")
            # Try to create template for user
            template_path = os.path.join(os.path.dirname(__file__), 'connection_info_template.txt')
            if os.path.exists(template_path):
                try:
                    import shutil
                    shutil.copy(template_path, config_path)
                    LOG.info(f"Created connection_info.txt template at {config_path}")
                    # Now read the template we just created
                    with open(config_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                config[key.strip()] = value.strip()
                    LOG.info(f"Loaded configuration from template")
                except Exception as e:
                    LOG.debug(f"Could not create config template: {e}")
        
        return config
    
    def _ensure_database_exists(self, db_name, config):
        """Create PostgreSQL database if it doesn't exist (for separate database mode)."""
        try:
            # Connect to 'postgres' database to check/create the target database
            temp_conn_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/postgres"
            temp_conn = psycopg.connect(temp_conn_string)
            temp_conn.autocommit = True
            
            with temp_conn.cursor() as cur:
                # Check if database exists
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    [db_name]
                )
                if not cur.fetchone():
                    # Create database using template with extensions
                    LOG.info(f"Creating new PostgreSQL database: {db_name}")
                    cur.execute(
                        sql.SQL("CREATE DATABASE {} TEMPLATE template_gramps").format(
                            sql.Identifier(db_name)
                        )
                    )
                    LOG.info(f"Successfully created database: {db_name}")
                else:
                    LOG.info(f"Database already exists: {db_name}")
            
            temp_conn.close()
            
        except psycopg.errors.InsufficientPrivilege:
            LOG.error(f"User '{config['user']}' lacks CREATE DATABASE privilege. "
                     f"Please create database '{db_name}' manually or grant CREATEDB privilege.")
            raise
        except Exception as e:
            LOG.error(f"Error checking/creating database: {e}")
            raise
    
    def _parse_connection_options(self, connection_string):
        """Parse connection options from the connection string."""
        if connection_string.startswith("postgresql://"):
            parsed = urlparse(connection_string)
            if parsed.query:
                params = parse_qs(parsed.query)
                # Check for JSONB disable flag
                if 'use_jsonb' in params:
                    self._use_jsonb = params['use_jsonb'][0].lower() != 'false'
    
    def _update_secondary_values(self, obj):
        """
        Update secondary columns from JSONB data.
        
        This extracts values from the JSONB column and updates the 
        secondary columns that DBAPI expects for queries.
        """
        table = obj.__class__.__name__.lower()
        # Use table prefix if in shared mode
        table_name = f"{self.table_prefix}{table}" if hasattr(self, 'table_prefix') else table
        
        # Get the JSON data
        json_obj = self.serializer.object_to_data(obj)
        
        # Build UPDATE statement based on object type
        if table in REQUIRED_COLUMNS:
            sets = []
            values = []
            
            for col_name, json_path in REQUIRED_COLUMNS[table].items():
                sets.append(f"{col_name} = ({json_path})")
            
            if sets:
                # Execute UPDATE using JSONB extraction
                query = f"""
                    UPDATE {table_name} 
                    SET {', '.join(sets)}
                    WHERE handle = %s
                """
                self.dbapi.execute(query, [obj.handle])
                
        # Also handle derived fields that DBAPI adds
        if table == 'person':
            # Extract given_name and surname if not already in REQUIRED_COLUMNS
            if 'given_name' not in REQUIRED_COLUMNS.get('person', {}):
                self.dbapi.execute(f"""
                    UPDATE {table_name}
                    SET given_name = COALESCE(json_data->'primary_name'->>'first_name', ''),
                        surname = COALESCE(json_data->'primary_name'->'surname_list'->0->>'surname', '')
                    WHERE handle = %s
                """, [obj.handle])
        elif table == 'place':
            # Handle enclosed_by if not in REQUIRED_COLUMNS
            if 'enclosed_by' not in REQUIRED_COLUMNS.get('place', {}):
                self.dbapi.execute(f"""
                    UPDATE {table_name}
                    SET enclosed_by = json_data->>'enclosed_by'
                    WHERE handle = %s
                """, [obj.handle])
    
    def close(self, *args, **kwargs):
        """Close the database connection."""
        if hasattr(self, 'dbapi') and self.dbapi:
            self.dbapi.close()
        self._is_open = False
        # Don't call super().close() as it expects file operations
    
    # Migration methods
    def has_migration_available(self):
        """Check if migration from another backend is available."""
        if self.migration_manager:
            return self.migration_manager.detect_migration_needed() is not None
        return False
    
    def migrate_from_sqlite(self, sqlite_path, callback=None):
        """
        Migrate data from a SQLite database.
        
        :param sqlite_path: Path to SQLite database file
        :param callback: Progress callback function
        """
        if not self.migration_manager:
            raise RuntimeError(_("Migration manager not initialized"))
        
        return self.migration_manager.migrate_from_sqlite(sqlite_path, callback)
    
    def migrate_from_postgresql(self, callback=None):
        """
        Upgrade from standard PostgreSQL backend to Enhanced.
        
        :param callback: Progress callback function
        """
        if not self.migration_manager:
            raise RuntimeError(_("Migration manager not initialized"))
        
        return self.migration_manager.upgrade_to_enhanced(callback)
    
    # Enhanced query methods (only available with JSONB)
    def find_common_ancestors(self, handle1, handle2):
        """Find common ancestors between two people."""
        if not self.enhanced_queries:
            raise RuntimeError(_("Enhanced queries require JSONB support"))
        return self.enhanced_queries.find_common_ancestors(handle1, handle2)
    
    def find_relationship_path(self, handle1, handle2, max_depth=15):
        """Find the shortest relationship path between two people."""
        if not self.enhanced_queries:
            raise RuntimeError(_("Enhanced queries require JSONB support"))
        return self.enhanced_queries.find_relationship_path(handle1, handle2, max_depth)
    
    def search_all_text(self, search_term):
        """Full-text search across all text fields."""
        if not self.enhanced_queries:
            raise RuntimeError(_("Enhanced queries require JSONB support"))
        return self.enhanced_queries.search_all_text(search_term)
    
    def get_statistics(self):
        """Get detailed database statistics."""
        stats = {
            'backend': 'PostgreSQL Enhanced',
            'jsonb_enabled': self._use_jsonb,
            'psycopg_version': psycopg.__version__,
        }
        
        if self.enhanced_queries:
            stats.update(self.enhanced_queries.get_statistics())
        
        return stats
    
    def _get_metadata(self, key, default="_"):
        """
        Override to handle table prefixes in monolithic mode.
        """
        if hasattr(self, 'table_prefix') and self.table_prefix:
            # In monolithic mode, use prefixed table name
            self.dbapi.execute(f"SELECT 1 FROM {self.table_prefix}metadata WHERE setting = %s", [key])
        else:
            # In separate mode, use standard query
            self.dbapi.execute("SELECT 1 FROM metadata WHERE setting = ?", [key])
        row = self.dbapi.fetchone()
        if row:
            self.dbapi.execute(f"SELECT value FROM {self.table_prefix if hasattr(self, 'table_prefix') and self.table_prefix else ''}metadata WHERE setting = %s", [key])
            row = self.dbapi.fetchone()
            if row and row[0]:
                try:
                    return pickle.loads(row[0])
                except:
                    return row[0]
        elif default == "_":
            return []
        else:
            return default
    
    def _set_metadata(self, key, value, use_txn=True):
        """
        Override to handle table prefixes in monolithic mode.
        """
        if use_txn:
            self._txn_begin()
        
        table_name = f"{self.table_prefix if hasattr(self, 'table_prefix') and self.table_prefix else ''}metadata"
        
        self.dbapi.execute(f"SELECT 1 FROM {table_name} WHERE setting = %s", [key])
        row = self.dbapi.fetchone()
        if row:
            self.dbapi.execute(
                f"UPDATE {table_name} SET value = %s WHERE setting = %s",
                [pickle.dumps(value), key]
            )
        else:
            self.dbapi.execute(
                f"INSERT INTO {table_name} (setting, value) VALUES (%s, %s)", 
                [key, pickle.dumps(value)]
            )
        if use_txn:
            self._txn_commit()


class TablePrefixWrapper:
    """
    Wraps a database connection to automatically add table prefixes in queries.
    
    This allows the standard DBAPI to work with prefixed tables in monolithic mode.
    """
    
    # Tables that should have prefixes
    PREFIXED_TABLES = {
        'person', 'family', 'event', 'place', 'source', 'citation',
        'repository', 'media', 'note', 'tag', 'metadata', 'reference',
        'gender_stats'
    }
    
    # Tables that are shared (no prefix)
    SHARED_TABLES = {'name_group', 'surname'}
    
    def __init__(self, connection, table_prefix):
        """Initialize wrapper with connection and prefix."""
        self._connection = connection
        self._prefix = table_prefix
        
    def execute(self, query, params=None):
        """Execute query with table prefixes added."""
        # Add prefixes to table names in the query
        modified_query = self._add_table_prefixes(query)
        
        # Log for debugging
        if query != modified_query:
            LOG.debug(f"Query modified: {query} -> {modified_query}")
            
        return self._connection.execute(modified_query, params)
    
    def cursor(self):
        """Return a wrapped cursor that prefixes queries."""
        # NO FALLBACK: Must wrap cursor to catch ALL queries
        return CursorPrefixWrapper(self._connection.cursor(), self._prefix)
    
    def _add_table_prefixes(self, query):
        """Add table prefixes to a query."""
        # NO FALLBACK: We must handle ALL query patterns comprehensively
        import re
        
        modified = query
        
        for table in self.PREFIXED_TABLES:
            # Match table name as whole word (not part of another word)
            # Handle ALL SQL patterns that DBAPI might generate
            patterns = [
                # SELECT patterns - MUST handle queries without keywords before FROM
                (rf'\bSELECT\s+(.+?)\s+FROM\s+({table})\b', 
                 lambda m: f"SELECT {m.group(1)} FROM {self._prefix}{m.group(2)}"),
                
                # Basic patterns with keywords before table name
                (rf'\b(FROM)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(JOIN)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(INTO)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(UPDATE)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(DELETE\s+FROM)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(INSERT\s+INTO)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(ALTER\s+TABLE)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(DROP\s+TABLE\s+IF\s+EXISTS)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+TABLE)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+INDEX\s+\S+\s+ON)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+UNIQUE\s+INDEX\s+\S+\s+ON)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(DROP\s+INDEX\s+IF\s+EXISTS\s+\S+\s+ON)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(REFERENCES)\s+({table})\b', rf'\1 {self._prefix}\2'),
                
                # EXISTS patterns
                (rf'\b(EXISTS)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\bEXISTS\s*\(\s*SELECT\s+.+?\s+FROM\s+({table})\b',
                 lambda m: m.group(0).replace(f'FROM {m.group(1)}', f'FROM {self._prefix}{m.group(1)}')),
                
                # Table name in WHERE clauses with table.column syntax
                (rf'\b({table})\.(\w+)', rf'{self._prefix}\1.\2'),
            ]
            
            for pattern, replacement in patterns:
                if callable(replacement):
                    # Use callable for complex replacements
                    modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE | re.DOTALL)
                else:
                    modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
        
        return modified
    
    def __getattr__(self, name):
        """Forward all other attributes to the wrapped connection."""
        return getattr(self._connection, name)


class CursorPrefixWrapper:
    """
    Wraps a database cursor to automatically add table prefixes in queries.
    """
    
    def __init__(self, cursor, table_prefix):
        """Initialize wrapper with cursor and prefix."""
        self._cursor = cursor
        self._prefix = table_prefix
        
    def execute(self, query, params=None):
        """Execute query with table prefixes added."""
        # Reuse the same prefix logic from TablePrefixWrapper
        modified_query = self._add_table_prefixes(query)
        
        # Log for debugging
        if query != modified_query:
            LOG.debug(f"Cursor query modified: {query} -> {modified_query}")
            
        return self._cursor.execute(modified_query, params)
    
    def _add_table_prefixes(self, query):
        """Add table prefixes to a query."""
        # NO FALLBACK: We must handle ALL query patterns comprehensively
        import re
        
        modified = query
        
        # Use same tables as TablePrefixWrapper
        PREFIXED_TABLES = TablePrefixWrapper.PREFIXED_TABLES
        
        for table in PREFIXED_TABLES:
            # Match table name as whole word (not part of another word)
            # Handle ALL SQL patterns that DBAPI might generate
            patterns = [
                # SELECT patterns - MUST handle queries without keywords before FROM
                (rf'\bSELECT\s+(.+?)\s+FROM\s+({table})\b', 
                 lambda m: f"SELECT {m.group(1)} FROM {self._prefix}{m.group(2)}"),
                
                # Basic patterns with keywords before table name
                (rf'\b(FROM)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(JOIN)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(INTO)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(UPDATE)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(DELETE\s+FROM)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(INSERT\s+INTO)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(ALTER\s+TABLE)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(DROP\s+TABLE\s+IF\s+EXISTS)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+TABLE)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+INDEX\s+\S+\s+ON)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(CREATE\s+UNIQUE\s+INDEX\s+\S+\s+ON)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(DROP\s+INDEX\s+IF\s+EXISTS\s+\S+\s+ON)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\b(REFERENCES)\s+({table})\b', rf'\1 {self._prefix}\2'),
                
                # EXISTS patterns
                (rf'\b(EXISTS)\s+({table})\b', rf'\1 {self._prefix}\2'),
                (rf'\bEXISTS\s*\(\s*SELECT\s+.+?\s+FROM\s+({table})\b',
                 lambda m: m.group(0).replace(f'FROM {m.group(1)}', f'FROM {self._prefix}{m.group(1)}')),
                
                # Table name in WHERE clauses with table.column syntax
                (rf'\b({table})\.(\w+)', rf'{self._prefix}\1.\2'),
            ]
            
            for pattern, replacement in patterns:
                if callable(replacement):
                    # Use callable for complex replacements
                    modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE | re.DOTALL)
                else:
                    modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
        
        return modified
    
    def __enter__(self):
        """Support context manager protocol."""
        self._cursor.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support context manager protocol."""
        return self._cursor.__exit__(exc_type, exc_val, exc_tb)
    
    def __getattr__(self, name):
        """Forward all other attributes to the wrapped cursor."""
        return getattr(self._cursor, name)