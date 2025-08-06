# Multi-Database Isolation Test Plan
**Date**: 2025-08-06
**Current State**: Single database (gramps_monolithic) with 2 active trees

## Objective
Test PostgreSQL Enhanced's ability to isolate trees across multiple databases while maintaining data integrity and preventing cross-contamination.

## Current Architecture

### Monolithic Mode (Currently Active)
- Single database: `gramps_monolithic`
- Table prefixes: `tree_TREEID_tablename`
- All trees share one database
- Connection info: `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt`

### Multi-Database Mode (To Test)
- Each tree in separate database
- Database naming: `gramps_tree_TREEID`
- Complete isolation between trees
- Connection switching required

## Test Scenarios

### 1. Create New Database for New Tree
```bash
# Create new database
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d postgres -c "
CREATE DATABASE gramps_tree_test WITH OWNER genealogy_user;"

# Update connection_info.txt to:
database_mode = multi_database
# Then create new tree in Gramps
```

### 2. Migration Test (Optional - High Risk)
- Export tree from monolithic database
- Import into separate database
- Verify data integrity

### 3. Connection Switching Test
- Open tree in database A
- Close and open tree in database B
- Verify no data leakage

### 4. Concurrent Access Test
- Open two Gramps instances
- Each accessing different database
- Verify isolation

## Implementation Steps

### Step 1: Backup Current State
```bash
# Backup monolithic database
PGPASSWORD='GenealogyData2025' pg_dump -h 192.168.10.90 -U genealogy_user \
    -d gramps_monolithic -f gramps_monolithic_backup_20250806.sql

# Backup connection info
cp ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt \
   ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt.bak
```

### Step 2: Modify Configuration
Edit `connection_info.txt`:
```ini
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = multi_database  # Changed from monolithic
# shared_database_name line removed or commented
```

### Step 3: Create Test Database
```bash
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d postgres -c "
CREATE DATABASE gramps_tree_multitest WITH OWNER genealogy_user;"
```

### Step 4: Test in Gramps
1. Close Gramps completely
2. Update configuration
3. Start Gramps with debug
4. Create new tree
5. Verify database creation
6. Import small test GEDCOM

## Verification Queries

### Check Database List
```sql
SELECT datname FROM pg_database 
WHERE datname LIKE 'gramps%' 
ORDER BY datname;
```

### Check Table Isolation
```sql
-- In gramps_monolithic
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename LIKE 'tree_%'
ORDER BY tablename;

-- In gramps_tree_multitest (should be different)
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
```

### Check No Cross-References
```sql
-- Run in each database
SELECT COUNT(*) as foreign_references
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
AND constraint_schema = 'public';
```

## Risk Assessment

### Low Risk
- Creating new databases
- Testing with new trees
- Read-only verification queries

### Medium Risk
- Switching database modes
- Connection configuration changes
- Multiple Gramps instances

### High Risk
- Migrating existing trees
- Modifying production data
- Database deletions

## Rollback Plan

1. **Restore Configuration**:
```bash
cp ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt.bak \
   ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt
```

2. **Drop Test Databases**:
```sql
DROP DATABASE IF EXISTS gramps_tree_multitest;
DROP DATABASE IF EXISTS gramps_tree_test;
```

3. **Restart Gramps**:
- Close all instances
- Clear any lock files
- Start fresh with monolithic mode

## Success Criteria

✅ New database created per tree
✅ No table prefix in multi-database mode
✅ Complete isolation verified
✅ No performance degradation
✅ Clean switching between databases
✅ No data corruption or loss

## Notes

- User has 400 GEDCOMs to import eventually
- Each in separate database would mean 400 databases
- Consider hybrid approach: grouped databases
- May need connection pooling at scale
- Database naming convention critical for management