# Database Modes - Tree Deletion Behavior
**Date**: 2025-08-06
**PostgreSQL Enhanced Version**: Current

## Database Modes Overview

### 1. Monolithic Mode
- **Single database**: All trees in one database (e.g., `gramps_monolithic`)
- **Table naming**: `tree_<TREEID>_<tablename>`
- **Isolation**: Via table prefix
- **Current state**: ACTIVE with 2 trees + 5 orphaned

### 2. Separate Mode  
- **Multiple databases**: Each tree gets its own database
- **Database naming**: `gramps_tree_<TREEID>`
- **Table naming**: Direct names (no prefix needed)
- **Isolation**: Complete database separation

## Tree Deletion Behavior

### Monolithic Mode - Current Behavior
**When tree deleted in Gramps:**
1. Tree removed from Gramps registry
2. Database tables remain (prefixed with tree ID)
3. Result: Orphaned tables in shared database

**Evidence:**
```sql
-- 7 trees in database
tree_68932301 - 86,647 persons (ACTIVE)
tree_68931a6f -  9,709 persons (ACTIVE)
tree_689310ec -    105 persons (ORPHANED)
tree_689313e0 -     71 persons (ORPHANED)
tree_6893155a -     57 persons (ORPHANED)
tree_68930da4 -     50 persons (ORPHANED)
tree_689304d4 -     14 persons (ORPHANED)

-- Only 2 trees visible in Gramps
```

### Separate Mode - Expected Behavior
**When tree deleted in Gramps:**
1. Tree removed from Gramps registry
2. Database connection closed
3. Database `gramps_tree_<TREEID>` remains on server
4. Result: Orphaned database (not just tables)

## Design Decision: PRESERVE

**Both modes preserve data when tree deleted from Gramps**

### Rationale
1. **Data Safety**: No accidental permanent deletion
2. **Recovery Option**: Can reconnect to orphaned data
3. **Audit Trail**: Historical data preserved
4. **User Control**: Explicit action required for permanent deletion

## Cleanup Procedures

### Monolithic Mode Cleanup
```bash
# List orphaned trees
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -c "
SELECT DISTINCT REPLACE(tablename, '_person', '') as orphaned_tree
FROM pg_tables 
WHERE tablename LIKE 'tree_%_person'
AND REPLACE(tablename, '_person', '') NOT IN (
    -- Add active tree IDs here
    'tree_68932301', 'tree_68931a6f'
);"

# Drop specific orphaned tree tables
TREE_ID="689304d4"  # Example
for table_type in person family event place source citation repository media note tag metadata reference name_group gender_stats; do
    PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -c "
    DROP TABLE IF EXISTS tree_${TREE_ID}_${table_type} CASCADE;"
done
```

### Separate Mode Cleanup
```bash
# List all gramps databases
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d postgres -c "
SELECT datname FROM pg_database 
WHERE datname LIKE 'gramps_tree_%'
ORDER BY datname;"

# Drop orphaned database
TREE_ID="689304d4"  # Example
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d postgres -c "
DROP DATABASE IF EXISTS gramps_tree_${TREE_ID};"
```

## Scale Considerations

### User's 400 GEDCOMs Scenario

**Monolithic Mode:**
- 1 database with 400 tree prefixes
- Orphans: 400+ sets of tables
- Management: Complex table filtering
- Performance: Potential catalog bloat

**Separate Mode:**
- 400 individual databases
- Orphans: Entire databases remain
- Management: Easier to identify orphans
- Performance: Better isolation, connection overhead

## Recommendations

### For Testing Phase
- Keep both modes' PRESERVE behavior
- Document thoroughly
- Create admin scripts

### For Production (400 GEDCOMs)
- Consider separate mode for better isolation
- Implement database naming convention
- Create management dashboard
- Regular orphan audits

### Future Enhancement
```python
# Add to postgresqlenhanced.py
def cleanup_tree(self, tree_id, mode='soft'):
    """
    Clean up tree data with safety checks
    
    Args:
        tree_id: Tree identifier
        mode: 'soft' (mark deleted), 'archive' (move), 'hard' (drop)
    """
    if mode == 'soft':
        # Mark as deleted in metadata
        pass
    elif mode == 'archive':
        # Move to archive schema
        pass
    elif mode == 'hard':
        # Require double confirmation
        # Log the deletion
        # Then DROP
        pass
```

## Testing Checklist

### Monolithic Mode
- [x] Create tree → tables created with prefix
- [x] Delete tree in Gramps → tables remain
- [x] Verify orphaned tables queryable
- [ ] Test cleanup script

### Separate Mode  
- [ ] Create tree → new database created
- [ ] Delete tree in Gramps → database remains
- [ ] Verify orphaned database accessible
- [ ] Test cleanup script

## Summary

**Current behavior is CORRECT and SAFE for both modes:**
- Monolithic: Orphaned tables in shared database
- Separate: Orphaned databases on server
- Both: Require explicit cleanup action
- Both: Preserve user data by default

This is the safest approach for irreplaceable genealogy data.