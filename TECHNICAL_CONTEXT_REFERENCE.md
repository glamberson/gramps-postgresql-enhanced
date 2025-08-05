# Technical Context Reference - PostgreSQL Enhanced

## Database Connection Details
```python
# Production PostgreSQL Server
HOST = "192.168.10.90"
PORT = 5432
USER = "genealogy_user"
PASSWORD = "GenealogyData2025"

# Test Databases Used
MONOLITHIC_TEST_DB = "gramps_monolithic_test"
SEPARATE_TEST_DB_PREFIX = "gramps_tree_"
```

## Module Import Structure

### Correct Import Order (Critical!)
```python
# 1. First: Import real DBAPI before any mocking
from gramps.plugins.db.dbapi.dbapi import DBAPI

# 2. Then: Import our enhanced version
from postgresqlenhanced import PostgreSQLEnhanced

# 3. Finally: Import mock framework if needed
import mock_gramps
```

### Module Locations
- Gramps DBAPI: `/usr/lib/python3/dist-packages/gramps/plugins/db/dbapi/dbapi.py`
- Gramps objects: `/usr/lib/python3/dist-packages/gramps/gen/lib/`
- Our addon: `/home/greg/gramps-postgresql-enhanced/`

## Class Hierarchy

### Inheritance Chain
```
gramps.plugins.db.dbapi.dbapi.DBAPI
    ↓ inherits
PostgreSQLEnhanced (postgresqlenhanced.py)
    ↓ has attribute
TablePrefixWrapper (wraps dbapi in monolithic mode)
    ↓ wraps
PostgreSQLConnection (connection.py)
    ↓ uses
psycopg.Connection (PostgreSQL driver)
```

### Key Classes and Their Roles

#### PostgreSQLEnhanced
- Main plugin class
- Inherits from DBAPI
- Handles both monolithic and separate modes
- Creates TablePrefixWrapper when in monolithic mode

#### TablePrefixWrapper
- Wraps database connection in monolithic mode
- Modifies SQL queries to add table prefixes
- Transparent proxy for all other methods

#### PostgreSQLConnection
- Handles actual PostgreSQL connection
- Manages connection pooling
- Provides execute(), commit(), rollback()

#### PostgreSQLSchema
- Creates database schema
- Handles JSONB columns
- Manages indexes and constraints

## Transaction Flow

### How Transactions Should Work
```python
# 1. User code creates transaction context
with DbTxn("Description", db) as trans:
    # 2. DbTxn.__enter__ calls db.transaction_begin(trans)
    
    # 3. User adds/modifies data
    db.add_person(person, trans)
    # This should:
    # - Serialize person to JSON
    # - Execute INSERT SQL
    # - NOT commit yet
    
    # 4. DbTxn.__exit__ calls db.transaction_commit(trans)
    # This should:
    # - Call dbapi.commit()
    # - Data persists to database
```

### Current Problem in Transaction Flow
```python
# MockDBAPI overrides add_person with MagicMock
MockDBAPI.add_person = MagicMock()  # Does nothing!

# So when db.add_person() is called:
# - No SQL is executed
# - No data is inserted
# - commit() has nothing to commit
```

## Table Naming Convention

### Monolithic Mode Table Names
```python
# Tree name: "smith_family"
# Tables created:
smith_family_person
smith_family_family
smith_family_event
smith_family_place
smith_family_source
smith_family_citation
smith_family_repository
smith_family_media
smith_family_note
smith_family_tag
smith_family_metadata
smith_family_reference
smith_family_gender_stats

# Shared tables (no prefix):
surname
name_group
```

### Table Prefix Generation
```python
import re
# Tree name → table prefix
prefix = re.sub(r"[^a-zA-Z0-9_]", "_", tree_name) + "_"
# "smith_family" → "smith_family_"
# "jones-research" → "jones_research_"
```

## SQL Query Modification

### Original Query
```sql
SELECT * FROM person WHERE handle = %s
INSERT INTO family (handle, json_data) VALUES (%s, %s)
```

### Modified Query (Monolithic Mode)
```sql
SELECT * FROM smith_family_person WHERE handle = %s
INSERT INTO smith_family_family (handle, json_data) VALUES (%s, %s)
```

### Patterns Modified by TablePrefixWrapper
- `FROM table_name`
- `JOIN table_name`
- `INTO table_name`
- `UPDATE table_name`
- `DELETE FROM table_name`
- `CREATE TABLE table_name`
- `DROP TABLE table_name`
- `table_name.column_name`

