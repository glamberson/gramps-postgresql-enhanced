# PostgreSQL Enhanced Plugin - Exhaustive Handover Document
## Date: 2025-08-05
## Critical: Database Addon Requirements - ZERO TOLERANCE FOR ERRORS

## 🚨 CRITICAL REQUIREMENTS - MUST BE ADDRESSED

### 1. Secondary Tables Issue
**MOST CONCERNING**: Tests expect these tables but they're not created:
- `child_ref`, `lds_ord`, `place_ref`, `media_ref`, `location`
- `event_ref`, `datamap`, `place_name`, `person_ref`, `reporef`
- `url`, `name`, `address`

**Why This Matters**: These tables are part of Gramps' internal data model. If they're missing, data integrity could be compromised.

**Action Required**: 
1. Investigate if these are created by parent DBAPI class
2. Ensure ALL tables required by Gramps are created
3. Validate against actual Gramps database schema

### 2. Testing Infrastructure Problems
**Current Issues**:
- MockDBAPI uses MagicMock - doesn't actually store/retrieve data
- High-level Gramps API tests fail because mocks don't work
- Can't validate actual data flow through Gramps API

**Required Solution**:
- Create REAL testing infrastructure that validates actual data storage
- Test with real Gramps DBAPI parent class
- Ensure 100% test coverage for a DATABASE addon

### 3. Data Validation Requirements
**STRICT REQUIREMENTS FOR DATABASE ADDON**:
- Every piece of data MUST be validated
- Both modes (separate/monolithic) MUST work identically
- Data integrity MUST be guaranteed
- NO data loss scenarios allowed
- Full ACID compliance required

## 📋 STRICT POLICIES TO MAINTAIN

### NO FALLBACK POLICY (ZERO TOLERANCE)
1. **NEVER** skip or work around issues
2. **NEVER** accept partial solutions
3. **NEVER** say "let's test this later"
4. **EVERY** problem must be completely solved
5. **EVERY** error must be fixed at its root cause
6. **NO** shortcuts, **NO** compromises

### Gramps Coding Standards (MUST MAINTAIN)
1. **Sphinx Docstrings**: All public methods documented
   ```python
   def method(self, param):
       """
       Brief description.
       
       :param param: Parameter description
       :type param: str
       :returns: Return description
       :rtype: dict
       """
   ```

2. **Pylint Compliance**: Score must stay above 8.0/10
   - Use `%` formatting for logging (NOT f-strings)
   - No bare except clauses
   - Line length < 100 characters
   - All imports at top of file

3. **Black Formatting**: All Python files formatted with Black

4. **Import Style**: Absolute imports (no relative imports with dots)

## 🗄️ Database Schema Requirements

### Tables That MUST Exist (Gramps Standard)
```sql
-- Primary object tables
person, family, event, place, source, citation, repository, media, note, tag

-- Secondary tables (MISSING IN TESTS - CRITICAL!)
child_ref, lds_ord, place_ref, media_ref, location, event_ref, 
datamap, place_name, person_ref, reporef, url, name, address

-- Shared tables (monolithic mode)
name_group, surname

-- Support tables
metadata, reference, gender_stats
```

### Data Types (PostgreSQL Specific)
- `handle`: TEXT PRIMARY KEY
- `json_data`: JSONB (stores Gramps object data)
- `gramps_id`: TEXT or VARCHAR
- `value` (in metadata): BYTEA (for pickled data)
- Timestamps: TIMESTAMPTZ

## 🔧 Technical Configuration

### Database Connection
```python
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",  # NO special characters!
}
```

### Test Databases Used
- Separate mode: `gramps_test_smith`, `gramps_test_jones`, `gramps_test_wilson`
- Monolithic mode: `gramps_monolithic_test`
- Validation: `gramps_validation_shared`

