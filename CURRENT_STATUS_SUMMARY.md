# Current Status Summary - PostgreSQL Enhanced v1.5 + GrampsWeb

## The Problem
**Login loop**: User can authenticate (gets JWT token) but immediately gets kicked back to login screen.

## Root Cause (EMPIRICALLY DETERMINED)
1. Login succeeds → JWT token generated ✓
2. Web UI calls `/api/metadata/` endpoint
3. Metadata endpoint returns **500 Internal Server Error**
4. Web UI redirects back to login

## The Actual Error
```
psycopg.errors.SyntaxError: syntax error at or near "/"
LINE 2: CREATE TABLE IF NOT EXISTS tree_/root/gramps...
```

PostgreSQL Enhanced is trying to create a table with an invalid name because it's using the full filesystem path as the tree ID instead of extracting just the tree ID.

## Why This Happens - Path Confusion

### Two Different Paths Being Used
- **CORRECT**: `/root/.gramps/grampsdb/` (hidden directory with dot)
- **WRONG**: `/root/gramps/grampsdb/` (regular directory, no dot)

### The Chain of Failures
1. **WebDbManager** (GrampsWeb component) is hardcoded to use `/root/gramps/grampsdb/`
2. When we pass a tree path, it creates a **new UUID** instead of using our tree ID
3. PostgreSQL Enhanced tries to extract tree ID from path
4. Extraction fails for UUID paths like `/root/gramps/grampsdb/bf09d30f-fcb0-4849-b27d-592e3b538143`
5. Falls back to using full path as tree ID
6. Creates invalid SQL: `CREATE TABLE tree_/root/gramps/grampsdb/bf09d30f..._metadata`

## What We Fixed
1. ✅ Added public `get_metadata()` and `set_metadata()` methods
2. ✅ Added `get_transactions()` stub method
3. ✅ Fixed concurrent update retry logic
4. ✅ Fixed `database.txt` vs `database.backend` issue
5. ✅ Updated tree ID extraction to handle UUIDs (line 322 of postgresqlenhanced.py)
6. ✅ Removed wrong directory `/root/gramps/grampsdb`

## ✅ RESOLVED - August 9, 2025
**Login loop issue is FIXED!** All problems resolved with two key fixes:

### Final Fixes Applied
1. **Path Fix**: Created symlink `/root/gramps/grampsdb -> /root/.gramps/grampsdb` to redirect WebDbManager's wrong path
2. **Logger Fix**: Added `self.log = logging.getLogger(__name__)` in PostgreSQL Enhanced `__init__()` method

### Verification Results  
✅ Authentication works - JWT tokens generated  
✅ Metadata endpoint returns data (not 500 error)  
✅ Database accessible - 93 Henderson records, 29 families  
✅ Web UI login persists - No more redirect loops  

### Version Status
- **Container driver**: ef3577f7678b373f6bd1027f12b19604 (2484 lines)
- **Repo driver**: ef3577f7678b373f6bd1027f12b19604 (2484 lines)  
- **Status**: ✅ IDENTICAL - All changes preserved in repo version

## Files Involved
- `/usr/local/lib/python3.11/dist-packages/gramps/plugins/db/postgresqlenhanced/postgresqlenhanced.py` - Main driver
- `/usr/local/lib/python3.11/dist-packages/gramps_webapi/dbmanager.py` - WebDbManager with wrong path
- `/app/filesystem_shim_manager.py` - Creates filesystem shims in CORRECT path

## Current Database State
- Database: `gramps_monolithic_v13_test` on 192.168.10.90
- Trees: `6894f36d` (93 Henderson records), `6894f362` (empty)
- Tables use prefix: `tree_6894f36d_*`
- User: greg/greg with role=5, default tree=6894f36d

## Test Commands
```bash
# Test authentication
TOKEN=$(curl -s -X POST http://localhost:8520/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"greg","password":"greg"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Test metadata (currently fails with 500)
curl http://localhost:8520/api/metadata/ -H "Authorization: Bearer $TOKEN"
```

## ✅ COMPLETED  
Login loop issue resolved. GrampsWeb + PostgreSQL Enhanced v1.5 is now fully functional with persistent authentication and working metadata endpoints.