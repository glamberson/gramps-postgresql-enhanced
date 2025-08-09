# Login Loop Fix Documentation - EMPIRICAL DATA

## Problem: Login works but immediately returns to login screen

### Root Cause Chain (EMPIRICALLY DETERMINED)

1. **Authentication succeeds** - Token is generated correctly
2. **Metadata endpoint fails with 500 error** - This causes the UI to redirect to login
3. **Actual error**: `syntax error at or near "/" LINE 2: CREATE TABLE IF NOT EXISTS tree_/root/gramps...`

### Why This Happens

#### Path Confusion Issue
**CRITICAL**: There are TWO paths being used:
- **CORRECT**: `/root/.gramps/grampsdb/` (with dot - hidden directory)
- **WRONG**: `/root/gramps/grampsdb/` (no dot - regular directory)

GrampsWeb or some component creates trees in the WRONG path, which then causes failures.

#### Tree ID Extraction Failure
The PostgreSQL Enhanced driver tries to extract tree IDs from filesystem paths:
- Works for: `/root/.gramps/grampsdb/6894f36d` → extracts `6894f36d`
- FAILS for: `/root/gramps/grampsdb/f0f38366-d362-48fa-81b3-b4a2c35c4dad` → uses full path!

The failure happens because:
1. UUID-style tree IDs have dashes: `f0f38366-d362-48fa-81b3-b4a2c35c4dad`
2. The extraction logic at line 322 checks: `(len(last_part) == 8 or '-' not in last_part)`
3. UUIDs have dashes, so this condition fails
4. When extraction fails, it uses the FULL PATH as the tree ID
5. This creates invalid SQL: `CREATE TABLE tree_/root/gramps/grampsdb/f0f38366-d362-48fa-81b3-b4a2c35c4dad_metadata`

### Previous Fixes Applied

#### 1. Database Backend File Name
- **Issue**: GrampsWeb expects `database.txt` NOT `database.backend`
- **Fix**: Filesystem shim manager creates `database.txt`
- **Location**: `/app/filesystem_shim_manager.py` line 88

#### 2. Tree Table 'enabled' Column Type
- **Issue**: Column was INTEGER but GrampsWeb expects BOOLEAN
- **Status**: Currently still INTEGER (value 1), may need conversion

#### 3. Public Metadata Methods
- **Issue**: GrampsWeb calls `set_metadata()` and `get_metadata()` directly
- **Fix**: Added public wrapper methods in PostgreSQL Enhanced v1.5
- **Location**: `postgresqlenhanced.py` lines 1969-2000

#### 4. Transaction History Method
- **Issue**: GrampsWeb expects `get_transactions()` method
- **Fix**: Added stub method returning empty list
- **Location**: `postgresqlenhanced.py` lines 2000-2015

### Files and Locations

#### Container Paths
- PostgreSQL Enhanced: `/usr/local/lib/python3.11/dist-packages/gramps/plugins/db/postgresqlenhanced/`
- GrampsWeb API: `/usr/local/lib/python3.11/dist-packages/gramps_webapi/`
- Filesystem Shim: `/app/filesystem_shim_manager.py`
- Tree directories: `/root/.gramps/grampsdb/{tree_id}/` (CORRECT PATH)

#### Critical Files in Each Tree Directory
1. `database.txt` - Contains "postgresqlenhanced" (NOT database.backend!)
2. `name.txt` - Human-readable tree name
3. `meta_data.db` - Empty file (just needs to exist)
4. `lock` - Empty lock file
5. `connection_info.txt` - PostgreSQL connection details

### Environment Variables (CORRECT)
```bash
GRAMPSHOME=/root
GRAMPS_DATABASE_PATH=/root/.gramps/grampsdb
GRAMPSWEB_TREE=6894f36d
POSTGRESQL_ENHANCED_MODE=monolithic
```

### Database Tables (CORRECT)
In `gramps_monolithic_v13_test`:
- `trees` table - Tree registry (id, enabled)
- `users` table - User auth (name='greg', tree='6894f36d')
- `tree_6894f36d_*` tables - Actual data (93 Henderson records)
- `tree_6894f362_*` tables - Empty test tree

### Immediate Fixes Needed

1. **Remove wrong path trees**:
```bash
docker exec grampsweb-test rm -rf /root/gramps/grampsdb
```

2. **Fix tree ID extraction** in `postgresqlenhanced.py` line 322:
```python
# OLD (fails for UUIDs):
if last_part and (len(last_part) == 8 or '-' not in last_part):

# NEW (handles any tree ID):
if last_part and len(last_part) <= 40:  # Reasonable limit for tree IDs
```

3. **Prevent wrong path creation**:
- Find where `/root/gramps/grampsdb` is being created
- Ensure all code uses `/root/.gramps/grampsdb`

### Testing After Fixes

1. **Check authentication**:
```bash
curl -X POST http://localhost:8520/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"greg","password":"greg"}'
# Should return access token
```

2. **Check metadata endpoint**:
```bash
TOKEN=$(curl -s -X POST http://localhost:8520/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"greg","password":"greg"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl http://localhost:8520/api/metadata/ \
  -H "Authorization: Bearer $TOKEN"
# Should return metadata, NOT 500 error
```

3. **Check web UI**:
- Navigate to http://localhost:8520
- Login with greg/greg
- Should stay logged in and show trees

### Known Working State
When everything is correct:
- Trees are in `/root/.gramps/grampsdb/`
- Tree IDs are properly extracted (just the ID, not full path)
- Table prefixes are `tree_{tree_id}_` (e.g., `tree_6894f36d_`)
- Authentication returns token
- Metadata endpoint returns data
- Web UI stays logged in

### What Creates Wrong Paths - RESOLVED
**ROOT CAUSE FOUND**: WebDbManager in GrampsWeb uses `config.get("database.path")` which returns `/root/gramps/grampsdb` instead of `/root/.gramps/grampsdb`.

**FINAL FIXES APPLIED - August 9, 2025**:

#### 1. Path Fix - Symlink Workaround
- **Issue**: WebDbManager hardcoded to wrong path `/root/gramps/grampsdb`
- **Root cause**: `config.get("database.path")` returns wrong path
- **Fix**: Created symlink: `/root/gramps/grampsdb -> /root/.gramps/grampsdb`
- **Location**: `gramps_webapi/dbmanager.py` line 69: `config.get("database.path")`

#### 2. Missing Logger Fix  
- **Issue**: `AttributeError: 'PostgreSQLEnhanced' object has no attribute 'log'`
- **Root cause**: Driver tries to use `self.log` but it was never initialized
- **Fix**: Added `self.log = logging.getLogger(__name__)` in `__init__()` method
- **Location**: `postgresqlenhanced.py` line 149 (after super().__init__())

### FINAL WORKING STATE - VERIFIED AUGUST 9, 2025
✅ **Login loop FIXED** - Users stay logged in after authentication
✅ **Metadata endpoint working** - Returns full database metadata
✅ **Database connection stable** - 93 Henderson records accessible
✅ **PostgreSQL Enhanced v1.5 fully functional** with GrampsWeb

**Test Results**:
- Authentication: ✅ Returns JWT tokens
- Metadata endpoint: ✅ Returns database info (not 500 error)
- Object counts: 93 people, 29 families, 258 citations (Henderson data)
- Database: `postgresql:tree_6894f36d` on 192.168.10.90