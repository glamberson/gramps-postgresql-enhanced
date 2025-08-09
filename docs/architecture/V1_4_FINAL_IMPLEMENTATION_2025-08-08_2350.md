# PostgreSQL Enhanced v1.4 Final Implementation
*Date: 2025-08-08 23:50*

## Complete v1.4 Load Method with Robust Mode Handling

```python
import os
import time
from typing import Optional, Union, Any
from gramps.gen.db.dbconst import DBMODE_R, DBMODE_W
from gramps.gen.lib import Researcher, GenderStats
from gramps.gen.db.exceptions import DbVersionError

def load(
    self,
    directory: str,
    callback: Optional[callable] = None,
    mode: Optional[str] = None,
    force_schema_upgrade: bool = False,
    force_bsddb_upgrade: bool = False,
    force_bsddb_downgrade: bool = False,
    force_python_upgrade: bool = False,
    update: bool = True,
    username: Optional[str] = None,
    password: Optional[str] = None,
    user: Optional[str] = None,
    **kwargs: Any
) -> bool:
    """
    Load a PostgreSQL Enhanced database with full Gramps compatibility.
    
    This method initializes all required DBAPI attributes while maintaining
    PostgreSQL-native design principles. It handles both monolithic mode
    (multiple trees with table prefixes) and separate mode (one tree per database).
    
    :param directory: Path to database directory or connection string.
                     For PostgreSQL, this is typically a tree identifier
                     or connection information.
    :type directory: str
    
    :param callback: Progress callback function for long operations.
                    Currently unused but kept for API compatibility.
    :type callback: Optional[callable]
    
    :param mode: Database open mode - DBMODE_R for read-only, DBMODE_W for read-write.
                Defaults to read-write mode.
    :type mode: Optional[str]
    
    :param force_schema_upgrade: Force schema upgrade even if not needed.
                                 Ignored for PostgreSQL (uses native migrations).
    :type force_schema_upgrade: bool
    
    :param force_bsddb_upgrade: Legacy BSDDB upgrade flag. Ignored.
    :type force_bsddb_upgrade: bool
    
    :param force_bsddb_downgrade: Legacy BSDDB downgrade flag. Ignored.
    :type force_bsddb_downgrade: bool
    
    :param force_python_upgrade: Force Python version upgrade. Ignored.
    :type force_python_upgrade: bool
    
    :param update: Whether to update files. Kept for compatibility.
    :type update: bool
    
    :param username: Database username. Can also be passed as 'user'.
    :type username: Optional[str]
    
    :param password: Database password for authentication.
    :type password: Optional[str]
    
    :param user: Alternative parameter for username.
    :type user: Optional[str]
    
    :param kwargs: Additional keyword arguments for future compatibility.
    :type kwargs: Any
    
    :returns: Always returns True to indicate successful load.
    :rtype: bool
    
    :raises DbVersionError: If database version is incompatible.
    :raises DbConnectionError: If connection to PostgreSQL fails.
    
    .. versionadded:: 1.4
        Added full DBAPI compatibility attributes.
        Added mode-aware metadata handling for monolithic mode.
        Added recent files tracking for PostgreSQL databases.
    
    .. note::
        In monolithic mode, all metadata is prefixed with the tree identifier
        to maintain isolation between trees sharing the same database.
    
    .. seealso::
        :meth:`_initialize` : PostgreSQL connection initialization
        :meth:`_initialize_mode_aware_metadata` : Mode-specific metadata setup
    """
    # Handle both 'user' and 'username' parameters for flexibility
    actual_username = username or user or None
    actual_password = password or None
    
    # Store original directory for later use
    self._original_directory = directory
    
    # PostgreSQL-native initialization
    self._initialize(directory, actual_username, actual_password)
    
    # CRITICAL: Set database open flag - without this, Gramps Web returns 0 records
    self.db_is_open = True
    
    # Set read-only mode based on parameter
    self.readonly = mode == DBMODE_R if mode else False
    
    # Initialize change tracking
    self.has_changed = 0
    
    # Set minimal directory attributes for compatibility
    self._directory = directory
    self.path = directory  # Some Gramps code expects this
    
    # Initialize all DBAPI-required attributes with mode awareness
    self._initialize_mode_aware_metadata()
    
    # Set up undo manager (keep our existing approach)
    from gramps.gen.db.generic import DbGenericUndo
    self.undolog = None
    self.undodb = DbGenericUndo(self, self.undolog)
    self.undodb.open()
    
    # Version checking (modified to skip file-based upgrades)
    self._check_version_compatibility()
    
    # Update recent files tracking with timestamp
    self._update_recent_files()
    
    # Set version to prevent upgrade prompts
    self._set_metadata("version", "21")
    
    return True


def _initialize_mode_aware_metadata(self) -> None:
    """
    Initialize all DBAPI-required metadata with mode awareness.
    
    This method handles the critical difference between monolithic and separate modes:
    
    - **Monolithic Mode**: Multiple trees in one database with table prefixes.
                          All metadata is prefixed to maintain tree isolation.
    - **Separate Mode**: One tree per database, standard metadata keys.
    
    :returns: None
    :rtype: None
    
    .. important::
        In monolithic mode, failing to prefix metadata would cause data leakage
        between trees, including shared ID counters and mixed surname lists.
    
    .. versionadded:: 1.4
        Mode-aware metadata initialization for proper tree isolation.
    """
    # Initialize bookmarks (always needed)
    self._initialize_bookmarks()
    
    # Initialize ID counters with mode awareness
    self._initialize_id_counters()
    
    # Load surname list with mode awareness
    self.surname_list = self._get_mode_aware_surname_list()
    
    # Load gender statistics
    gstats = self._get_mode_aware_metadata("gender_stats", {})
    self.genderStats = GenderStats(gstats)
    
    # Initialize all custom type attributes
    self._initialize_custom_types()
    
    # Load name formats and researcher info
    self.name_formats = self._get_mode_aware_metadata("name_formats", [])
    self.owner = self._get_mode_aware_metadata("researcher", default=Researcher())
    
    # Set serializer (always JSON for PostgreSQL Enhanced)
    self.set_serializer("json")


def _get_mode_aware_metadata(self, key: str, default: Any = None) -> Any:
    """
    Retrieve metadata with mode awareness.
    
    In monolithic mode, prefixes the key with the tree identifier to maintain
    isolation between trees. In separate mode, uses the key as-is.
    
    :param key: The metadata key to retrieve.
    :type key: str
    
    :param default: Default value if metadata doesn't exist.
    :type default: Any
    
    :returns: The metadata value or default.
    :rtype: Any
    
    :Example:
        >>> # In monolithic mode with tree_6894f36d_ prefix:
        >>> self._get_mode_aware_metadata("pmap_index", 0)
        # Actually retrieves "tree_6894f36d_pmap_index"
        
        >>> # In separate mode:
        >>> self._get_mode_aware_metadata("pmap_index", 0)  
        # Retrieves "pmap_index" directly
    
    .. versionadded:: 1.4
        Mode-aware metadata retrieval.
    """
    if self.table_prefix:  # Monolithic mode
        # Remove trailing underscore and prefix the key
        tree_id = self.table_prefix.rstrip('_')
        actual_key = f"{tree_id}_{key}"
    else:  # Separate mode
        actual_key = key
    
    return self._get_metadata(actual_key, default)


def _set_mode_aware_metadata(self, key: str, value: Any) -> None:
    """
    Set metadata with mode awareness.
    
    In monolithic mode, prefixes the key with the tree identifier to maintain
    isolation between trees. In separate mode, uses the key as-is.
    
    :param key: The metadata key to set.
    :type key: str
    
    :param value: The value to store.
    :type value: Any
    
    :returns: None
    :rtype: None
    
    .. versionadded:: 1.4
        Mode-aware metadata storage.
    """
    if self.table_prefix:  # Monolithic mode
        tree_id = self.table_prefix.rstrip('_')
        actual_key = f"{tree_id}_{key}"
    else:  # Separate mode
        actual_key = key
    
    self._set_metadata(actual_key, value)


def _initialize_bookmarks(self) -> None:
    """
    Initialize all bookmark collections for the database.
    
    Loads bookmarks for all Gramps object types. In monolithic mode,
    bookmarks are isolated per tree through prefixed metadata keys.
    
    :returns: None
    :rtype: None
    
    .. note::
        Bookmarks are stored as lists of handles in the metadata table.
        Empty lists are used if no bookmarks exist yet.
    
    .. versionadded:: 1.4
        Complete bookmark initialization for Gramps Web compatibility.
    """
    bookmark_types = [
        'bookmarks',           # Person bookmarks
        'family_bookmarks',    # Family bookmarks
        'event_bookmarks',     # Event bookmarks
        'source_bookmarks',    # Source bookmarks
        'citation_bookmarks',  # Citation bookmarks
        'repo_bookmarks',      # Repository bookmarks
        'media_bookmarks',     # Media bookmarks
        'place_bookmarks',     # Place bookmarks
        'note_bookmarks'       # Note bookmarks
    ]
    
    for bookmark_type in bookmark_types:
        # Get the bookmark attribute (e.g., self.bookmarks)
        bookmark_attr = getattr(self, bookmark_type)
        # Load with mode-aware metadata
        bookmarks_data = self._get_mode_aware_metadata(bookmark_type, [])
        bookmark_attr.load(bookmarks_data)


def _initialize_id_counters(self) -> None:
    """
    Initialize ID generation counters with mode awareness.
    
    These counters are critical for generating unique Gramps IDs for new objects.
    In monolithic mode, each tree maintains its own set of counters to prevent
    ID collisions between trees.
    
    :returns: None
    :rtype: None
    
    .. important::
        In monolithic mode, sharing counters between trees would cause
        ID collisions. Each tree MUST have its own counter set.
    
    .. note::
        Future enhancement: Consider using PostgreSQL sequences for better
        concurrency support and atomic ID generation.
    
    .. versionadded:: 1.4
        Mode-aware ID counter initialization.
    """
    counter_mappings = {
        'cmap_index': 0,  # Citation ID counter
        'smap_index': 0,  # Source ID counter
        'emap_index': 0,  # Event ID counter
        'pmap_index': 0,  # Person ID counter
        'fmap_index': 0,  # Family ID counter
        'lmap_index': 0,  # Place (Location) ID counter
        'omap_index': 0,  # Media Object ID counter
        'rmap_index': 0,  # Repository ID counter
        'nmap_index': 0,  # Note ID counter
    }
    
    for counter_name, default_value in counter_mappings.items():
        value = self._get_mode_aware_metadata(counter_name, default_value)
        setattr(self, counter_name, value)
    
    # Optional: Create PostgreSQL sequences for better concurrency
    if hasattr(self, '_create_id_sequences'):
        self._create_id_sequences()


def _initialize_custom_types(self) -> None:
    """
    Initialize all custom type attributes for the database.
    
    These attributes define custom types that users have created for various
    Gramps objects (events, attributes, etc.). They populate dropdown menus
    in the Gramps UI.
    
    :returns: None
    :rtype: None
    
    .. note::
        Custom types are stored as sets to ensure uniqueness.
        Empty sets are used if no custom types exist yet.
    
    .. versionadded:: 1.4
        Complete custom type initialization for UI compatibility.
    """
    custom_type_mappings = {
        'event_names': set(),           # Custom event types
        'family_attributes': set(),     # Custom family attributes  
        'individual_attributes': set(), # Custom person attributes
        'source_attributes': set(),     # Custom source attributes
        'marker_names': set(),          # Custom marker types
        'child_ref_types': set(),       # Custom child reference types
        'family_rel_types': set(),      # Custom family relationship types
        'event_role_names': set(),      # Custom event role types
        'name_types': set(),            # Custom name types
        'origin_types': set(),          # Custom origin types
        'repository_types': set(),      # Custom repository types
        'note_types': set(),            # Custom note types
        'source_media_types': set(),    # Custom source media types
        'url_types': set(),             # Custom URL types
        'media_attributes': set(),      # Custom media attributes
        'event_attributes': set(),      # Custom event attributes
        'place_types': set(),           # Custom place types
    }
    
    # Map internal names to metadata keys
    metadata_key_map = {
        'family_attributes': 'fattr_names',
        'individual_attributes': 'pattr_names',
        'source_attributes': 'sattr_names',
        'source_media_types': 'sm_types',
        'media_attributes': 'mattr_names',
        'event_attributes': 'eattr_names',
    }
    
    for attr_name, default_value in custom_type_mappings.items():
        # Get the metadata key (some have different names in metadata)
        metadata_key = metadata_key_map.get(attr_name, attr_name)
        value = self._get_mode_aware_metadata(metadata_key, default_value)
        setattr(self, attr_name, value)


def _get_mode_aware_surname_list(self) -> list:
    """
    Retrieve the surname list with mode awareness.
    
    In monolithic mode, returns surnames only from the current tree's person table.
    In separate mode, returns surnames from the single person table.
    
    :returns: Sorted list of unique surnames in the tree.
    :rtype: list
    
    :raises DatabaseError: If the query fails.
    
    .. important::
        In monolithic mode, querying all person tables would leak data
        between trees. We MUST query only the current tree's table.
    
    :Example:
        >>> # Monolithic mode with tree_6894f36d_ prefix:
        >>> surnames = self._get_mode_aware_surname_list()
        # Queries: SELECT DISTINCT ... FROM tree_6894f36d_person
        
        >>> # Separate mode:
        >>> surnames = self._get_mode_aware_surname_list()
        # Queries: SELECT DISTINCT ... FROM person
    
    .. versionadded:: 1.4
        Mode-aware surname list retrieval.
    """
    if self.table_prefix:  # Monolithic mode
        table_name = f"{self.table_prefix}person"
    else:  # Separate mode
        table_name = "person"
    
    query = f"""
        SELECT DISTINCT 
            json_data->'primary_name'->>'surname' as surname
        FROM {table_name}
        WHERE json_data IS NOT NULL 
        AND json_data->'primary_name'->>'surname' IS NOT NULL
        AND json_data->'primary_name'->>'surname' != ''
        ORDER BY surname
    """
    
    try:
        result = self.dbapi.execute(query)
        return [row[0] for row in result.fetchall()]
    except Exception as e:
        LOG.warning(f"Failed to load surname list: {e}")
        return []


def _check_version_compatibility(self) -> None:
    """
    Check database version compatibility.
    
    Unlike the parent DBAPI implementation, this skips file-based upgrade
    operations since PostgreSQL Enhanced uses native database migrations.
    
    :returns: None
    :rtype: None
    
    :raises DbVersionError: If database version is newer than this code supports.
    
    .. note::
        We only check if the database is too new. Older versions are handled
        through PostgreSQL's native migration system, not file operations.
    
    .. versionadded:: 1.4
        PostgreSQL-appropriate version checking.
    """
    dbversion = int(self._get_mode_aware_metadata("version", default="21"))
    
    # Check if database is too new for this code
    if dbversion > self.VERSION[0]:
        self.close()
        raise DbVersionError(dbversion, self.VERSION[0], self.VERSION[0])
    
    # We don't run file-based upgrades - PostgreSQL handles schema migrations
    # through its own migration system (see migration.py)
    if dbversion < self.VERSION[0]:
        LOG.info(f"Database version {dbversion} < {self.VERSION[0]}, "
                 f"but PostgreSQL migrations handle this automatically")


def _update_recent_files(self) -> None:
    """
    Update Gramps' recent files tracking with current timestamp.
    
    This fixes the "Last Accessed: NEVER" issue by properly registering
    database access with Gramps' recent files system. Since PostgreSQL
    databases don't have filesystem paths, we create a meaningful virtual path.
    
    :returns: None
    :rtype: None
    
    .. note::
        The virtual path format is:
        - Monolithic: postgresql://tree_identifier
        - Separate: postgresql://database_name
        
        This provides a meaningful identifier in the recent files list.
    
    .. versionadded:: 1.4
        Recent files tracking for PostgreSQL databases.
    """
    try:
        from gramps.gen.recentfiles import recent_files
        
        # Create a meaningful virtual path for PostgreSQL
        if self.table_prefix:
            # Monolithic mode: use tree identifier
            tree_id = self.table_prefix.rstrip('_').replace('tree_', '')
            virtual_path = f"postgresql://monolithic/{tree_id}"
            display_name = f"PostgreSQL Tree: {tree_id}"
        else:
            # Separate mode: use database/directory name
            if '/' in str(self._original_directory):
                db_name = self._original_directory.split('/')[-1]
            else:
                db_name = self._original_directory
            virtual_path = f"postgresql://separate/{db_name}"
            display_name = f"PostgreSQL: {db_name}"
        
        # Get the tree name from metadata if available
        tree_name = self._get_mode_aware_metadata("name", display_name)
        
        # Update recent files with current timestamp
        # This will show the current time in "Last Accessed" field
        recent_files(virtual_path, tree_name)
        
        LOG.debug(f"Updated recent files: {virtual_path} -> {tree_name}")
        
    except Exception as e:
        # Don't fail the entire load if recent files update fails
        LOG.warning(f"Could not update recent files tracking: {e}")


def _create_id_sequences(self) -> None:
    """
    Create PostgreSQL sequences for ID generation (optional enhancement).
    
    This is an optional enhancement that uses PostgreSQL sequences instead
    of counter values for ID generation. Sequences provide better concurrency
    and atomic operations.
    
    :returns: None
    :rtype: None
    
    .. note::
        Sequences are created with IF NOT EXISTS, so this is safe to call
        multiple times. Each sequence corresponds to an ID counter.
    
    .. versionadded:: 1.4
        Optional PostgreSQL sequence support for ID generation.
    """
    if not hasattr(self.dbapi, 'execute'):
        return
    
    sequence_names = {
        'person': 'pmap',
        'family': 'fmap',
        'event': 'emap',
        'place': 'lmap',
        'source': 'smap',
        'citation': 'cmap',
        'media': 'omap',
        'repository': 'rmap',
        'note': 'nmap'
    }
    
    for object_type, counter_prefix in sequence_names.items():
        if self.table_prefix:
            # Monolithic mode: prefix the sequence name
            seq_name = f"{self.table_prefix}{counter_prefix}_seq"
        else:
            # Separate mode: standard sequence name
            seq_name = f"{counter_prefix}_seq"
        
        try:
            # Create sequence if it doesn't exist
            self.dbapi.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq_name}")
            
            # Get current counter value
            counter_attr = f"{counter_prefix}_index"
            current_value = getattr(self, counter_attr, 0)
            
            # Set sequence to start at current counter value
            if current_value > 0:
                self.dbapi.execute(
                    f"SELECT setval('{seq_name}', %s, false)",
                    [current_value]
                )
        except Exception as e:
            LOG.debug(f"Could not create sequence {seq_name}: {e}")
            # Fall back to counter-based ID generation
```

## Summary

This implementation:

1. **Fixes "Last Accessed: NEVER"** by creating virtual PostgreSQL paths and updating recent files with timestamps
2. **Robustly handles monolithic vs separate modes** with prefixed metadata and table-specific queries
3. **Includes comprehensive Sphinx-compatible docstrings** with examples, warnings, and version notes
4. **Maintains PostgreSQL-native design** while providing full DBAPI compatibility

The key innovation is treating PostgreSQL databases as first-class citizens with their own virtual paths, rather than trying to fake filesystem paths.