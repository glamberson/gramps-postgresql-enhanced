# PostgreSQL Enhanced - Architectural Analysis
## Date: 2025-08-04
## Analysis of DBAPI Requirements vs Implementation

### Executive Summary

After deep analysis of the Gramps DBAPI implementation, I've discovered that DBAPI is more sophisticated than initially understood. It has built-in support for JSON storage, but our implementation has several architectural misalignments that need addressing.

### Key Discoveries

#### 1. DBAPI's JSON Support
DBAPI is **designed** to support JSON storage natively:
- `DbGeneric.load()` has `json_data=True` parameter by default
- DBAPI checks for `json_data` column existence to auto-select serializer
- Two serializers available: `JSONSerializer` and `BlobSerializer`
- JSON is the preferred modern storage format

#### 2. Current Implementation Issues

##### A. Secondary Columns Architecture Conflict
**The Problem**: 
- DBAPI expects to directly UPDATE secondary columns via SQL
- We created real columns but sync via triggers from JSONB
- We override `_update_secondary_values()` to do nothing
- This creates a data flow conflict

**Why This Matters**:
- Violates principle of least surprise
- Creates two sources of truth (columns vs JSONB)
- Triggers add overhead on every insert/update
- Complicates debugging and maintenance

##### B. Schema Version Management
**Current Workaround**:
```python
# We bypass parent's load() and set version directly
self._set_metadata("version", "21")
```

**The Issue**:
- Parent's `load()` method handles schema creation and versioning
- We're fighting the framework instead of working with it
- Missing other initialization that parent's load() performs

##### C. Type System Mismatches
**SQLite Assumptions in DBAPI**:
- Booleans stored as integers (0/1)
- `_sql_cast_list()` converts Python types to SQLite types
- We handle this in connection layer, but it's a band-aid

### Architecture Recommendations

#### 1. Embrace DBAPI's Design Intent

**Option A: Pure JSONB with Virtual Columns (PostgreSQL 12+)**
```sql
-- Use GENERATED columns properly
CREATE TABLE person (
    handle VARCHAR(50) PRIMARY KEY,
    json_data JSONB,
    given_name TEXT GENERATED ALWAYS AS (json_data->>'given_name') STORED,
    surname TEXT GENERATED ALWAYS AS (json_data->>'surname') STORED
);
```

**Option B: Hybrid Storage with Proper Updates**
- Keep physical columns
- Let DBAPI update them via `_update_secondary_values()`
- Use JSONB for enhanced queries only
- Single source of truth: physical columns

**Option C: Override DBAPI Query Methods**
- Override methods that generate SQL queries
- Rewrite to use JSONB operators instead of columns
- Most aligned with PostgreSQL strengths
- Requires more extensive changes

#### 2. Fix the Inheritance Chain

Instead of bypassing parent's `load()`:
```python
def load(self, directory, **kwargs):
    # Set up our connection first
    self._setup_postgresql_connection(directory)
    
    # Let parent handle standard initialization
    super().load(directory, json_data=True, **kwargs)
    
    # Add our enhancements
    self._setup_enhanced_features()
```

#### 3. Leverage PostgreSQL Native Features

**What DBAPI Doesn't Know About**:
- JSONB operators (`@>`, `?`, `#>>`)
- GIN indexes on JSONB
- Partial indexes
- Expression indexes
- Array operations
- Full-text search on JSON

**Opportunities**:
1. **Enhanced Search Methods**:
   ```python
   def find_people_by_json_path(self, path, value):
       """PostgreSQL-specific: Search using JSONB paths"""
       return self.dbapi.execute(
           "SELECT handle FROM person WHERE json_data #>> ? = ?",
           [path, value]
       )
   ```

2. **Bulk Operations**:
   ```python
   def bulk_update_json_field(self, handles, path, value):
       """Update specific JSON field without loading full objects"""
       self.dbapi.execute(
           "UPDATE person SET json_data = jsonb_set(json_data, ?, ?) "
           "WHERE handle = ANY(?)",
           [path, json.dumps(value), handles]
       )
   ```

3. **Advanced Queries**:
   ```python
   def find_related_people(self, handle, max_depth=3):
       """Use recursive CTEs for relationship traversal"""
       # PostgreSQL-specific recursive query
   ```

### Immediate Action Items

1. **Decide on Column Strategy**:
   - [ ] Pure JSONB with proper GENERATED columns?
   - [ ] Keep physical columns and let DBAPI update them?
   - [ ] Override query generation to use JSONB?

2. **Fix Inheritance Issues**:
   - [ ] Properly call parent's load()
   - [ ] Handle schema creation through DBAPI
   - [ ] Remove manual version setting

3. **Type System Alignment**:
   - [ ] Create proper type mapping layer
   - [ ] Handle at DBAPI level, not connection level
   - [ ] Document all type conversions

### Technical Debt to Address

1. **Configuration Management**:
   - Hardcoded credentials
   - No environment variable support
   - No connection pooling configuration

2. **Error Handling**:
   - Silent failures in trigger sync
   - No validation of JSON structure
   - Missing constraint checks

3. **Performance Optimization**:
   - Prepared statements not used
   - No query result caching
   - Missing connection pooling

### Conclusion

DBAPI is more capable than initially assessed. It supports JSON storage natively and expects certain patterns. Our current implementation fights against these patterns rather than embracing them. 

The path forward requires choosing between:
1. Working within DBAPI's constraints (easier, more compatible)
2. Extending DBAPI's capabilities (harder, more powerful)

Given the goal of "pushing the envelope," I recommend Option C: Override query methods to use JSONB natively while maintaining API compatibility. This gives us the best of both worlds - compatibility with Gramps and full PostgreSQL power.

### Next Steps

1. Create proof-of-concept for JSONB query override approach
2. Test with real genealogy data
3. Benchmark against SQLite implementation
4. Document PostgreSQL-specific enhancements
5. Contribute improvements back to Gramps project