# PostgreSQL Enhanced v1.4 Implementation Plan
*Date: 2025-08-08 23:45*

## Answers to Critical Questions

### Q1: Why does "Last Accessed" always show "NEVER"?

**Root Cause**: The parent DBAPI's `load()` method calls this at the end:
```python
recent_files(filename, name)  # Updates the recent files list with timestamp
```

PostgreSQL Enhanced v1.3 never calls this, so Gramps never records that the database was accessed. This is tracked in Gramps' recent files system, not in the database itself.

**Solution for v1.4**: We need to call the recent files update. However, this expects a filesystem path, which doesn't make sense for PostgreSQL. We'll need to provide a virtual path or handle this specially.

### Q2: ID Counters & Surname Lists in Monolithic vs Separate Modes

**Critical Issue Identified**: You're absolutely right! In monolithic mode with table prefixes, each tree needs its own set of counters and surname lists.

#### ID Counters (Item 4)
**Problem**: 
- In **separate mode**: One set of counters per database (standard)
- In **monolithic mode**: Need counters PER TREE (with prefix)

**Solution**:
```python
if self.table_prefix:  # Monolithic mode
    # Each tree needs its own counters in metadata
    self.pmap_index = self._get_metadata(f"{self.table_prefix}pmap_index", 0)
    self.fmap_index = self._get_metadata(f"{self.table_prefix}fmap_index", 0)
    # OR use PostgreSQL sequences per tree
    CREATE SEQUENCE IF NOT EXISTS tree_6894f36d_person_id_seq;
else:  # Separate mode
    # Standard counters
    self.pmap_index = self._get_metadata("pmap_index", 0)
    self.fmap_index = self._get_metadata("fmap_index", 0)
```

#### Surname List (Item 5)
**Problem**:
- In **separate mode**: One surname list for the database
- In **monolithic mode**: Need surname list PER TREE

**Solution**:
```python
def get_surname_list(self):
    if self.table_prefix:  # Monolithic mode
        # Get surnames from this tree's person table only
        table_name = f"{self.table_prefix}person"
        query = f"""
            SELECT DISTINCT json_data->'primary_name'->>'surname' 
            FROM {table_name} 
            WHERE json_data IS NOT NULL
        """
    else:  # Separate mode
        # Standard query
        query = """
            SELECT DISTINCT json_data->'primary_name'->>'surname' 
            FROM person 
            WHERE json_data IS NOT NULL
        """
    return self.dbapi.execute(query).fetchall()
```

## Final v1.4 Implementation Based on Your Decisions

### Your Decisions:
1. ✅ **Include** - db_is_open flag
2. ✅ **Include** - Read-only mode  
3. ✅ **Include** - Bookmarks
4. ❓ **Include with mode-awareness** - ID counters (see solution above)
5. ❓ **Include with mode-awareness** - Surname list (see solution above)
6. ✅ **Include** - Gender statistics
7. ✅ **Include** - Custom type attributes (all 17)
8. ✅ **Include** - Name formats
9. ✅ **Include** - Database owner/researcher
10. ✅ **Include modified** - Serializer setup
11. ✅ **Include minimal** - Save path
12. ❌ **Skip** - Schema existence check
13. ✅ **Include modified** - Version checking
14. ✅ **Include** - has_changed counter
15. ✅ **Keep current** - Undo manager

## Complete v1.4 Implementation

