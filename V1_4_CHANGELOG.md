# PostgreSQL Enhanced v1.4 - Gramps Web Compatibility Release
*Branch: v1.4-grampsweb-compatibility*
*Created: 2025-08-09 00:00*

## Overview
Version 1.4 adds full Gramps Web compatibility while maintaining PostgreSQL-native design principles.

## Key Changes from v1.3

### 1. DBAPI Compatibility Attributes
- [x] Added `db_is_open = True` flag (fixes "0 records" issue)
- [ ] Implement read-only mode support
- [ ] Initialize all bookmark collections (9 types)
- [ ] Load ID counters with mode awareness
- [ ] Load surname list with mode awareness
- [ ] Initialize gender statistics
- [ ] Load all custom type attributes (17 types)
- [ ] Load name formats and researcher info
- [ ] Set proper serializer
- [ ] Add minimal save path
- [ ] Add modified version checking
- [ ] Initialize has_changed counter

### 2. Mode-Aware Metadata Handling
- [ ] Implement `_get_mode_aware_metadata()`
- [ ] Implement `_set_mode_aware_metadata()`
- [ ] Prefix all metadata keys in monolithic mode
- [ ] Isolate surname lists per tree
- [ ] Isolate ID counters per tree

### 3. Recent Files Tracking
- [ ] Implement `_update_recent_files()`
- [ ] Create virtual PostgreSQL paths
- [ ] Update timestamps properly

### 4. Documentation
- [x] Created implementation plan
- [x] Added Sphinx-compatible docstrings
- [ ] Update README
- [ ] Create migration guide from v1.3

## Implementation Status

### Files to Modify
- `postgresqlenhanced.py` - Main implementation
- `RELEASE_NOTES_V1_4.md` - To be created
- `README.md` - Update with v1.4 features

### Testing Checklist
- [ ] Desktop Gramps compatibility maintained
- [ ] Gramps Web returns records (not 0)
- [ ] Monolithic mode - proper tree isolation
- [ ] Separate mode - standard functionality
- [ ] Last Accessed shows timestamp
- [ ] Bookmarks functional
- [ ] Custom types in UI dropdowns
- [ ] GEDCOM import works
- [ ] ID generation works without conflicts

## Branch Management

### Current Branch Structure
```
master                          (v1.2 stable)
├── v1.3-development           (debug changes saved)
    └── v1.4-grampsweb-compatibility  (THIS BRANCH)
```

### Merge Strategy
1. Complete implementation on v1.4 branch
2. Test thoroughly
3. Merge back to v1.3-development when stable
4. Eventually merge to master for release

## Linting/Style Notes
- Manual compliance only (auto-linting breaks code)
- Focus on functionality over style initially
- Document any style decisions
- Consider creating `.pylintrc` with safe rules

## Next Steps
1. Implement the load() method changes from V1_4_FINAL_IMPLEMENTATION
2. Test with Docker container
3. Verify Gramps Web functionality
4. Clean up and document

## Commands for Testing
```bash
# Test with Docker
docker restart grampsweb-postgresql
docker logs grampsweb-postgresql

# Check database
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user \
  -d gramps_monolithic_v13_test -c "SELECT COUNT(*) FROM tree_6894f36d_person;"

# Test API
curl http://localhost:8519/api/trees/
```