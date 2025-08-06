# Orphaned Trees Design Decision
**Date**: 2025-08-06
**Issue**: Trees deleted in Gramps UI leave tables in PostgreSQL

## Current Situation

### Database Contains 7 Trees
```
tree_68932301 - 86,647 persons (ACTIVE - just imported)
tree_68931a6f -  9,709 persons (ACTIVE - test data)
tree_689310ec -    105 persons (ORPHANED)
tree_689313e0 -     71 persons (ORPHANED)
tree_6893155a -     57 persons (ORPHANED)
tree_68930da4 -     50 persons (ORPHANED)
tree_689304d4 -     14 persons (ORPHANED)
```

### Gramps UI Shows Only 2 Trees
- The 5 orphaned trees were deleted via Gramps Family Tree Manager
- PostgreSQL tables remain in database
- Total orphaned data: ~300 persons, ~4MB

## Design Considerations

### Current Behavior: PRESERVE (Data Safety)
**What happens now:**
- Gramps removes tree from its internal registry
- PostgreSQL tables remain untouched
- Data is "orphaned" but preserved

**Pros:**
- ✅ Zero risk of accidental data loss
- ✅ Recovery possible if deletion was mistake
- ✅ Audit trail maintained
- ✅ Follows database best practices (explicit DROP required)

**Cons:**
- ❌ Database accumulates orphaned tables
- ❌ Storage waste over time (minor at 4MB per tree)
- ❌ Confusion about which trees are active
- ❌ Manual cleanup required

### Alternative 1: AUTO-DROP (Clean)
**What would happen:**
- Gramps deletion triggers CASCADE DROP of all tables
- Immediate space reclamation
- Clean database state

**Pros:**
- ✅ Clean database, no orphans
- ✅ Storage efficiency
- ✅ Clear active/inactive distinction
- ✅ No manual maintenance

**Cons:**
- ❌ IRREVERSIBLE data loss
- ❌ No recovery from accidental deletion
- ❌ Violates "never lose user data" principle
- ❌ High risk for genealogy data (irreplaceable)

### Alternative 2: SOFT DELETE (Hybrid)
**What could happen:**
- Add `deleted_at` timestamp to metadata
- Hide deleted trees from Gramps
- Provide "recover" and "purge" options

**Pros:**
- ✅ Recoverable deletions
- ✅ Clear active/inactive state
- ✅ Admin can purge when certain
- ✅ Best of both worlds

**Cons:**
- ❌ More complex implementation
- ❌ Requires UI changes
- ❌ Migration needed for existing trees

## Scale Implications

With user's 400 GEDCOMs:
- **Orphan risk**: 400 trees × 2.8GB = 1.12TB potential orphans
- **Management overhead**: Tracking 400+ tree states
- **Recovery importance**: Each tree represents years of research

## Recommendation: ENHANCED PRESERVE

### Short Term (Current)
1. **Keep current PRESERVE behavior**
2. **Document cleanup procedure**
3. **Add admin script for orphan detection**

### Medium Term (Next Release)
1. **Add tree status tracking**:
```sql
ALTER TABLE tree_metadata ADD COLUMN status VARCHAR(20) DEFAULT 'active';
ALTER TABLE tree_metadata ADD COLUMN deleted_at TIMESTAMP;
```

2. **Implement cleanup tool**:
```python
# gramps_db_admin.py
def list_orphaned_trees():
    """List trees in DB but not in Gramps"""
    
def archive_tree(tree_id):
    """Move tree tables to archive schema"""
    
def purge_tree(tree_id, confirm=True):
    """Permanently delete tree with confirmation"""
```

3. **Add UI warnings**:
- "This will remove the tree from Gramps. Database tables will be preserved for safety."
- "To permanently delete, use Database Administration tool."

### Long Term (Future)
1. **Tree lifecycle management**
2. **Automated backups before deletion**
3. **Configurable retention policy**
4. **Point-in-time recovery**

## Implementation Priority

Given that:
- User has 38 million persons to import
- Each tree is irreplaceable family history
- Current orphans are only 4MB total
- Data safety is paramount

**Decision: Keep PRESERVE behavior, add management tools**

## Cleanup Script for Current Orphans

```bash
#!/bin/bash
# cleanup_orphaned_trees.sh

echo "Orphaned trees in database:"
echo "tree_689304d4 - 14 persons"
echo "tree_68930da4 - 50 persons"  
echo "tree_689310ec - 105 persons"
echo "tree_689313e0 - 71 persons"
echo "tree_6893155a - 57 persons"

read -p "Delete these orphaned trees? (y/N): " confirm
if [ "$confirm" = "y" ]; then
    for tree in 689304d4 68930da4 689310ec 689313e0 6893155a; do
        echo "Dropping tree_${tree}_* tables..."
        PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 \
            -U genealogy_user -d gramps_monolithic -c "
        DROP TABLE IF EXISTS tree_${tree}_person CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_family CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_event CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_place CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_source CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_citation CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_repository CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_media CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_note CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_tag CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_metadata CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_reference CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_name_group CASCADE;
        DROP TABLE IF EXISTS tree_${tree}_gender_stats CASCADE;"
    done
    echo "Cleanup complete."
else
    echo "Cleanup cancelled."
fi
```

## Summary

**Current behavior (PRESERVE) is correct for genealogy data.**

Reasons:
1. Data safety trumps storage efficiency
2. 4MB of orphans vs risk of losing 86,647 persons
3. User's 38 million person dataset is irreplaceable
4. Manual cleanup is acceptable trade-off
5. Can enhance with tools without changing core behavior

**Action**: Document as intended behavior, provide cleanup tools.