```python
def load(
    self,
    directory,
    callback=None,
    mode=None,
    force_schema_upgrade=False,
    force_bsddb_upgrade=False,
    force_bsddb_downgrade=False,
    force_python_upgrade=False,
    update=True,
    username=None,
    password=None,
    user=None,
    **kwargs
):
    """
    PostgreSQL Enhanced v1.4 - Full Gramps compatibility with PostgreSQL-native design.
    
    Includes all necessary DBAPI attributes while maintaining our superior architecture.
    """
    # Handle both 'user' and 'username' parameters
    actual_username = username or user or None
    actual_password = password or None
    
    # Our PostgreSQL-native initialization
    self._initialize(directory, actual_username, actual_password)
    
    # 1. CRITICAL - Database open flag
    self.db_is_open = True
    
    # 2. Read-only mode support
    self.readonly = mode == DBMODE_R if mode else False
    
    # 3. Initialize all bookmark collections
    self._initialize_bookmarks()
    
    # 4. ID counters - MODE AWARE
    self._initialize_id_counters()
    
    # 5. Surname list - MODE AWARE
    self.surname_list = self.get_surname_list()
    
    # 6. Gender statistics
    gstats = self.get_gender_stats()
    self.genderStats = GenderStats(gstats)
    
    # 7. All custom type attributes
    self._initialize_custom_types()
    
    # 8. Name formats
    self.name_formats = self._get_metadata("name_formats", [])
    
    # 9. Database owner/researcher
    from gramps.gen.lib import Researcher
    self.owner = self._get_metadata("researcher", default=Researcher())
    
    # 10. Modified serializer setup (always JSON for PostgreSQL)
    self.set_serializer("json")
    
    # 11. Minimal save path (for compatibility)
    self._directory = directory
    self.path = directory  # Some code expects this
    
    # 13. Modified version checking (no file upgrades)
    dbversion = int(self._get_metadata("version", default="21"))
    if dbversion > self.VERSION[0]:
        self.close()
        raise DbVersionError(dbversion, self.VERSION[0], self.VERSION[0])
    # Skip file-based upgrades - we handle schema differently
    
    # 14. Change tracking counter
    self.has_changed = 0
    
    # 15. Keep current undo manager setup
    from gramps.gen.db.generic import DbGenericUndo
    self.undolog = None
    self.undodb = DbGenericUndo(self, self.undolog)
    self.undodb.open()
    
    # Set version to avoid upgrade prompts
    self._set_metadata("version", "21")
    
    # Update recent files (fixes "NEVER" issue)
    try:
        from gramps.gen.recentfiles import recent_files
        # For PostgreSQL, use a virtual path
        if self.table_prefix:
            virtual_path = f"postgresql://{self.table_prefix.rstrip('_')}"
        else:
            virtual_path = f"postgresql://{directory.split('/')[-1]}"
        recent_files(virtual_path, self._get_metadata("name", directory))
    except:
        pass  # Don't fail if recent files update fails

def _initialize_bookmarks(self):
    """Initialize all bookmark collections."""
    self.bookmarks.load(self._get_metadata("bookmarks", []))
    self.family_bookmarks.load(self._get_metadata("family_bookmarks", []))
    self.event_bookmarks.load(self._get_metadata("event_bookmarks", []))
    self.source_bookmarks.load(self._get_metadata("source_bookmarks", []))
    self.citation_bookmarks.load(self._get_metadata("citation_bookmarks", []))
    self.repo_bookmarks.load(self._get_metadata("repo_bookmarks", []))
    self.media_bookmarks.load(self._get_metadata("media_bookmarks", []))
    self.place_bookmarks.load(self._get_metadata("place_bookmarks", []))
    self.note_bookmarks.load(self._get_metadata("note_bookmarks", []))

def _initialize_id_counters(self):
    """
    Initialize ID counters - MODE AWARE.
    In monolithic mode, each tree has its own counters.
    """
    if self.table_prefix:  # Monolithic mode
        # Each tree needs its own counters
        prefix = self.table_prefix.rstrip('_')
        self.cmap_index = self._get_metadata(f"{prefix}_cmap_index", 0)
        self.smap_index = self._get_metadata(f"{prefix}_smap_index", 0)
        self.emap_index = self._get_metadata(f"{prefix}_emap_index", 0)
        self.pmap_index = self._get_metadata(f"{prefix}_pmap_index", 0)
        self.fmap_index = self._get_metadata(f"{prefix}_fmap_index", 0)
        self.lmap_index = self._get_metadata(f"{prefix}_lmap_index", 0)
        self.omap_index = self._get_metadata(f"{prefix}_omap_index", 0)
        self.rmap_index = self._get_metadata(f"{prefix}_rmap_index", 0)
        self.nmap_index = self._get_metadata(f"{prefix}_nmap_index", 0)
        
        # Optional: Create PostgreSQL sequences for better concurrency
        self._create_sequences_if_needed()
    else:  # Separate mode
        # Standard counters
        self.cmap_index = self._get_metadata("cmap_index", 0)
        self.smap_index = self._get_metadata("smap_index", 0)
        self.emap_index = self._get_metadata("emap_index", 0)
        self.pmap_index = self._get_metadata("pmap_index", 0)
        self.fmap_index = self._get_metadata("fmap_index", 0)
        self.lmap_index = self._get_metadata("lmap_index", 0)
        self.omap_index = self._get_metadata("omap_index", 0)
        self.rmap_index = self._get_metadata("rmap_index", 0)
        self.nmap_index = self._get_metadata("nmap_index", 0)

def _initialize_custom_types(self):
    """Initialize all custom type attributes."""
    self.event_names = self._get_metadata("event_names", set())
    self.family_attributes = self._get_metadata("fattr_names", set())
    self.individual_attributes = self._get_metadata("pattr_names", set())
    self.source_attributes = self._get_metadata("sattr_names", set())
    self.marker_names = self._get_metadata("marker_names", set())
    self.child_ref_types = self._get_metadata("child_refs", set())
    self.family_rel_types = self._get_metadata("family_rels", set())
    self.event_role_names = self._get_metadata("event_roles", set())
    self.name_types = self._get_metadata("name_types", set())
    self.origin_types = self._get_metadata("origin_types", set())
    self.repository_types = self._get_metadata("repo_types", set())
    self.note_types = self._get_metadata("note_types", set())
    self.source_media_types = self._get_metadata("sm_types", set())
    self.url_types = self._get_metadata("url_types", set())
    self.media_attributes = self._get_metadata("mattr_names", set())
    self.event_attributes = self._get_metadata("eattr_names", set())
    self.place_types = self._get_metadata("place_types", set())

def get_surname_list(self):
    """
    Get surname list - MODE AWARE.
    In monolithic mode, returns surnames from this tree only.
    """
    if self.table_prefix:  # Monolithic mode
        table_name = f"{self.table_prefix}person"
        query = f"""
            SELECT DISTINCT json_data->'primary_name'->>'surname' as surname
            FROM {table_name} 
            WHERE json_data IS NOT NULL 
            AND json_data->'primary_name'->>'surname' IS NOT NULL
            ORDER BY surname
        """
    else:  # Separate mode
        query = """
            SELECT DISTINCT json_data->'primary_name'->>'surname' as surname
            FROM person 
            WHERE json_data IS NOT NULL
            AND json_data->'primary_name'->>'surname' IS NOT NULL
            ORDER BY surname
        """
    
    result = self.dbapi.execute(query)
    return [row[0] for row in result.fetchall()]

def _create_sequences_if_needed(self):
    """
    Optional: Create PostgreSQL sequences for ID generation.
    Better than counters for concurrent access.
    """
    if self.table_prefix:
        prefix = self.table_prefix.rstrip('_')
        sequences = [
            f"{prefix}_person_id_seq",
            f"{prefix}_family_id_seq",
            f"{prefix}_event_id_seq",
            f"{prefix}_place_id_seq",
            f"{prefix}_source_id_seq",
            f"{prefix}_citation_id_seq",
            f"{prefix}_media_id_seq",
            f"{prefix}_repository_id_seq",
            f"{prefix}_note_id_seq"
        ]
        for seq in sequences:
            self.dbapi.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq}")
```

## Testing Checklist for v1.4

### Monolithic Mode Tests
- [ ] ID counters unique per tree
- [ ] Surname lists isolated per tree
- [ ] Bookmarks per tree
- [ ] Custom types per tree
- [ ] Recent files tracking works

### Separate Mode Tests  
- [ ] ID counters work normally
- [ ] Surname list for single database
- [ ] All attributes initialized
- [ ] Recent files tracking works

### Gramps Web Tests
- [ ] Returns 93 records (not 0)
- [ ] Bookmarks functional
- [ ] Custom types in dropdowns
- [ ] Last accessed shows timestamp
- [ ] GEDCOM import works

## Summary

The key insight from your questions is that **monolithic mode requires tree-isolated metadata**. Items 4 and 5 (ID counters and surname lists) must be prefixed in monolithic mode to maintain tree separation. This is critical for data integrity when multiple trees share one database.

The "NEVER" issue is simply because we're not calling `recent_files()` to update Gramps' tracking system.