# SQLite to PostgreSQL Migration Tool Analysis

## Overview

A migration tool would need to convert existing Gramps SQLite databases to the PostgreSQL Enhanced format, transforming pickled BLOBs into JSONB while preserving all data and relationships.

## Technical Requirements

### 1. Data Extraction from SQLite

```python
# SQLite stores Gramps objects as pickled BLOBs
# Table structure in SQLite:
# - handle (TEXT PRIMARY KEY)
# - blob_data (BLOB) - pickled Gramps object
# - order_by (TEXT) - for sorting

# Need to:
1. Connect to SQLite database
2. Read each table (person, family, event, etc.)
3. Unpickle the blob_data to get Gramps objects
4. Extract secondary fields for indexing
```

### 2. Data Transformation

```python
# Transform Gramps objects to JSON structure
def transform_person(gramps_person):
    # Convert Gramps Person object to JSON-compatible dict
    return {
        "handle": gramps_person.handle,
        "gramps_id": gramps_person.gramps_id,
        "gender": gramps_person.gender,
        "primary_name": name_to_dict(gramps_person.primary_name),
        "names": [name_to_dict(n) for n in gramps_person.names],
        "birth_ref_index": gramps_person.birth_ref_index,
        "death_ref_index": gramps_person.death_ref_index,
        # ... all other fields
    }

# Extract secondary columns for performance
def extract_secondary_fields(person_dict):
    return {
        "given_name": person_dict["primary_name"]["first_name"],
        "surname": person_dict["primary_name"]["surname_list"][0]["surname"],
        "birth_date": extract_birth_date(person_dict),
        # ... other indexed fields
    }
```

### 3. Migration Process Flow

```
1. Pre-Migration Phase
   - Verify source SQLite database
   - Check target PostgreSQL connection
   - Estimate data volume and time
   - Create backup of source

2. Schema Creation Phase  
   - Create PostgreSQL database (if separate mode)
   - Initialize PostgreSQL Enhanced schema
   - Create all tables with JSONB columns

3. Data Migration Phase
   - For each object type (person, family, etc.):
     a. Read batch from SQLite
     b. Unpickle objects
     c. Transform to JSON
     d. Extract secondary fields
     e. Bulk insert to PostgreSQL
     f. Update progress

4. Verification Phase
   - Compare record counts
   - Verify sample objects
   - Check relationships integrity
   - Generate migration report

5. Post-Migration Phase
   - Create indexes
   - Update statistics
   - Run VACUUM ANALYZE
   - Final verification
```

## Implementation Complexity

### Core Migration Code (~500-800 lines)

```python
class SQLiteToPostgreSQLMigrator:
    def __init__(self, sqlite_path, pg_config, batch_size=1000):
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
        self.batch_size = batch_size
        self.stats = defaultdict(int)
        
    def migrate(self):
        """Main migration entry point."""
        # 1. Connect to both databases
        # 2. Create PostgreSQL schema
        # 3. Migrate each object type
        # 4. Verify migration
        # 5. Generate report
        
    def migrate_persons(self):
        """Migrate person objects."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT handle, blob_data FROM person")
        
        batch = []
        for handle, blob in cursor:
            person = pickle.loads(blob)
            json_data = self.transform_person(person)
            secondary = self.extract_person_fields(json_data)
            
            batch.append((handle, json_data, secondary))
            
            if len(batch) >= self.batch_size:
                self.bulk_insert_persons(batch)
                batch = []
                
    def verify_migration(self):
        """Compare source and target databases."""
        # Check counts, sample objects, relationships
```

### Challenges and Solutions

| Challenge | Solution |
|-----------|----------|
| **Large databases (1M+ persons)** | Batch processing with progress reporting |
| **Memory usage** | Stream processing, don't load all at once |
| **Pickle compatibility** | Use same Gramps version for migration |
| **Relationship integrity** | Migrate in dependency order |
| **Performance** | Use COPY instead of INSERT for bulk ops |
| **Rollback capability** | Transaction per object type |
| **Progress tracking** | CLI progress bar with ETA |

### Time Estimates

| Database Size | Migration Time | Complexity |
|--------------|----------------|------------|
| < 10K persons | < 1 minute | Low |
| 10K - 100K | 5-10 minutes | Medium |
| 100K - 1M | 30-60 minutes | High |
| > 1M persons | 2-4 hours | Very High |

## Proposed Implementation Plan

### Phase 1: Basic Migration (2-3 days)
- Read SQLite schema
- Unpickle objects
- Transform to JSON
- Basic insertion
- Progress reporting

### Phase 2: Optimization (1-2 days)
- Batch processing
- COPY command usage
- Memory optimization
- Parallel processing

### Phase 3: Verification (1 day)
- Data integrity checks
- Relationship verification
- Sample comparisons
- Report generation

### Phase 4: Polish (1 day)
- Error handling
- Resume capability
- Rollback support
- Documentation

## Usage Example

```bash
# Basic migration
python migrate_sqlite_to_pg.py \
    --sqlite /path/to/gramps.db \
    --pg-host localhost \
    --pg-database gramps_migrated \
    --batch-size 5000

# With options
python migrate_sqlite_to_pg.py \
    --sqlite /path/to/gramps.db \
    --pg-config connection.txt \
    --verify-samples 100 \
    --parallel 4 \
    --resume
```

## Risk Assessment

### Low Risk
- Read-only on source database
- Can retry if fails
- Non-destructive process

### Medium Risk  
- Large memory usage for big databases
- Long running process (hours)
- Network interruption for remote PostgreSQL

### Mitigation
- Implement resume capability
- Progress checkpoints
- Memory monitoring
- Connection retry logic

## Conclusion

A SQLite to PostgreSQL migration tool is:
- **Technically feasible** - All required APIs available
- **Medium complexity** - ~1 week development time
- **High value** - Enables existing users to upgrade
- **Low risk** - Non-destructive, retryable

The main complexity comes from:
1. Unpickling Gramps objects correctly
2. Handling large datasets efficiently  
3. Ensuring data integrity
4. Providing good user experience

Recommended approach: Start with basic functionality for small databases, then optimize for larger ones.