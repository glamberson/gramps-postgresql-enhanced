# PostgreSQL Enhanced Addon - Comprehensive Session Handover Document

**PROJECT DIRECTORY: `/home/greg/gramps-postgresql-enhanced/`**
**DATE: 2025-08-05**
**CRITICAL: This project follows a strict NO FALLBACK policy**

## 🚨 CRITICAL CONTEXT - READ FIRST

### The NO FALLBACK Policy (MANDATORY)
This project operates under a **ZERO TOLERANCE** policy for workarounds:
1. **NEVER** accept partial solutions
2. **NEVER** silence errors or warnings
3. **NEVER** work around problems - FIX THEM PROPERLY
4. **NEVER** skip failing tests
5. **NEVER** commit code that doesn't work completely
6. If something doesn't work, find out WHY and fix the root cause
7. ALL tests must pass (20+ test files, not just 3)

### The Disaster and Recovery
- **Commit ec231d7** deleted 29,000+ lines of working code claiming it was "mocks"
- This broke monolithic mode completely
- Recovery executed by reverting to **commit d777c70** and cherry-picking **commit 3266153**
- The "mock" code was actually real test infrastructure, NOT fake code

## Project Overview

### What This Is
PostgreSQL Enhanced is an advanced database backend for Gramps genealogy software that provides:
- **Monolithic Mode**: Multiple family trees in one PostgreSQL database using table prefixes
- **Separate Mode**: Each family tree gets its own database (standard mode)
- **JSONB Storage**: Enhanced queries and performance with PostgreSQL JSON features
- **Connection Pooling**: Better resource management
- **Advanced Queries**: Relationship path finding, duplicate detection, common ancestors

### Current Working Directory Structure
```
/home/greg/gramps-postgresql-enhanced/
├── postgresqlenhanced.py    # Main plugin file (extends DBAPI)
├── connection.py             # PostgreSQL connection handling
├── schema.py                 # Schema creation and management
├── schema_columns.py         # Column definitions for tables
├── queries.py                # Advanced query implementations
├── migration.py              # Migration utilities
├── debug_utils.py            # Debug and profiling tools
├── mock_gramps.py            # Test framework (NOT MOCKS - REAL TEST CODE!)
├── test_monolithic_comprehensive.py  # Main test suite (28476 bytes)
└── [20+ other test files]
```

## Database Configuration

### PostgreSQL Server Details
```python
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
    # For monolithic mode tests:
    "shared_database": "gramps_monolithic_test",
    # For separate mode: each tree gets its own database
}
```

### Connection Configuration Files
For monolithic mode, create `connection_info.txt`:
```
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = monolithic
shared_database_name = gramps_monolithic_test
```

For separate mode:
```
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = separate
```

## Current State and Issues

### What Works
1. ✅ Database connection and schema creation
2. ✅ Table creation with prefixes in monolithic mode
3. ✅ Query modification via TablePrefixWrapper
4. ✅ Transaction methods are being called
5. ✅ Recovery from commit ec231d7 is complete

### Current Problem: Data Not Persisting in Tests
**Issue**: Data appears to be inserted but isn't persisting in the database

**Root Cause Analysis**:
1. MockDbTxn was not properly committing transactions ❌ FIXED
2. transaction_begin/commit methods weren't available ❌ FIXED
3. MockDBAPI overrides add_person with a MagicMock that does nothing ✅ CURRENT ISSUE

**Discovery Process**:
```python
# The transaction flow:
DbTxn.__enter__() -> db.transaction_begin(trans)
DbTxn.__exit__() -> db.transaction_commit(trans) -> dbapi.commit()

# The problem:
MockDBAPI.add_person = MagicMock()  # Does nothing!
# Real DBAPI.add_person would execute SQL INSERT
```

### Technical Discoveries

#### 1. Table Prefix System
In monolithic mode, tables are prefixed with tree name:
- Tree: "smith_family" → Tables: "smith_family_person", "smith_family_family", etc.
- Shared tables (no prefix): "surname", "name_group"

