# PostgreSQL Enhanced v1.5 Deployment Status

## What We've Deployed

### Version: 1.5.0
- **Location**: `/usr/local/lib/python3.11/dist-packages/gramps/plugins/db/postgresqlenhanced/`
- **Container**: `grampsweb-test` (port 8520)
- **Database**: `gramps_monolithic_v13_test` on 192.168.10.90

### Changes Included in v1.5:
1. ✅ Fixed search syntax for psycopg3 (`WHERE x.name = ANY(%s)`)
2. ✅ Added public metadata methods (`set_metadata`, `get_metadata`)
3. ✅ Added `get_transactions()` stub method (returns empty list)
4. ✅ Added concurrent update retry logic
5. ✅ Added PostgreSQL-native undo implementation (`DbUndoPostgreSQL`)
6. ✅ Version bumped to 1.5.0

### Files Updated:
- `postgresqlenhanced.py` - Main driver with all fixes
- `postgresqlenhanced.gpr.py` - Version 1.5.0
- `connection.py` - Concurrent update handling
- `search_capabilities.py` - PostgreSQL syntax fixes
- `undo_postgresql.py` - NEW: PostgreSQL-native undo system

## Known Issues

### 1. Filesystem Shim Management
The filesystem shim manager is currently separate from the driver (`/app/filesystem_shim_manager.py` in container). It creates:
- `/root/.gramps/grampsdb/{tree_id}/database.txt` (contains "postgresqlenhanced")
- Connection info files
- Lock files
- Metadata placeholders

**Issue**: This should be better integrated or at least properly documented as a required component for GrampsWeb deployment.

### 2. Database Backend File
**Critical**: Must be `database.txt` NOT `database.backend`
- This is defined by `DBBACKEND` constant in `gramps.gen.db.dbconst`
- The filesystem shim was creating the wrong file initially

## Testing Instructions

### Web UI Test (http://localhost:8520)
1. Login: greg/greg
2. Check if you can:
   - See available trees
   - Select tree 6894f36d
   - View all 93 Henderson family members
   - Edit a person
   - Search for "Henderson"

### API Test
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8520/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"greg","password":"greg"}' | \
  python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# Check people count
curl -s "http://localhost:8520/api/people/?pagesize=1" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('Total people:', d.get('total_count', 0))"
```

### Gramps GUI Test
```bash
cd /home/greg/gramps-postgresql-enhanced
export POSTGRESQL_ENHANCED_MODE=monolithic
export GRAMPSWEB_POSTGRES_HOST=192.168.10.90
export GRAMPSWEB_POSTGRES_DB=gramps_monolithic_v13_test
export GRAMPSWEB_POSTGRES_USER=genealogy_user
export GRAMPSWEB_POSTGRES_PASSWORD=GenealogyData2025
gramps
```

## Current Status

### ✅ Completed:
- Cleaned up old copies
- Deployed v1.5 to container
- Fixed database.txt issue
- Created comprehensive test plan

### ⚠️ In Progress:
- Testing with GrampsWeb UI
- Verifying all functionality works

### 📝 TODO:
- Test with Gramps GUI
- Verify transaction history doesn't error
- Test concurrent updates
- Import/export testing

## Important Notes

1. **The filesystem shim manager is a workaround** - GrampsWeb expects filesystem-based trees, but PostgreSQL Enhanced stores everything in the database. The shim creates minimal filesystem structures to satisfy GrampsWeb's expectations.

2. **Transaction history is stubbed** - The `get_transactions()` method returns an empty list. Full implementation would require significant work to track all database changes.

3. **PostgreSQL native search has issues** - Currently falls back to SQLite/sifts for search functionality.

4. **Monolithic mode is working** - Multiple trees in a single database with table prefixes (e.g., `tree_6894f36d_person`).

## Next Steps

1. **Immediate**: Test that the web UI actually works with the 93 Henderson records
2. **Important**: Test Gramps GUI with the same database
3. **Future**: Consider properly integrating or documenting the filesystem shim requirement
4. **Future**: Implement full transaction history if needed