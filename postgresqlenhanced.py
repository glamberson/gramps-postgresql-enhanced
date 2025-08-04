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

# -------------------------------------------------------------------------
#
# Constants
#
# -------------------------------------------------------------------------
MIN_PSYCOPG_VERSION = (3, 1)
MIN_POSTGRESQL_VERSION = 15

# Create logger
LOG = logging.getLogger(".PostgreSQLEnhanced")

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
        # If so, use our hardcoded connection for now
        if directory and os.path.isabs(directory) and '/grampsdb/' in directory:
            # This is a Gramps-generated path, use our PostgreSQL connection
            # TODO: Read connection settings from a config file or environment
            connection_string = "postgresql://genealogy_user:GenealogyData2025@192.168.10.90:5432/gramps_test_db"
            LOG.info(f"Using PostgreSQL connection instead of file path: {directory}")
        else:
            connection_string = directory
        
        # Parse connection options
        self._parse_connection_options(connection_string)
        
        # Store path for compatibility
        self.path = directory
        
        # Create connection
        try:
            self.dbapi = PostgreSQLConnection(connection_string, username, password)
        except Exception as e:
            raise DbConnectionError(str(e), connection_string)
        
        # Set serializer - DBAPI expects JSONSerializer
        # JSONSerializer has object_to_data method that DBAPI needs
        self.serializer = JSONSerializer()
        
        # Initialize schema
        schema = PostgreSQLSchema(self.dbapi, use_jsonb=self._use_jsonb)
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
        
        # Call parent's load to set up undo manager and other base functionality
        # Pass the directory and callback to satisfy the parent's requirements
        super().load(directory, callback, mode or "w")
    
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
        Override DBAPI's _update_secondary_values.
        
        We don't need to update secondary columns because:
        1. All data is already in json_data
        2. We use JSONB indexes for queries
        3. Storing in two places violates DRY and risks inconsistency
        """
        # Do nothing - data is already in JSONB
        pass
    
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