#### 2. TablePrefixWrapper
Automatically modifies SQL queries to add prefixes:
```python
# Original query:
"SELECT * FROM person WHERE handle = %s"
# Modified query:
"SELECT * FROM smith_family_person WHERE handle = %s"
```

#### 3. Mock System Architecture
**CRITICAL**: mock_gramps.py is NOT mocks - it's real test infrastructure!
- MockPerson, MockFamily, etc. are functional test objects
- MockDbTxn handles transaction context
- MockDBAPI was incorrectly overriding real database methods

#### 4. DBAPI Inheritance Chain
```
gramps.plugins.db.dbapi.dbapi.DBAPI (real Gramps class)
    ↓
PostgreSQLEnhanced (our enhanced version)
    ↓ (in tests)
[Problem: MockDBAPI replaces DBAPI before PostgreSQLEnhanced imports it]
```

## Test Files and Their Purpose

### Critical Test Files (Must All Pass)
1. **test_monolithic_comprehensive.py** - Complete monolithic mode testing
2. **test_database_modes.py** - Tests both separate and monolithic modes
3. **test_data_validation.py** - Data integrity tests
4. **test_transaction_handling.py** - Transaction commit/rollback
5. **test_connection_pooling.py** - Connection pool management
6. **test_jsonb_features.py** - JSONB storage and queries
7. **test_migration.py** - Schema migration tests
8. **test_queries.py** - Advanced query tests
9. **test_backup_restore.py** - Backup/restore functionality
10. **test_performance.py** - Performance benchmarks
11. **test_simple_monolithic.py** - Basic monolithic operations
12. **test_minimal_monolithic.py** - Minimal test case

### Debug Test Files Created During Investigation
- test_debug_transaction.py - Transaction flow debugging
- test_direct_commit.py - Direct commit testing
- test_transaction_trace.py - Transaction call tracing

## Fix Attempts and Results

### Attempt 1: Fix MockDbTxn Transaction Handling
**Change**: Made MockDbTxn call transaction_commit
**Result**: ❌ Methods not available on PostgreSQLEnhanced

### Attempt 2: Add Transaction Methods to MockDBAPI
**Change**: Added transaction_begin/commit/abort to MockDBAPI
**Result**: ✅ Methods now available, commit is called

### Attempt 3: Make MockDBAPI Inherit from Real DBAPI
**Change**: `class MockDBAPI(RealDBAPI)`
**Result**: ❌ Import order issues, PostgreSQLEnhanced loses methods

### Current Approach Needed
Either:
1. Don't mock DBAPI at all in tests (use real class)
2. Make MockDBAPI properly proxy to real methods
3. Implement actual SQL operations in MockDBAPI

## Git History and Commits

### Key Commits
- **d777c70**: Last known working state (revert target)
- **3266153**: SQL syntax fixes (must be preserved)
- **ec231d7**: The catastrophic deletion (29,000+ lines deleted)
- Current state: Reverted to d777c70 + cherry-picked 3266153

### Files Modified in Recovery
1. mock_gramps.py - Fixed MockDbTxn transaction handling
2. schema.py - SQL syntax fixes for CREATE INDEX statements

## Running Tests

### Basic Test Execution
```bash
cd /home/greg/gramps-postgresql-enhanced/
python3 test_monolithic_comprehensive.py
python3 test_database_modes.py
```

### With Debug Output
```bash
python3 test_transaction_trace.py  # Shows transaction calls
python3 test_debug_transaction.py  # Step-by-step debugging
```

### Expected Test Output (When Working)
```
======================================================================
PostgreSQL Enhanced - Monolithic Mode Comprehensive Test Suite
======================================================================
✓ Created shared database: gramps_monolithic_test
✓ Created 13 tables with prefix 'smith_family_'
✓ Added Person0 to smith_family
✓ Data isolation verified - no cross-contamination
✓ Concurrent access test passed
✓ All CRUD operations successful
Total tests: 5
Passed: 5
Failed: 0
```

### Current Test Output (Broken State)
```
✗ Data isolation test failed: smith_family has 0 people, expected 1
✗ Concurrent access test failed: smith_family has 0 people, expected 11
Total tests: 4
Passed: 2
Failed: 2
```

