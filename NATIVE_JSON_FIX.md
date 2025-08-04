# Native JSON Support Fix for PostgreSQL Enhanced

## The Problem

We've been fighting against DBAPI's design instead of using its native JSON support properly. DBAPI has built-in JSON storage support that we're not leveraging correctly.

## How DBAPI's JSON Support Works

1. **Schema Creation**: When `_create_schema(json_data=True)` is called, DBAPI creates tables with:
   - Primary key (handle)
   - Secondary columns (surname, given_name, etc.)
   - json_data column (NOT blob_data)

2. **Serializer Selection**: DBAPI checks if `json_data` column exists in metadata table via `use_json_data()`
   - If exists: Uses JSONSerializer
   - If not: Uses BlobSerializer

3. **Data Flow with JSONSerializer**:
   - `_commit_base()` stores full object in json_data column
   - `_update_secondary_values()` updates secondary columns from the object
   - Queries use secondary columns for WHERE clauses
   - Full object loaded from json_data

## Our Current Issues

1. We create both json_data AND blob_data columns (DBAPI expects only one)
2. We override `_update_secondary_values()` to do nothing (breaking DBAPI's design)
3. We use triggers to sync from JSONB (unnecessary complexity)
4. We don't call parent's load() method (missing proper initialization)

## The Fix

### Option 1: Work WITH DBAPI's Design

Let DBAPI manage the secondary columns as it expects:

```python
def load(self, directory, **kwargs):
    # Set up our connection first
    self._setup_postgresql_connection(directory)
    
    # Let parent handle schema creation with json_data=True
    super().load(directory, json_data=True, **kwargs)
    
    # Our enhancements go here
    self._setup_enhanced_indexes()

def _update_secondary_values(self, obj):
    # Let parent update secondary columns normally
    super()._update_secondary_values(obj)
    
    # Add any PostgreSQL-specific optimizations here
    # But don't block the normal flow
```

### Option 2: Override Schema Creation

Keep our JSONB approach but properly integrate:

```python
def _create_schema(self, json_data=True):
    """Override to create PostgreSQL-optimized schema."""
    # Create schema with JSONB instead of TEXT
    self.dbapi.begin()
    
    # Create tables with json_data as JSONB
    for table in TABLES:
        self.dbapi.execute(f"""
            CREATE TABLE {table} (
                handle VARCHAR(50) PRIMARY KEY,
                json_data JSONB,  -- JSONB instead of TEXT
                {secondary_columns}
            )
        """)
    
    # Let DBAPI know we're using JSON
    self.dbapi.execute("""
        CREATE TABLE metadata (
            setting VARCHAR(255) PRIMARY KEY,
            json_data JSONB  -- This tells DBAPI to use JSONSerializer
        )
    """)
    
    self.dbapi.commit()
```

## Recommended Approach

1. **Remove trigger-based syncing** - Let DBAPI update secondary columns directly
2. **Remove `_update_secondary_values()` override** - Use parent's implementation
3. **Call parent's load()** - Get proper initialization
4. **Use JSONB for storage** - But let DBAPI manage secondary columns
5. **Add PostgreSQL enhancements** - Without breaking DBAPI's flow

## Benefits

- Works with DBAPI's design, not against it
- Simpler architecture (no triggers needed)
- Single source of truth (DBAPI manages consistency)
- Can still use JSONB features for enhanced queries
- Maintains compatibility with Gramps

## Implementation Steps

1. Remove `_create_sync_trigger()` and trigger creation
2. Remove `_update_secondary_values()` override
3. Modify load() to call parent properly
4. Update schema creation to use JSONB for json_data column
5. Test that secondary columns are properly updated by DBAPI

This approach gives us PostgreSQL's JSONB benefits while maintaining full DBAPI compatibility.