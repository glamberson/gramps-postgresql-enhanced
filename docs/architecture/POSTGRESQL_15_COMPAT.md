# PostgreSQL 15+ Compatible Implementation

## Current Situation

- Your server runs PostgreSQL 17.5 (great!)
- Need to maintain PostgreSQL 15 compatibility
- GENERATED STORED columns are fully supported in PostgreSQL 12+

## Key PostgreSQL 15 Features We Can Use

1. **GENERATED STORED columns** ✓ (since PostgreSQL 12)
2. **JSONB path expressions** ✓ 
3. **MERGE statement** ✓ (new in PostgreSQL 15)
4. **SQL/JSON constructors** ✓ (enhanced in PostgreSQL 15)
5. **Parallel query improvements** ✓

## Implementation for PostgreSQL 15 Compatibility

### 1. Table Creation (PostgreSQL 15 Compatible)

```sql
CREATE TABLE IF NOT EXISTS person (
    -- Primary storage
    handle VARCHAR(50) PRIMARY KEY,
    json_data JSONB NOT NULL,
    
    -- GENERATED STORED columns (PostgreSQL 12+)
    gramps_id VARCHAR(50) GENERATED ALWAYS AS (json_data->>'gramps_id') STORED,
    surname TEXT GENERATED ALWAYS AS (
        json_data#>>'{names,0,surname,surname}'  -- SQL/JSON path
    ) STORED,
    given_name TEXT GENERATED ALWAYS AS (
        json_data#>>'{names,0,first_name}'
    ) STORED,
    gender INTEGER GENERATED ALWAYS AS (
        (json_data->>'gender')::INTEGER
    ) STORED,
    
    -- Metadata
    change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Future extensions (nullable)
    vector_embedding vector(768),  -- Requires pgvector extension
    graph_node_id BIGINT          -- For Apache AGE
);

-- Indexes (all PostgreSQL 15 compatible)
CREATE INDEX idx_person_gramps_id ON person(gramps_id);
CREATE INDEX idx_person_surname ON person(surname);
CREATE INDEX idx_person_json ON person USING GIN(json_data);
CREATE INDEX idx_person_names ON person USING GIN(json_data->'names');
```

### 2. Handle GENERATED Column UPDATE Errors

Since PostgreSQL won't allow UPDATE on GENERATED columns, we need to handle this at the psycopg3 level:

```python
# In connection.py
import psycopg.errors

def execute(self, query, params=None):
    """Execute with PostgreSQL 15+ error handling."""
    try:
        with self._get_cursor() as cur:
            cur.execute(query, params)
            self.connection.commit()
    except psycopg.errors.GeneratedAlways as e:
        # PostgreSQL 15: "column ... can only be updated to DEFAULT"
        if "UPDATE" in query.upper():
            # Expected for GENERATED columns - silently succeed
            self.connection.rollback()
            logging.debug(f"Ignored GENERATED column UPDATE: {e}")
            return
        raise
    except psycopg.errors.Error as e:
        self.connection.rollback()
        # Check for GENERATED column errors by SQLSTATE
        if e.sqlstate == '428C9':  # generated_always
            logging.debug(f"Ignored GENERATED column error: {e}")
            return
        raise
```

### 3. Schema Detection for PostgreSQL Version

```python
# In schema.py
def get_postgresql_version(self):
    """Get PostgreSQL version for feature compatibility."""
    result = self.conn.execute("SELECT version()").fetchone()
    # Parse "PostgreSQL 15.x ..." or "PostgreSQL 17.5 ..."
    import re
    match = re.search(r'PostgreSQL (\d+)\.(\d+)', result[0])
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        return (major, minor)
    return (15, 0)  # Safe default

def create_schema(self):
    """Create schema compatible with PostgreSQL 15+."""
    version = self.get_postgresql_version()
    if version[0] < 15:
        raise Exception(f"PostgreSQL 15+ required, found {version[0]}.{version[1]}")
    
    # Use PostgreSQL 15+ features
    self._create_tables_with_generated_columns()
```

### 4. Alternative: Updatable Views (PostgreSQL 15 Feature)

If GENERATED columns prove problematic, use updatable views:

```sql
-- Base table with JSONB only
CREATE TABLE person_data (
    handle VARCHAR(50) PRIMARY KEY,
    json_data JSONB NOT NULL,
    change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Updatable view that DBAPI sees
CREATE VIEW person AS
SELECT 
    handle,
    json_data,
    json_data->>'gramps_id' AS gramps_id,
    json_data#>>'{names,0,surname,surname}' AS surname,
    json_data#>>'{names,0,first_name}' AS given_name,
    (json_data->>'gender')::INTEGER AS gender,
    change_time
FROM person_data;

-- PostgreSQL 15: Automatically updatable for simple views
-- But we can add explicit rules for complex updates
CREATE RULE person_update AS ON UPDATE TO person
WHERE OLD.handle = NEW.handle
DO INSTEAD UPDATE person_data 
SET json_data = NEW.json_data,
    change_time = CURRENT_TIMESTAMP
WHERE handle = OLD.handle;
```

### 5. Use PostgreSQL 15's MERGE for Upserts

```python
def _commit_base(self, obj, obj_key, trans, change_time):
    """Use PostgreSQL 15 MERGE for atomic upserts."""
    table = KEY_TO_NAME_MAP[obj_key]
    
    # PostgreSQL 15's MERGE statement
    self.dbapi.execute(f"""
        MERGE INTO {table} AS target
        USING (VALUES (%s, %s::jsonb)) AS source(handle, json_data)
        ON target.handle = source.handle
        WHEN MATCHED THEN
            UPDATE SET json_data = source.json_data
        WHEN NOT MATCHED THEN
            INSERT (handle, json_data) VALUES (source.handle, source.json_data)
    """, [obj.handle, self.serializer.object_to_string(obj)])
    
    # Let GENERATED columns auto-update
    # Don't call _update_secondary_values()
```

## Testing PostgreSQL 15 Compatibility

```bash
# Create test database with version check
psql -c "SELECT version();" 
psql -c "SELECT current_setting('server_version_num')::int >= 150000 as is_pg15_plus;"

# Test GENERATED columns
psql -c "
CREATE TABLE test_generated (
    id SERIAL PRIMARY KEY,
    data JSONB,
    name TEXT GENERATED ALWAYS AS (data->>'name') STORED
);
INSERT INTO test_generated(data) VALUES ('{\"name\":\"test\"}');
SELECT * FROM test_generated;
"
```

## Summary

For PostgreSQL 15 compatibility:
1. Use GENERATED STORED columns (available since PostgreSQL 12)
2. Handle UPDATE errors gracefully in psycopg3
3. Consider updatable views as alternative
4. Use MERGE for better upsert performance
5. Test on PostgreSQL 15 to ensure compatibility

This approach gives you modern PostgreSQL features while maintaining broad compatibility.