# PostgreSQL Enhanced v1.4.0 Release Notes
*Development Version - Not Yet Released*

## Overview

Version 1.4.0 addresses **Gramps Web compatibility issues** discovered during integration testing. This release adds missing DBAPI attributes that Gramps Web expects, with special attention to mode-aware metadata handling for monolithic deployments.

## Key Features

### 🎯 Gramps Web Compatibility

- **Fixes "0 records" issue** - Sets `db_is_open` flag that Gramps Web requires
- **Full DBAPI compliance** - All expected attributes now initialized
- **Recent files tracking** - "Last Accessed" now shows proper timestamps
- **UI integration** - Custom types populate dropdowns correctly

### 🔄 Mode-Aware Metadata

- **Monolithic mode support** - Proper tree isolation with prefixed metadata
- **ID counter isolation** - Each tree maintains its own ID counters
- **Surname list isolation** - Trees don't leak surname data between each other
- **Bookmark isolation** - Bookmarks are tree-specific in monolithic mode

### 📊 Complete Attribute Support

- ✅ All 9 bookmark collections initialized
- ✅ All 17 custom type attributes loaded
- ✅ All 9 ID counters properly managed
- ✅ Gender statistics available
- ✅ Name formats and researcher info loaded
- ✅ Read-only mode support

## Technical Details

### New Methods

- `_initialize_bookmarks()` - Loads all bookmark collections
- `_initialize_custom_types()` - Loads custom type attributes for UI
- `_initialize_id_counters()` - Mode-aware ID counter initialization
- `_get_mode_aware_surname_list()` - Isolated surname lists per tree
- `_update_recent_files()` - PostgreSQL path registration

### Virtual PostgreSQL Paths

Instead of filesystem paths, v1.4 uses meaningful PostgreSQL identifiers:
- **Monolithic**: `postgresql://monolithic/tree_id`
- **Separate**: `postgresql://separate/database_name`

## Breaking Changes

None. Version 1.4 is fully backward compatible with v1.3.

## Migration from v1.3

Simply update the plugin files. No database changes required.

```bash
# Update to v1.4
git checkout v1.4-grampsweb-compatibility
```

## Configuration

No new configuration required. Existing v1.3 configurations work unchanged.

## Testing

Tested with:
- Gramps Desktop 6.0.1
- Gramps Web 2.5.0
- PostgreSQL 15 and 17
- Monolithic mode with 400+ trees
- Separate mode with individual databases

## Known Issues

- Search capabilities module temporarily disabled (will be re-enabled in v1.4.1)
- Some reports may need additional testing with mode-aware metadata

## What's Next (v1.5)

- PostgreSQL sequence support for ID generation
- Materialized views for surname lists
- Enhanced caching for better performance
- Full search capabilities restoration

## Contributors

- Greg Lamberson - Lead developer
- Thanks to the Gramps Web team for compatibility testing

## Support

For issues or questions:
- GitHub: https://github.com/gramps-postgresql-enhanced
- Email: greg@aigenealogyinsights.com

---

## Detailed Changelog

### Added
- `db_is_open` flag for Gramps Web compatibility
- Read-only mode support (`DBMODE_R`)
- All 9 bookmark collection initializations
- All 17 custom type attribute loads
- Mode-aware ID counter management
- Mode-aware surname list queries
- Virtual PostgreSQL path generation
- Recent files timestamp tracking
- Comprehensive Sphinx docstrings

### Changed
- `load()` method now includes all DBAPI attributes
- Version updated from 1.3.0 to 1.4.0
- Improved error handling in metadata operations

### Fixed
- "Last Accessed: NEVER" display issue
- Gramps Web returning 0 records
- ID collision risk in monolithic mode
- Surname list data leakage between trees
- Custom type dropdowns not populating

### Technical
- No database schema changes
- No migration required
- Backward compatible with v1.3
- Forward compatible with planned v1.5 features