### Directory Structure
```
/home/greg/gramps-postgresql-enhanced/
├── postgresqlenhanced.py      # Main plugin file
├── connection.py               # Database connection handling
├── schema.py                   # Schema creation/management
├── migration.py                # Migration utilities
├── queries.py                  # Enhanced query methods
├── mock_gramps.py             # Mock objects (NEEDS FIXING!)
├── test_*.py                  # Various test files
└── requirements.txt           # psycopg[binary]>=3.1.0
```

## 📊 Current Test Status

### Passing Tests (6/9)
1. ✅ Database Modes Test
2. ✅ Table Prefix Mechanism
3. ✅ Database Contents Verification
4. ✅ Basic SQL Operations
5. ✅ SQL Comprehensive Tests
6. ✅ Data Validation Tests

### Failing Tests (3/9) - MUST BE FIXED
1. ❌ Separate Mode Comprehensive - MockDBAPI issue
2. ❌ Monolithic Comprehensive - MockDBAPI issue
3. ❌ PostgreSQL Enhanced Basic - Missing methods

## 🎯 Action Items for Next Session

### PRIORITY 1: Fix Secondary Tables Issue
1. Analyze Gramps source to understand ALL required tables
2. Update schema.py to create ALL tables
3. Validate against working Gramps SQLite database

### PRIORITY 2: Real Testing Infrastructure
1. Replace MockDBAPI with working implementation
2. Or find way to test with real Gramps DBAPI
3. Create integration tests that verify actual data flow

### PRIORITY 3: Complete Data Validation
1. Test EVERY data type Gramps uses
2. Verify ALL relationships maintained
3. Test edge cases (unicode, large data, etc.)
4. Performance testing under load

### PRIORITY 4: Monolithic Mode Verification
1. Ensure TablePrefixWrapper catches ALL queries
2. Test with complex Gramps operations
3. Verify no data leakage between trees

## 📚 Key Resources

### Documentation
- `/home/greg/gramps-postgresql-enhanced/COMPREHENSIVE_TEST_REPORT_2025_08_05.md`
- `/home/greg/gramps-postgresql-enhanced/GRAMPS_COMPLIANCE_WORK_SUMMARY_2025_08_05.md`
- `/home/greg/gramps-postgresql-enhanced/COMPREHENSIVE_HANDOVER_MONOLITHIC_TESTING_2025_08_05.md`

### Critical Code Sections
- `postgresqlenhanced.py:643-705` - TablePrefixWrapper implementation
- `schema.py` - Table creation (NEEDS secondary tables)
- `connection.py:373` - Fixed cursor handling
- `mock_gramps.py` - Needs complete rewrite

### Test Commands
```bash
# Setup
source .venv/bin/activate

# Run all tests
python run_all_tests.py

# SQL-level tests (these work)
python test_sql_comprehensive.py
python test_data_validation.py

# Problem tests (need fixing)
python test_separate_comprehensive.py
python test_monolithic_comprehensive.py
```

## ⚠️ CRITICAL REMINDERS

1. **This is a DATABASE addon** - reliability is NON-NEGOTIABLE
2. **Data integrity** trumps everything else
3. **Both modes** must work IDENTICALLY from user perspective
4. **NO FALLBACK** means NO SHORTCUTS
5. **100% test coverage** is REQUIRED for database code

## 🔐 Security Considerations
- SQL injection prevention in table prefix handling
- Password security (no special characters currently)
- Connection pooling security
- Data isolation in monolithic mode

## 🚀 Future Enhancements (After Core Fixed)
- PostgreSQL full-text search
- pgvector for AI/ML features
- PostGIS for geographic data
- Apache AGE for graph queries
- Recursive CTEs for relationship queries

## Final Statement

This PostgreSQL Enhanced addon is NOT ready for production use until:
1. ALL secondary tables are properly created
2. Testing validates ACTUAL data storage/retrieval
3. Both modes pass 100% of tests with REAL data
4. Data integrity is PROVEN, not assumed

The NO FALLBACK POLICY must be maintained. This is a database addon - there is ZERO tolerance for data loss or corruption.