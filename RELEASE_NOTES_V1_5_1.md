# PostgreSQL Enhanced v1.5.1 Release Notes

## Release Date: 2025-08-11

## Overview
This patch release fixes a critical issue where converting SQLite databases with long strings would fail with truncation errors. The fix aligns our schema with SQLite's TEXT fields for full compatibility.

## Bug Fixes

### Fixed: VARCHAR(255) Truncation Error
- **Issue:** Converting SQLite databases would fail with `psycopg.errors.StringDataRightTruncation` when names, metadata, or other text exceeded 255 characters
- **Root Cause:** PostgreSQL Enhanced used VARCHAR(255) while SQLite uses TEXT (unlimited)
- **Solution:** Changed all VARCHAR(255) columns to TEXT to match SQLite behavior
- **Impact:** Now handles long international names, historical titles, and metadata without truncation

## Migration

### Automatic Migration
Existing PostgreSQL Enhanced databases are **automatically migrated** when opened with v1.5.1:
- The driver detects old VARCHAR(255) columns
- Automatically converts them to TEXT
- No data loss or manual intervention required

### Manual Migration (Optional)
For users who want to migrate databases before upgrading:
```bash
python3 migrate_varchar_to_text.py --database=your_database --user=your_user
```

### New Installations
New databases created with v1.5.1 use TEXT fields from the start - no migration needed.

## Technical Details

### Schema Changes
The following columns changed from VARCHAR(255) to TEXT:

| Table | Column | Old Type | New Type |
|-------|--------|----------|----------|
| metadata | setting | VARCHAR(255) | TEXT |
| gender_stats | given_name | VARCHAR(255) | TEXT |
| surname | surname | VARCHAR(255) | TEXT |
| name_group | name | VARCHAR(255) | TEXT |
| name_group | grouping | VARCHAR(255) | TEXT |
| reference | obj_class | VARCHAR(50) | TEXT |
| reference | ref_class | VARCHAR(50) | TEXT |
| All object tables | Various secondary columns | VARCHAR(255) | TEXT |

### Performance Impact
**None.** In PostgreSQL:
- TEXT and VARCHAR have identical storage mechanisms (TOAST)
- Same indexing capabilities
- Same query performance
- TEXT is actually PostgreSQL's preferred type for variable-length strings

### Compatibility
- **SQLite → PostgreSQL Enhanced:** Now 100% compatible, no truncation
- **PostgreSQL Enhanced → SQLite:** Fully compatible (SQLite uses TEXT)
- **Gramps:** No changes needed, fully transparent
- **GrampsWeb:** Fully compatible

## Testing Performed
- ✅ Migration of 100,000+ person database from SQLite
- ✅ Long international names (Asian, Arabic, European with titles)
- ✅ Historical names with full noble titles
- ✅ Metadata with long plugin configuration strings
- ✅ Automatic migration of existing PostgreSQL Enhanced databases
- ✅ Performance benchmarks show no regression

## Upgrading

### From v1.5.0 or earlier
1. Backup your database (recommended):
   ```bash
   pg_dump your_database > backup.sql
   ```
2. Install v1.5.1 in your Gramps addons folder
3. Open your database normally - migration happens automatically

### From SQLite
Convert as normal - the truncation issue is now fixed:
```
1. Open SQLite database in Gramps
2. Export to Gramps XML (.gramps)
3. Create new PostgreSQL Enhanced database
4. Import the XML file
```

## Credits
- **Bug Report & Testing:** Jean Michault (jmichault) - reported the VARCHAR(255) truncation issue and tested the fix
- **Solution:** Jean's suggested fix of changing to TEXT was adopted
- **Author:** Greg Lamberson (lamberson@yahoo.com)

## Support
- **Issues:** https://github.com/glamberson/gramps-postgresql-enhanced/issues
- **Documentation:** See README.md for full documentation

## What's Next
- v1.6.0: Full-text search implementation
- v1.7.0: Apache AGE graph database integration
- v2.0.0: AI/ML features with pgvector