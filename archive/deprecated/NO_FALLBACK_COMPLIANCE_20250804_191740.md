# NO FALLBACK Policy Compliance Update
## Date: 2025-08-04 19:17:40 EEST
## Issue: GENERATED Columns vs DBAPI Expectations

### Problem Summary
The PostgreSQL Enhanced addon was using GENERATED STORED columns which:
1. Cannot be directly updated (PostgreSQL restriction)
2. DBAPI's `_update_secondary_values()` tries to UPDATE them
3. Previous implementation silently ignored these errors (NO FALLBACK violation)

### Solution Implemented
Switched from GENERATED columns to regular columns with explicit updates:

#### 1. Schema Changes (schema.py)
- Removed GENERATED ALWAYS AS syntax
- Created regular columns for all secondary fields
- These columns are now updatable by DBAPI

#### 2. Update Method Implementation (postgresqlenhanced.py)
- Properly implemented `_update_secondary_values()` method
- Extracts values from JSONB and updates secondary columns
- Uses PostgreSQL's JSONB operators for extraction
- Handles both standard fields and derived fields (given_name, surname)

#### 3. Error Handling Fix (connection.py)
- Removed silent error suppression for GENERATED column errors
- All errors now properly propagate (NO FALLBACK compliant)
- Maintains transaction rollback on errors

### Technical Details
The new approach:
1. Data is stored in `json_data` JSONB column (source of truth)
2. Secondary columns exist as regular columns
3. `_update_secondary_values()` extracts from JSONB and updates secondary columns
4. No silent failures - all errors are reported

### Files Modified
- `schema.py`: Changed from GENERATED to regular columns
- `postgresqlenhanced.py`: Implemented proper `_update_secondary_values()`
- `connection.py`: Removed silent error handling

### Compliance Status
✅ NO FALLBACK POLICY: Now fully compliant
- No silent error suppression
- Explicit error propagation
- Clear failure modes

### Next Steps
1. Test person creation in Gramps
2. Verify secondary columns are properly populated
3. Monitor for any new errors
4. Consider performance implications of explicit updates

### Trade-offs
- **Pro**: Works with existing DBAPI expectations
- **Pro**: NO FALLBACK compliant
- **Con**: Data duplication between JSONB and secondary columns
- **Con**: Potential sync issues if updates fail partially

This implementation prioritizes compatibility and policy compliance over architectural purity.