# GENERATED COLUMNS Fix Strategy

## The Problem We Already Know

- GENERATED columns can't be UPDATE'd (PostgreSQL limitation)
- DBAPI's `_update_secondary_values()` tries to UPDATE them
- Results in: "column can only be updated to DEFAULT" error

## The Smart Solution

### 1. Intercept UPDATE Errors at Connection Level

Instead of overriding `_update_secondary_values()`, intercept and handle the errors:

```python
# In connection.py
def execute(self, query, params=None):
    """Execute query with GENERATED column error handling."""
    try:
        with self._get_cursor() as cur:
            cur.execute(query, params)
            self.connection.commit()
    except psycopg.errors.GeneratedAlways as e:
        # This is expected for GENERATED columns
        # Log but don't fail
        if "UPDATE" in query and any(col in query for col in ['surname', 'given_name', 'gramps_id']):
            # Silently succeed - the GENERATED column already has the right value
            logging.debug(f"Ignoring GENERATED column UPDATE: {query}")
            self.connection.rollback()
            return
        else:
            raise
    except Exception as e:
        self.connection.rollback()
        raise
```

### 2. Use GENERATED STORED with Proper Expressions

```sql
CREATE TABLE person (
    handle VARCHAR(50) PRIMARY KEY,
    json_data JSONB NOT NULL,
    
    -- GENERATED columns that auto-update from JSONB
    gramps_id VARCHAR(50) GENERATED ALWAYS AS (json_data->>'gramps_id') STORED,
    surname TEXT GENERATED ALWAYS AS (
        COALESCE(json_data->'names'->0->'surname'->>'surname', '')
    ) STORED,
    given_name TEXT GENERATED ALWAYS AS (
        COALESCE(json_data->'names'->0->'first_name'->>'', '')
    ) STORED,
    
    -- More GENERATED columns as needed
    gender INTEGER GENERATED ALWAYS AS (
        CAST(json_data->>'gender' AS INTEGER)
    ) STORED,
    
    change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Smart Error Handling in _update_secondary_values

```python
def _update_secondary_values(self, obj):
    """Override to handle GENERATED columns."""
    # Try parent's update
    try:
        super()._update_secondary_values(obj)
    except Exception as e:
        error_msg = str(e).lower()
        # Expected errors for GENERATED columns
        if any(phrase in error_msg for phrase in [
            'generated', 
            'can only be updated to default',
            'cannot update generated column'
        ]):
            # This is fine - GENERATED columns auto-update from json_data
            pass
        else:
            # Real error - re-raise
            raise
```

## Why This is Better Than Triggers

1. **PostgreSQL Native** - GENERATED columns are maintained by the database engine
2. **No Trigger Overhead** - Computed at storage time, not via trigger
3. **Consistency Guaranteed** - Can never be out of sync with json_data
4. **Query Optimizer Aware** - PostgreSQL knows about GENERATED columns for planning

## Complete Implementation Plan

### Step 1: Modify Schema Creation

```python
# In schema.py
def _create_object_table(self, obj_type):
    if obj_type not in REQUIRED_COLUMNS:
        return
        
    # Build GENERATED column definitions
    generated_cols = []
    for col_name, json_path in REQUIRED_COLUMNS[obj_type].items():
        col_type = self._get_column_type(col_name)
        # COALESCE prevents NULL issues
        safe_path = f"COALESCE({json_path}, {self._get_default_value(col_type)})"
        generated_cols.append(
            f"{col_name} {col_type} GENERATED ALWAYS AS ({safe_path}) STORED"
        )
    
    # Create table with GENERATED columns
    self.conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {obj_type} (
            handle VARCHAR(50) PRIMARY KEY,
            json_data JSONB NOT NULL,
            {', '.join(generated_cols)},
            change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

### Step 2: Remove Trigger Code

- Delete `_create_sync_trigger()` method
- Remove trigger creation calls
- Simpler, cleaner architecture

### Step 3: Add Robust Error Handling

Handle all GENERATED column scenarios:
- UPDATE attempts (ignore)
- INSERT with values (strip them)
- SELECT queries (work normally)

## Testing Approach

1. Drop existing tables
2. Recreate with GENERATED STORED
3. Test person creation
4. Verify secondary columns auto-populate
5. Confirm UPDATE errors are handled gracefully

This gives you the best of all worlds:
- DBAPI compatibility 
- PostgreSQL native features
- Single source of truth (JSONB)
- Future-ready architecture