## Environment Details

### System Information
- Platform: Linux 6.12.38+deb13-amd64
- Python: Python 3.x
- PostgreSQL: On remote server 192.168.10.90
- Gramps: Version 6.x installed at /usr/lib/python3/dist-packages/gramps

### Python Path Requirements
```python
sys.path.insert(0, "/home/greg/gramps-postgresql-enhanced")
```

### Required Python Packages
- psycopg (PostgreSQL adapter)
- gramps (genealogy application)

## Next Steps for New Session

### Immediate Priority
Fix the data persistence issue by resolving the MockDBAPI problem:

1. **Option A**: Remove DBAPI mocking entirely
   - Let PostgreSQLEnhanced use real DBAPI
   - Only mock the Gramps objects (Person, Family, etc.)

2. **Option B**: Fix MockDBAPI to call real methods
   - Make add_person actually execute SQL
   - Ensure commit_person updates the database

3. **Option C**: Create minimal test without mocks
   - Direct test of PostgreSQLEnhanced functionality
   - Bypass the mock framework entirely

### Testing Protocol (NO FALLBACK)
1. Run ALL tests, not just one or two
2. If ANY test fails, fix it before proceeding
3. Never comment out failing tests
4. Never add try/except to hide errors
5. Verify data actually persists in PostgreSQL

### Success Criteria
- ALL 20+ test files pass completely
- Data persists correctly in monolithic mode
- No errors or warnings in any test
- Can create, read, update, delete all object types
- Multiple trees work independently in same database

## Configuration Files Reference

### connection_info.txt Format
```ini
# Required fields
host = hostname_or_ip
port = port_number
user = database_user
password = database_password
database_mode = monolithic|separate

# For monolithic mode only:
shared_database_name = database_name

# Optional
schema_version = 21
use_jsonb = true
```

### Directory Structure for Tests
```
temp_dir/
└── tree_name/
    └── connection_info.txt
```

## SQL Debugging Commands

### Check if data exists:
```sql
-- Connect to database
psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic_test

-- List all tables
\dt

-- Check person table (with prefix)
SELECT COUNT(*) FROM smith_family_person;
SELECT handle, json_data->>'gramps_id' FROM smith_family_person;

-- Check metadata
SELECT * FROM smith_family_metadata;
```

### Monitor transactions:
```sql
-- See active connections
SELECT pid, state, query FROM pg_stat_activity WHERE datname = 'gramps_monolithic_test';

-- Check for locks
SELECT * FROM pg_locks WHERE NOT granted;
```

## Critical Functions and Methods

### PostgreSQLEnhanced Key Methods
- `load(directory, callback)` - Initialize database
- `transaction_begin(transaction)` - Start transaction
- `transaction_commit(transaction)` - Commit transaction
- `add_person(person, trans)` - Add person to database

### TablePrefixWrapper
- `_add_table_prefixes(query)` - Modifies SQL to add prefixes
- `execute(query, params)` - Executes prefixed query
- `__getattr__(name)` - Proxies other methods to wrapped connection

### MockDbTxn (Fixed Version)
```python
class MockDbTxn(defaultdict):
    def __init__(self, msg, db, batch=False):
        defaultdict.__init__(self, list)
        self.msg = msg
        self.db = db
        if hasattr(db, 'transaction_begin'):
            db.transaction_begin(self)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if hasattr(self.db, 'transaction_commit'):
                self.db.transaction_commit(self)
```

## Final Notes

### Why This Matters
This addon enables:
- Professional genealogists to manage multiple client trees in one database
- Advanced queries not possible with blob storage
- Better performance through PostgreSQL optimizations
- Scalability for large family trees

### The Lesson from ec231d7
- NEVER delete code you don't understand
- "Mock" doesn't always mean fake
- 29,000 lines doesn't appear by accident
- Test everything before committing

### Remember the NO FALLBACK Policy
This is not optional. It's the core principle that ensures reliability.

---
*Document created: 2025-08-05*
*Recovery from ec231d7 executed successfully*
*Data persistence issue identified and solution paths documented*