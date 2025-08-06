# CLAUDE.md - PostgreSQL Enhanced for Gramps

This file provides guidance to Claude Code (claude.ai/code) when working with the PostgreSQL Enhanced addon for Gramps.

## Project Overview

This is a high-performance PostgreSQL database backend addon for Gramps genealogy software. It provides advanced database capabilities while maintaining full compatibility with the Gramps data model. The addon has been rigorously tested with databases containing over 100,000 persons.

## Critical Context

### NO FALLBACK POLICY
**NEVER silently convert or fallback on data issues**
- If data doesn't match expected format → FAIL EXPLICITLY
- If type conversion needed → LOG ERROR AND STOP
- If database operation unclear → ABORT TRANSACTION
- This handles irreplaceable genealogical data - 100% accuracy required

### Date Verification (MANDATORY)
```bash
/home/greg/ai-tools/scripts/check_current_date.sh
```
**Required**: Run before ANY date operations to avoid January 2025 bias!

## Project Structure

```
gramps-postgresql-enhanced/
├── postgresqlenhanced.py      # Main addon file (MUST stay in root)
├── postgresqlenhanced.gpr.py  # Plugin registration (MUST stay in root)
├── connection.py              # Database connection handling
├── schema.py                  # Schema creation and management
├── migration.py               # Migration utilities
├── queries.py                 # Enhanced query functions
├── schema_columns.py          # Column definitions
├── debug_utils.py             # Debug utilities
├── __init__.py               # Package initialization
├── config/                   # Configuration files
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── tests/                    # Test files
├── archive/                  # Archived files
└── INDEX.md                  # Master navigation
```

## Development Context

### Database Configuration
- Host: 192.168.10.90
- User: genealogy_user
- Password: GenealogyData2025
- Database: gramps_monolithic (monolithic mode) or per-tree (separate mode)

### Two Database Modes (Both Working)
1. **Monolithic Mode**: All trees in one database with table prefixes (tree_<id>_*)
2. **Separate Mode**: Each tree gets its own database

### Configuration System
- Configuration via `connection_info.txt` file (GUI fields are ignored)
- Central config: `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt`

## Key Features

### Performance
- Tested with 100,000+ person databases
- 3-10x faster than SQLite
- Network capable with excellent performance
- True concurrent access without locking

### Technical Implementation
- Modern psycopg3 (NOT psycopg2)
- Dual storage: pickle blobs + JSONB
- Table prefix wrapper for monolithic mode
- Transaction safety with savepoints
- Data preservation when trees deleted (by design)

## Testing Commands

### Quick Database Check
```bash
export PGPASSWORD='GenealogyData2025'
psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -c "\dt tree_*"
```

### Run Tests
```bash
cd /home/greg/gramps-postgresql-enhanced
python3 scripts/run_tests.py
```

### Start Gramps with Debug
```bash
export GRAMPS_POSTGRESQL_DEBUG=1
gramps
```

## Important Notes

1. **Main addon files MUST stay in root directory** - Gramps requires them there
2. **Both database modes are fully tested and working**
3. **Data preservation is intentional** - Deleted trees remain in PostgreSQL
4. **No automatic migration between modes** - Export/import required
5. **GUI configuration fields don't work** - Use connection_info.txt file

## Common Tasks

### Register Existing Tree
```bash
./scripts/register_existing_tree.sh <tree_id> "<tree_name>"
```

### Switch Database Mode
1. Edit `connection_info.txt`
2. Change `database_mode = monolithic` or `database_mode = separate`
3. Create new tree and import data

### Clean Up Orphaned Tables (Monolithic)
```bash
TREE_ID="689304d4"
for table in person family event place source citation repository media note tag; do
    PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic \
        -c "DROP TABLE IF EXISTS tree_${TREE_ID}_${table} CASCADE;"
done
```

## Submission Status
- Status: Experimental, rigorous testing completed
- Both modes tested successfully
- Ready for final review before submission to Gramps project
- GitHub: https://github.com/glamberson/gramps-postgresql-enhanced