# Continue PostgreSQL Enhanced Monolithic Mode Testing

I need to complete the rigorous testing of monolithic database mode for the gramps-postgresql-enhanced plugin. This mode allows multiple family trees to share a single PostgreSQL database using table prefixes.

**CRITICAL**: This plugin implements a NO FALLBACK POLICY. All errors must be explicit. The plugin must NEVER fall back to SQLite.

## Current Status

The monolithic mode is MOSTLY WORKING:
- ✅ Tables are created with correct prefixes (smith_family_person, jones_research_event, etc.)
- ✅ Data can be inserted successfully
- ✅ Basic SQL queries are being prefixed correctly
- ❌ Some SELECT queries from Gramps' DBAPI aren't being caught by our TablePrefixWrapper

## Immediate Task

Fix the TablePrefixWrapper in postgresqlenhanced.py to catch ALL query patterns, specifically:
- `SELECT handle, json_data FROM person` (currently failing)
- Other SELECT patterns without keywords before FROM

## Resources

Please review the comprehensive handover document at:
`/home/greg/gramps-postgresql-enhanced/COMPREHENSIVE_HANDOVER_MONOLITHIC_TESTING_2025_08_05.md`

This contains:
- Complete status of what's working and what's not
- Technical details of the implementation
- Test results and error messages
- Database connection details
- Quick commands to run tests

## Key Files to Focus On

1. `/home/greg/gramps-postgresql-enhanced/postgresqlenhanced.py` - Contains TablePrefixWrapper class (lines 643-705)
2. `/home/greg/gramps-postgresql-enhanced/test_monolithic_comprehensive.py` - Main test that's partially failing
3. `/home/greg/gramps-postgresql-enhanced/schema.py` - Already fixed for prefixes

## Success Criteria

1. ALL tests in test_monolithic_comprehensive.py must pass
2. Complete data isolation between trees sharing a database
3. NO FALLBACK to SQLite ever occurs
4. Performance is acceptable (within 10% of separate mode)

The core functionality is working. We just need to enhance the SQL query pattern matching to catch all variations from the parent DBAPI class.