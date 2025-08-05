# Monolithic Mode Testing Results
## Date: 2025-08-05

### Summary

I've made significant progress testing the monolithic database mode for the gramps-postgresql-enhanced plugin. This mode allows multiple family trees to share a single PostgreSQL database using table prefixes.

### Completed Tasks

1. **✅ Table Prefix Mechanism Test** - PASSED
   - Prefix generation working correctly
   - Query modification working for basic patterns
   - SQL injection prevention working
   - Concurrent operations conceptually validated

2. **✅ Schema Creation with Prefixes** - FIXED
   - Fixed schema.py to use table prefixes consistently
   - All tables now created with correct prefixes
   - Shared tables (name_group, surname) remain unprefixed

3. **✅ Metadata Override Methods** - IMPLEMENTED
   - Added _get_metadata and _set_metadata overrides
   - These methods now use prefixed table names in monolithic mode

4. **✅ Transaction Handling** - FIXED
   - Updated tests to use proper DbTxn objects
   - Fixed Person object creation in tests

5. **✅ Directory Structure** - FIXED
   - Tests now create proper directory structure
   - Tree name extracted correctly from path

### Partially Working

1. **⚠️ Comprehensive Test** - PARTIAL SUCCESS
   - Tree creation: ✅ WORKING
   - Data insertion: ✅ WORKING
   - Data retrieval: ❌ FAILING - Query prefix issue

2. **⚠️ TablePrefixWrapper** - NEEDS IMPROVEMENT
   - Basic query patterns working
   - Complex queries still failing
   - Need to handle more SQL patterns

### Known Issues

1. **Query Pattern Matching**
   - The pattern `SELECT handle, json_data FROM person` is not being caught
   - Need more comprehensive SQL parsing
   - Some queries from DBAPI parent class bypass our wrapper

2. **Transaction Errors**
   - "current transaction is aborted" error in concurrent test
   - Suggests error handling issue in one thread affects others

3. **Performance Test**
   - Uses direct SQL queries that need prefixing

### Technical Details

The main challenge is that Gramps' DBAPI class has many methods that execute SQL queries directly. Our approach of wrapping the connection to add prefixes works for most cases, but some queries are still slipping through.

The TablePrefixWrapper class intercepts execute() calls and modifies queries to add table prefixes. However, it needs more comprehensive pattern matching to catch all SQL variations.

### Recommendations

1. **Short-term Fix**: Enhance TablePrefixWrapper patterns to catch more query variations
2. **Long-term Solution**: Consider overriding more DBAPI methods to handle prefixes at a higher level
3. **Alternative**: Use PostgreSQL schemas instead of table prefixes (cleaner separation)

### NO FALLBACK Policy Compliance

✅ The plugin maintains strict NO FALLBACK compliance:
- Never falls back to SQLite
- All errors are explicit
- Database connection failures are properly reported

### Next Steps

1. Debug the specific query patterns that are failing
2. Test via Gramps UI with multiple trees
3. Verify complete data isolation
4. Test edge cases (special characters, concurrent access)
5. Create user documentation for monolithic mode configuration

### Files Modified

- `postgresqlenhanced.py` - Added metadata overrides and TablePrefixWrapper
- `schema.py` - Fixed table creation to use prefixes
- `test_table_prefix_mechanism.py` - Fixed test expectations
- `test_monolithic_comprehensive.py` - Fixed to use proper Gramps objects

### Configuration Example

For monolithic mode, create `connection_info.txt`:
```ini
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = monolithic
shared_database_name = gramps_shared
```

This will create tables like:
- `smith_family_person`
- `smith_family_family`
- `jones_research_person`
- etc.

While shared tables remain:
- `name_group`
- `surname`