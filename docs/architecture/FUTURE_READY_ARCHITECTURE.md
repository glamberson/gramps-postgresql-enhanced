# Future-Ready PostgreSQL Architecture for Gramps

## Design Principles

1. **Complete DBAPI Compatibility** - Works perfectly with current Gramps
2. **PostgreSQL Native Storage** - JSONB as primary storage
3. **Extension Ready** - Prepared for AGE, pgvector, PostGIS
4. **Clean Abstraction Layer** - Easy to enhance without breaking compatibility

## Recommended Architecture

### Phase 1: Rock-Solid Compatibility (Current Priority)

```sql
-- Core tables with hybrid storage
CREATE TABLE person (
    -- Primary key
    handle VARCHAR(50) PRIMARY KEY,
    
    -- JSONB primary storage (source of truth)
    json_data JSONB NOT NULL,
    
    -- Compatibility columns (maintained by triggers)
    gramps_id VARCHAR(50) GENERATED ALWAYS AS (json_data->>'gramps_id') STORED,
    surname TEXT GENERATED ALWAYS AS (json_data->'names'->0->>'surname') STORED,
    given_name TEXT GENERATED ALWAYS AS (json_data->'names'->0->>'given_name') STORED,
    
    -- System columns
    change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Future extension columns (NULL for now)
    vector_embedding vector(768),  -- For pgvector
    graph_properties JSONB,        -- For Apache AGE
    spatial_data geometry          -- For PostGIS
);

-- Indexes for performance
CREATE INDEX idx_person_gramps_id ON person(gramps_id);
CREATE INDEX idx_person_names ON person USING GIN(json_data->'names');
CREATE INDEX idx_person_json ON person USING GIN(json_data);
```

### Key Design Decisions

1. **GENERATED STORED columns** instead of triggers
   - PostgreSQL 12+ feature
   - Automatically maintained
   - Can't be updated (which is good - prevents DBAPI interference)
   - Acts like a materialized index

2. **Override `_update_secondary_values()` to handle GENERATED column errors**
   ```python
   def _update_secondary_values(self, obj):
       """Override to work with GENERATED columns."""
       try:
           super()._update_secondary_values(obj)
       except Exception as e:
           if "GENERATED" in str(e):
               # Expected - GENERATED columns can't be updated
               pass
           else:
               raise
   ```

3. **Extension columns ready but nullable**
   - Add columns for future features
   - Keep NULL until needed
   - No impact on current functionality

### Phase 2: Enhanced Query Layer

Create a parallel API that Gramps doesn't know about:

```python
class EnhancedQueries:
    """PostgreSQL-native queries using JSONB."""
    
    def find_dna_matches(self, person_handle, threshold=0.9):
        """Find genetic matches using pgvector."""
        return self.dbapi.execute("""
            SELECT p2.handle, 
                   1 - (p1.vector_embedding <=> p2.vector_embedding) as similarity
            FROM person p1, person p2
            WHERE p1.handle = %s
              AND p1.vector_embedding IS NOT NULL
              AND p2.vector_embedding IS NOT NULL
              AND p1.handle != p2.handle
              AND 1 - (p1.vector_embedding <=> p2.vector_embedding) > %s
            ORDER BY similarity DESC
        """, [person_handle, threshold])
    
    def find_relationship_path_graph(self, person1, person2):
        """Find relationship using Apache AGE graph queries."""
        return self.dbapi.execute("""
            SELECT * FROM cypher('genealogy_graph', $$
                MATCH path = shortestPath(
                    (p1:Person {handle: $person1})-[*]-(p2:Person {handle: $person2})
                )
                RETURN path
            $$, %s) as (path agtype)
        """, {'person1': person1, 'person2': person2})
```

### Phase 3: Future Migration Path

1. **Create new methods that bypass DBAPI limitations**
   ```python
   def get_person_jsonb(self, handle):
       """Direct JSONB access bypassing DBAPI."""
       result = self.dbapi.execute(
           "SELECT json_data FROM person WHERE handle = %s", 
           [handle]
       )
       return Person.create(result[0]) if result else None
   ```

2. **Gradually migrate Gramps to use new methods**
   - Submit patches upstream
   - Maintain backward compatibility
   - Document performance improvements

## Implementation Strategy

### Step 1: Fix Current Implementation
```python
# In schema.py - Use GENERATED STORED instead of triggers
def _create_object_table(self, obj_type):
    if obj_type in REQUIRED_COLUMNS:
        columns = []
        for col_name, json_path in REQUIRED_COLUMNS[obj_type].items():
            col_type = self._get_column_type(col_name)
            columns.append(
                f"{col_name} {col_type} GENERATED ALWAYS AS ({json_path}) STORED"
            )
        
        self.conn.execute(f"""
            CREATE TABLE {obj_type} (
                handle VARCHAR(50) PRIMARY KEY,
                json_data JSONB NOT NULL,
                {', '.join(columns)},
                change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
```

### Step 2: Handle GENERATED Column Errors
```python
# In postgresqlenhanced.py
def _update_secondary_values(self, obj):
    """Override to handle GENERATED columns gracefully."""
    # Don't update - let PostgreSQL handle it via GENERATED
    # This is actually more efficient than triggers
    pass
```

### Step 3: Add Extension Support
```sql
-- Run once to prepare for future features
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Add columns (nullable, no impact until used)
ALTER TABLE person ADD COLUMN IF NOT EXISTS vector_embedding vector(768);
ALTER TABLE person ADD COLUMN IF NOT EXISTS graph_properties JSONB;
```

## Benefits of This Approach

1. **100% DBAPI Compatible** - Works with current Gramps
2. **Single Source of Truth** - JSONB stores everything
3. **Efficient** - GENERATED columns are maintained by PostgreSQL
4. **Future Ready** - Extension columns ready when needed
5. **Clean Upgrade Path** - Add enhanced methods without breaking compatibility

## Testing Strategy

1. **Compatibility Tests**
   - All Gramps operations work
   - GEDCOM import/export
   - All reports generate correctly

2. **Performance Tests**
   - Benchmark vs SQLite
   - Large database tests (100k+ persons)
   - Concurrent access tests

3. **Future Feature Tests**
   - DNA vector similarity (when ready)
   - Graph relationship queries (when ready)
   - Spatial queries for places (when ready)

This architecture gives you everything:
- Works today with zero compatibility issues
- Uses PostgreSQL's best features
- Ready for cutting-edge extensions
- Clear path to enhance without breaking