## Test Data Structure

### Person Test Object
```python
TEST_PERSON_DATA = {
    "handle": "TEST001",
    "gramps_id": "I0001",
    "gender": 1,  # Male
    "primary_name": {
        "first_name": "John",
        "surname_list": [{"surname": "Smith", "prefix": "", "primary": True}],
    },
    "birth_ref_index": -1,
    "death_ref_index": -1,
    "event_ref_list": [],
    "family_list": [],
    "parent_family_list": [],
    "change": int(time.time()),
}
```

### Creating Test Person
```python
def create_test_person(handle, gramps_id, first_name, surname_text):
    person = Person()
    person.set_handle(handle)
    person.set_gramps_id(gramps_id)
    person.set_gender(Person.MALE)
    
    name = Name()
    name.set_first_name(first_name)
    surname = Surname()
    surname.set_surname(surname_text)
    name.add_surname(surname)
    person.set_primary_name(name)
    
    return person
```

## JSONB Storage Format

### How Objects Are Stored
```sql
-- Table structure
CREATE TABLE person (
    handle VARCHAR(50) PRIMARY KEY,
    json_data JSONB NOT NULL,
    -- Secondary columns for indexing
    gramps_id VARCHAR(50),
    given_name TEXT,
    surname TEXT
);

-- Example stored data
{
    "handle": "TEST001",
    "gramps_id": "I0001", 
    "gender": 1,
    "names": [{
        "first_name": "John",
        "surname": "Smith"
    }],
    "change": 1738239293
}
```

## Error Patterns to Watch For

### Silent Failures (NO FALLBACK!)
```python
# WRONG - Silences errors
try:
    db.add_person(person, trans)
except:
    pass  # NO! Never do this!

# RIGHT - Handle or raise
try:
    db.add_person(person, trans)
except Exception as e:
    print(f"Failed to add person: {e}")
    raise  # Re-raise to fail the test
```

### Transaction Not Committing
```python
# Symptom: Data not persisting
# Check:
1. Is transaction_commit being called?
2. Is dbapi.commit() being called?
3. Is the SQL INSERT actually executed?
4. Are we in autocommit mode accidentally?
```

### Table Prefix Issues
```python
# Symptom: "table does not exist" errors
# Check:
1. Is TablePrefixWrapper active?
2. Is the regex pattern matching correctly?
3. Are shared tables being prefixed incorrectly?
```

## Debug SQL Commands

### Connect to Test Database
```bash
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic_test
```

### Useful Queries
```sql
-- List all tables
\dt

-- Check specific tree's tables
\dt smith_family_*

-- Count records
SELECT COUNT(*) FROM smith_family_person;

-- View person data
SELECT handle, json_data->>'gramps_id', json_data->>'gender' 
FROM smith_family_person;

-- Check active transactions
SELECT * FROM pg_stat_activity WHERE datname = 'gramps_monolithic_test';

-- Kill stuck connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'gramps_monolithic_test' AND pid <> pg_backend_pid();
```

## File Sizes for Verification

After recovery, these files should have these sizes:
- mock_gramps.py: ~15,715 bytes (varies with fixes)
- test_monolithic_comprehensive.py: 28,476 bytes
- postgresqlenhanced.py: ~40,000 bytes
- connection.py: ~20,000 bytes
- schema.py: ~18,000 bytes

## Environment Variables

```bash
# Optional debug settings
export GRAMPS_POSTGRESQL_DEBUG=1
export GRAMPS_POSTGRESQL_SLOW_QUERY=0.1
export PYTHONPATH=/home/greg/gramps-postgresql-enhanced:$PYTHONPATH
```

## Test Execution Commands

### Full Test Suite
```bash
cd /home/greg/gramps-postgresql-enhanced
for test in test_*.py; do
    echo "Running $test..."
    python3 "$test"
    if [ $? -ne 0 ]; then
        echo "FAILED: $test"
        break
    fi
done
```

### Individual Tests
```bash
python3 test_monolithic_comprehensive.py
python3 test_database_modes.py
python3 test_data_validation.py
```

### With Debug Output
```bash
python3 -u test_transaction_trace.py 2>&1 | tee debug.log
```

---
*Reference document for technical details*
*Created: 2025-08-05*