# COMPREHENSIVE HANDOVER - PostgreSQL Enhanced for Gramps
**Date**: 2025-08-06  
**Time**: 11:40 UTC  
**Status**: WORKING - All Views Functional, Verify Tool Fixed

## CRITICAL PROJECT INFORMATION

### Project Directory Structure
```
PRIMARY PROJECT ROOT: /home/greg/gramps-postgresql-enhanced/
├── postgresqlenhanced.py          # Main addon implementation
├── postgresqlenhanced.gpr.py      # Gramps plugin registration
├── connection.py                   # PostgreSQL connection management
├── schema.py                       # Database schema creation
├── migration.py                    # SQLite to PostgreSQL migration
├── queries.py                      # Query utilities
├── schema_columns.py               # Column definitions
├── test_*.py                       # Various test files
└── *.md                           # Documentation files
```

**CRITICAL**: DO NOT use `cd /home/greg/gramps-postgresql-enhanced/` from other directories!
Use relative paths or work within the directory.

### Gramps Plugin Installation Location
```
~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/
├── postgresqlenhanced.py          # Must be copied here after changes
├── postgresqlenhanced.gpr.py      # Plugin registration
├── connection_info.txt            # User configuration (monolithic mode)
└── [other supporting files]
```

### Configuration File
```
~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt
```
Current contents:
```
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = monolithic
shared_database_name = gramps_monolithic
```

### Gramps Data Directory
```
~/.local/share/gramps/grampsdb/
└── [tree_id]/                     # Each tree gets a directory
    ├── database.txt               # Contains "postgresqlenhanced"
    └── name.txt                   # Contains tree name
```

## DATABASE CONFIGURATION

### PostgreSQL Server Details
```
Host: 192.168.10.90 (NOT localhost!)
Port: 5432
Database: gramps_monolithic
User: genealogy_user
Password: GenealogyData2025
PostgreSQL Version: 17
```

### Monolithic Mode Architecture
- ALL family trees share ONE database (gramps_monolithic)
- Each tree gets table prefix: `tree_{tree_id}_`
- Example: `tree_689310ec_person`, `tree_689310ec_family`
- Central configuration in connection_info.txt

### Table Structure
Each tree has these tables:
- tree_{id}_person
- tree_{id}_family
- tree_{id}_event
- tree_{id}_place
- tree_{id}_source
- tree_{id}_citation
- tree_{id}_media
- tree_{id}_note
- tree_{id}_repository
- tree_{id}_tag
- tree_{id}_metadata
- tree_{id}_reference
- tree_{id}_gender_stats

## CORE PRINCIPLE: NO FALLBACK POLICY

**ABSOLUTE RULE**: Invalid data must be REJECTED with clear errors, never silently converted.

- **NEVER** modify data to make it "acceptable"
- **NEVER** silently convert types
- **ALWAYS** preserve data integrity exactly
- **ALWAYS** reject clearly invalid data
- This is irreplaceable family history data - NO COMPROMISES

## CRITICAL FIXES IMPLEMENTED (2025-08-06)

### 1. ✅ Verify Tool Compatibility
Added two methods to prevent crashes:
```python
def get_dbname(self)    # Returns display name
def get_save_path(self)  # Returns hashable string for verify tool
```

### 2. ✅ Table Prefix Wrapper
- TablePrefixWrapper intercepts ALL queries
- Adds `tree_{id}_` prefix to table names
- Wraps both connection.execute() and cursor operations

### 3. ✅ Collation Version Fix
- Fixed ALL 96 databases on server
- Updated from glibc 2.36 to 2.41
- No more collation warnings

### 4. ✅ Previous Critical Fixes (Still Active)
- NULL first name handling
- Nonexistent handle returns None
- GEDCOM import parameter handling
- Concurrent metadata updates (UPSERT)
- Order by person key NULL handling

## TESTING PROCEDURE (CRITICAL)

**Greg's Standard Testing Process:**
1. Start Gramps GUI
2. Delete any databases in family tree selection window
3. Go to Plugin Manager → Refresh (gets new plugin version)
4. Create new database with PostgreSQL Enhanced
5. Add person or import GEDCOM
6. Test all views

**IMPORTANT**: During GUI testing, NEVER manipulate database directly!

## CURRENT TEST RESULTS

### Working Features ✅
- Dashboard with Top Surnames
- People View (both regular and grouped)
- Families View (all 24 families display)
- Quick View (surname lists work)
- GEDCOM Import (50 people, 131 events imported successfully)
- Verify the Data tool (now works with get_save_path fix)

### Known UI Quirks
- "Grouped People" filter may show only 1 person
- Switch to regular "People" view to see all
- This is UI behavior, not a bug

## COMMON COMMANDS

### Check Database Activity
```bash
ssh 192.168.10.90 "sudo -u postgres psql -c \"SELECT pid, state, now() - xact_start as duration FROM pg_stat_activity WHERE usename = 'genealogy_user';\""
```

### Check Table Contents
```bash
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -c "SELECT COUNT(*) FROM tree_XXXXX_person;"
```

### Copy Plugin After Changes
```bash
cp /home/greg/gramps-postgresql-enhanced/postgresqlenhanced.py ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/
```

### Fix Collations (if needed after OS updates)
```bash
ssh 192.168.10.90 "sudo -u postgres psql -d gramps_monolithic -c 'ALTER COLLATION pg_catalog.\"en_US\" REFRESH VERSION;'"
```

## GIT REPOSITORY

Repository: https://github.com/glamberson/gramps-postgresql-enhanced.git
Branch: master

## FILES MODIFIED TODAY

1. postgresqlenhanced.py - Added get_dbname() and get_save_path() methods
2. fix_collations.sh - Script to fix all database collations
3. fix_all_collations.sql - SQL script for collation fixes
4. test_wrapper_diagnostic.py - Diagnostic for table prefix wrapper
5. COMPREHENSIVE_HANDOVER_20250806_FINAL.md - This document

## ENVIRONMENT DETAILS

- OS: Linux 6.12.38+deb13-amd64
- Python: 3.13.5
- Gramps: 6.0.1
- psycopg: 3.x
- PostgreSQL: 17 (on 192.168.10.90)
- glibc: 2.41 (was 2.36, updated)

## NEXT PRIORITIES

1. Test SQLite migration functionality
2. Document which Gramps tools are SQLite-specific
3. Performance testing with larger databases (>100k persons)
4. Cross-tree query capabilities in monolithic mode
5. Connection pooling for multi-user scenarios

## CRITICAL REMINDERS

1. **Project directory**: `/home/greg/gramps-postgresql-enhanced/` (cannot cd into from outside)
2. **Database is at 192.168.10.90**, NOT localhost
3. **Monolithic mode** with central config
4. **NO FALLBACK POLICY** - reject invalid data
5. **During GUI testing**: NO direct database manipulation
6. **After code changes**: Copy to `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/`
7. **Gramps logs**: Go to console where Gramps was started

## SUCCESS METRICS

- ✅ All views display data correctly
- ✅ GEDCOM import works
- ✅ Verify tool doesn't crash
- ✅ No PostgreSQL errors in logs
- ✅ No collation warnings
- ✅ Data integrity maintained 100%

Remember: This is irreplaceable family history data. Every edge case matters.