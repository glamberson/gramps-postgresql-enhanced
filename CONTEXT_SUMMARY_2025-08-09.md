# PostgreSQL Enhanced v1.4 & Gramps Web Integration - Current Status
*Date: 2025-08-09*

## THE PROBLEM
PostgreSQL Enhanced v1.4 works PERFECTLY when called directly (returns 93 people), but Gramps Web API returns 500 Internal Server Error when trying to access the data through its endpoints.

## WHAT WE'VE FIXED IN v1.4
1. **Fixed filesystem shim path**: Changed from `/root/gramps/grampsdb/` to `/root/.gramps/grampsdb/` ✅
2. **Fixed tree ID extraction**: Now properly extracts tree ID from paths like `/root/.gramps/grampsdb/6894f36d` ✅
3. **Added all missing DBAPI attributes**: Including critical `db_is_open` flag ✅
4. **All 50+ initialization operations**: Bookmarks, ID counters, custom types, etc. ✅

## CURRENT STATUS
- **Database**: PostgreSQL at 192.168.10.90, database `gramps_monolithic_v13_test`, 93 people in tree_6894f36d_person table ✅
- **Direct Python test**: Works perfectly - `db.load()` returns 93 people ✅
- **Gramps Web API**: Returns 500 error on all endpoints ❌
- **Root cause**: Unknown - database opens fine, all attributes set, but API still fails

## DISCOVERED ISSUES
1. **Redis/Celery dependency**: Container expects Redis at 192.168.10.90:6379 but it's not running
2. **Multiple containers running**: 
   - `grampsweb-postgresql` on port 8519 (has v1.4 code)
   - `grampsweb-test` on port 8520 (still has v1.3 code)

## FILES MODIFIED TODAY
1. `/home/greg/gramps-postgresql-enhanced/postgresqlenhanced.py` - Added tree ID extraction fix
2. `/home/greg/greatgramps/filesystem_shim_manager.py` - Fixed path to use `/root/.gramps/grampsdb/`
3. `/home/greg/gramps-postgresql-enhanced/postgresqlenhanced.gpr.py` - Updated version to 1.4.0

## CRITICAL CONTEXT FROM YESTERDAY
- **Both `postgresql` and `sharedpostgresql` backends WORK with Gramps Web**
- This proves Gramps Web CAN work with PostgreSQL backends
- We need to understand what makes PostgreSQL Enhanced different

## IMMEDIATE NEXT STEPS
1. Start fresh container with v1.4 code properly installed
2. Disable or fix Redis/Celery configuration
3. Debug the actual 500 error - need to see the exception
4. Compare with working postgresql/sharedpostgresql backends if available

## TEST COMMANDS THAT WORK
```bash
# Direct database test (WORKS - returns 93 people)
docker exec grampsweb-postgresql python3 -c "
from gramps.plugins.db.postgresqlenhanced.postgresqlenhanced import PostgreSQLEnhanced
db = PostgreSQLEnhanced()
db.load('/root/.gramps/grampsdb/6894f36d')
print(f'People: {db.get_number_of_people()}')
"

# Get auth token (WORKS)
curl -s -X POST http://localhost:8519/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "greg", "password": "greg"}'

# API test (FAILS with 500)
curl -s -H "Authorization: Bearer TOKEN" \
  http://localhost:8519/api/trees/6894f36d/people
```

## KEY INSIGHT WE KEEP FORGETTING
The database and plugin work perfectly. The issue is specifically in how Gramps Web API is trying to use the backend, not with the backend itself. We've fixed all the known issues (shim path, tree ID extraction, missing attributes) but there's still something the API expects that we're not providing.

## FOR NEXT SESSION
Start here:
1. Read this file: `/home/greg/gramps-postgresql-enhanced/CONTEXT_SUMMARY_2025-08-09.md`
2. Check container has v1.4: `docker exec CONTAINER grep version= /usr/local/lib/python3.11/dist-packages/gramps/plugins/db/postgresqlenhanced/postgresqlenhanced.gpr.py`
3. Find the actual error causing 500: Need to see the exception in Gramps Web API
4. Fix Redis issue or disable Celery
5. Compare with working postgresql/sharedpostgresql backends