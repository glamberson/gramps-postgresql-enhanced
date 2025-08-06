# PostgreSQL Enhanced Architecture Learnings
## Date: 2025-08-04

### 🏗️ Core Architecture Discoveries

#### 1. DBAPI Evolution and Serializer Requirements
**Critical Discovery**: DBAPI has evolved to expect `JSONSerializer` instead of `BlobSerializer`
- **Issue**: `AttributeError: 'BlobSerializer' object has no attribute 'object_to_data'`
- **Root Cause**: DBAPI calls `serializer.object_to_data()` which only exists in JSONSerializer
- **Implications**:
  - Data is stored as JSON strings in `json_data` column
  - Metadata uses `json_data` column (not `value`)
  - All objects are serialized to JSON format, not pickled bytes

#### 2. Secondary Columns Architecture
**The Dilemma**: Gramps expects physical columns for queries vs. PostgreSQL JSONB capabilities

**Attempted Approaches**:
1. **GENERATED Columns** (Failed)
   - PostgreSQL GENERATED columns cannot be UPDATE'd
   - Gramps' `_update_secondary_values()` tries to UPDATE them
   - Error: "column can only be updated to DEFAULT"

2. **No Columns + Override** (Failed)
   - Override `_update_secondary_values()` to do nothing
   - Store only in JSONB
   - Error: Gramps queries expect columns to exist (e.g., "column 'surname' does not exist")

3. **Hybrid Approach** (Current)
   - Physical columns exist for Gramps queries
   - Triggers sync from JSONB on INSERT/UPDATE
   - Override `_update_secondary_values()` to prevent duplicate updates
   - Data source of truth remains JSONB

**Key Learning**: DBAPI bakes SQLite assumptions into the abstraction layer
- `_sql_cast_list()` converts booleans to integers
- Secondary columns are assumed to be directly updatable
- The abstraction is at the wrong level

#### 3. Transaction System Architecture
**Critical Discovery**: Transactions require proper undo manager initialization

**The Chain**:
1. `DbTxn.__init__` expects `grampsdb.get_undodb()`
2. `get_undodb()` returns `self.undodb`
3. `undodb` must be created via `_create_undo_manager()`
4. This happens in DbGeneric's `load()` method

**Issue**: Calling parent's `load()` triggers upgrade mechanisms
- Looks for non-existent zip files
- Enters infinite upgrade loop
- Solution: Initialize undo manager directly

#### 4. Schema Version Management
**Discovery**: Gramps expects schema version 21
- Stored as metadata key "version" (not "schema_version")
- Retrieved via `_get_metadata("version")`
- Must match `DbGeneric.VERSION[0]` which is 21

#### 5. Type Conversion Issues
**PostgreSQL vs SQLite Type Mismatches**:
- SQLite: Boolean stored as INTEGER (0/1)
- PostgreSQL: Has native BOOLEAN type
- DBAPI converts: `bool` → `int` for SQLite compatibility
- Required custom conversion in connection layer

### 🔑 Key Architectural Insights

#### 1. Inheritance Hierarchy
```
DbGeneric (gramps.gen.db.generic)
    ↓
DBAPI (gramps.plugins.db.dbapi.dbapi)
    ↓
PostgreSQLEnhanced (our plugin)
```

#### 2. Critical Methods to Understand
- `load()`: Initializes database, undo manager, metadata
- `_commit_base()`: Core method for saving objects
- `_update_secondary_values()`: Updates derived columns
- `transaction_begin()`: Sets up transaction (but not commitdb)
- `get_undodb()`: Returns undo database for transactions

#### 3. Storage Architecture
With JSONSerializer:
- Primary data: `json_data` column (JSONB)
- Secondary columns: Physical columns for queries
- Triggers: Sync secondary columns from JSONB
- Indexes: Both on columns and JSONB paths

### 🚨 Critical Gotchas

1. **Serializer Selection**: Must use JSONSerializer for modern DBAPI
2. **Column Names**: json_data not json_value, metadata uses json_data
3. **Transaction Setup**: Must initialize undodb or transactions fail
4. **Schema Version**: Must be 21 to avoid upgrade prompts
5. **Type Conversions**: Must handle SQLite→PostgreSQL type differences
6. **Parent Methods**: Some must be called, others must be avoided

### 📋 Current Implementation Status

**Working**:
- Plugin loads in Gramps ✅
- Database connection established ✅
- Schema creation with all tables ✅
- JSONSerializer integration ✅
- Secondary columns with triggers ✅
- Transaction system initialized ✅

**Pending Verification**:
- Person creation and editing
- GEDCOM import
- Query performance
- Concurrent access
- Migration from SQLite

### 🔮 Future Considerations

1. **Better Abstraction Layer**
   - Move type conversions to backend
   - Make secondary columns optional
   - Support for JSONB-native queries

2. **Performance Optimization**
   - Prepared statements
   - Connection pooling
   - Query result caching

3. **Configuration Management**
   - External config file for credentials
   - Environment variable support
   - UI for connection parameters

4. **Gramps Integration**
   - Work with Gramps team on DBAPI improvements
   - Propose backend-agnostic abstractions
   - Submit patches for PostgreSQL support