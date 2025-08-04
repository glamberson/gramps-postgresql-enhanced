# PostgreSQL Enhanced Testing Guide

## Overview

Comprehensive test suite for the PostgreSQL Enhanced Gramps addon with full logging and debugging capabilities.

## Test Coverage

### Core CRUD Operations
- **Person CRUD**: Create, read, update, delete persons with names, attributes, URLs
- **Family CRUD**: Family creation with parents and children
- **Event CRUD**: Events with dates and descriptions
- **Place CRUD**: Places with titles and codes
- **Source/Citation CRUD**: Sources and citations with relationships
- **Repository CRUD**: Repository objects
- **Media CRUD**: Media objects with paths and MIME types
- **Note CRUD**: Notes with formatted text
- **Tag CRUD**: Tags with colors and priorities

### Data Integrity Tests
- **Secondary Columns**: Verifies population of surname, given_name, etc.
- **All Table Columns**: Checks all required columns exist
- **Relationship Integrity**: Parent-child, family relationships
- **Reference Integrity**: Event references, citations to sources

### Functionality Tests
- **Search Operations**: Tests search by surname, name
- **Filter Operations**: Gender filtering, custom filters
- **Bulk Operations**: Performance testing with 100+ records
- **Concurrent Access**: Multiple database connections

### Edge Cases & Error Handling
- **Empty Names**: Persons with no name data
- **Long Names**: 200+ character names
- **Special Characters**: UTF-8, apostrophes, hyphens
- **Duplicate IDs**: Same gramps_id handling
- **Transaction Rollback**: Error recovery

## Running Tests

### Full Test Suite
```bash
# Basic run
python3 run_tests.py

# With debug logging
python3 run_tests.py --debug

# Keep test database after run
python3 run_tests.py --keep-db
```

### Specific Tests
```bash
# Run only person CRUD tests
python3 run_tests.py --test person_crud

# Available test names:
# person_crud, family_crud, event_crud, place_crud
# source_citation_crud, repository_crud, media_crud
# note_crud, tag_crud, secondary_columns_person
# secondary_columns_all, search, filter, relationships
# references, bulk, concurrent, edge_cases, error_handling
```

### SQL Verification
```bash
# Check database state without running tests
python3 run_tests.py --sql-verify
```

## Logging

### Log Locations
- **Console**: Basic pass/fail information
- **File Logs**: `test_logs/test_run_YYYYMMDD_HHMMSS.log`
- **Debug Log**: `~/.gramps/postgresql_enhanced_debug.log` (when GRAMPS_POSTGRESQL_DEBUG=1)

### Enable Debug Logging
```bash
# For tests
python3 run_tests.py --debug

# For plugin itself
export GRAMPS_POSTGRESQL_DEBUG=1
gramps
```

### Log Levels
- **DEBUG**: All SQL queries, method calls, data transformations
- **INFO**: Test progress, major operations
- **WARNING**: Non-critical issues, deprecations
- **ERROR**: Test failures, exceptions

## Test Database Management

Test databases are created with pattern `test_gramps_TIMESTAMP`.

### Manual Cleanup
```bash
# List test databases
export PGPASSWORD="GenealogyData2025"
psql -h 192.168.10.90 -U genealogy_user -d postgres -c "\l" | grep test_gramps

# Drop specific test database
psql -h 192.168.10.90 -U genealogy_user -d postgres -c "DROP DATABASE test_gramps_12345;"
```

## Debugging Failed Tests

### Check Specific Failures
1. Look at the test log file for full stack traces
2. Run the specific test with debug flag
3. Check the PostgreSQL logs on the server

### Common Issues
- **Connection Failed**: Check PostgreSQL server is accessible
- **Permission Denied**: Ensure user has CREATEDB privilege
- **Column Missing**: Schema may be out of sync, check schema.py
- **JSON Path Error**: Check schema_columns.py paths match actual structure

### Direct Database Inspection
```bash
# Connect to test database
export PGPASSWORD="GenealogyData2025"
psql -h 192.168.10.90 -U genealogy_user -d test_gramps_XXXXX

# Useful queries
\dt                          -- List all tables
\d person                    -- Show person table structure
SELECT * FROM person LIMIT 5; -- View person data
SELECT jsonb_pretty(json_data) FROM person LIMIT 1; -- Pretty JSON

# Check secondary columns
SELECT handle, gramps_id, given_name, surname FROM person;
```

## Performance Benchmarks

The bulk test creates 100 persons and reports:
- Insert rate (persons/second)
- Total time for bulk operation
- Database size growth

Typical results:
- Insert rate: 50-100 persons/second
- 100 persons: 1-2 seconds
- Database overhead: ~10KB per person

## Continuous Integration

For CI/CD pipelines:
```bash
# Run tests and exit with proper code
python3 run_tests.py
# Exit codes:
# 0 = All tests passed
# 1 = Some tests failed  
# 2 = Interrupted
# 3 = Unexpected error

# Generate JUnit XML (future enhancement)
# python3 run_tests.py --junit report.xml
```

## Adding New Tests

1. Add test method to `PostgreSQLEnhancedTester` class
2. Follow naming convention: `test_feature_name()`
3. Use try/except with `self.results.add_pass/fail()`
4. Add to test_methods dict in run_tests.py
5. Document expected behavior

Example:
```python
def test_new_feature(self):
    """Test new feature description"""
    test_name = "New feature"
    try:
        # Test implementation
        assert something == expected
        self.results.add_pass(test_name)
    except Exception as e:
        self.results.add_fail(test_name, str(e))
```

## Test Data

Tests create various test objects:
- Persons: William Shakespeare, John Smith, Jane Doe, etc.
- Families: Smith family with parents and children
- Events: Birth events with dates
- Places: Test City (TC)

All test data is cleaned up after tests complete (unless --keep-db is used).