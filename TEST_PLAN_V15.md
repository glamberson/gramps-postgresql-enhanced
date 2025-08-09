# PostgreSQL Enhanced v1.5 Comprehensive Test Plan

## Test Environment
- **PostgreSQL Enhanced Version**: 1.5.0
- **GrampsWeb Container**: grampsweb-test (port 8520)
- **Database**: gramps_monolithic_v13_test on 192.168.10.90
- **Tree ID**: 6894f36d (93 Henderson family members)
- **Mode**: Monolithic (multiple trees in single database)

## 1. GrampsWeb UI Tests (http://localhost:8520)

### 1.1 Basic Functionality
- [ ] **Login**: greg/greg should work
- [ ] **Tree Loading**: 93 people should be visible
- [ ] **Person View**: Click on any Henderson family member
  - [ ] All details load correctly
  - [ ] Photos/media display if present
  - [ ] Relationships show correctly
  - [ ] Events display with dates

### 1.2 Data Modification Tests
- [ ] **Edit Person**:
  - [ ] Change a name or date
  - [ ] Save changes
  - [ ] Verify changes persist after refresh
  - [ ] Check no errors in console

- [ ] **Add New Person**:
  - [ ] Create new person with basic details
  - [ ] Save successfully
  - [ ] Person appears in list
  - [ ] Can navigate to new person

### 1.3 Search Functionality
- [ ] **Search for "Henderson"**:
  - [ ] Results should appear (using sifts/SQLite fallback)
  - [ ] Click results to navigate
  
- [ ] **Search for "William"**:
  - [ ] Multiple results expected
  - [ ] All Williams should be found

### 1.4 Transaction History
- [ ] **Check History Tab**:
  - [ ] Should not crash (returns empty list is OK)
  - [ ] No JavaScript errors
  - [ ] UI remains functional

### 1.5 Database Tools
- [ ] **Rebuild Indexes**:
  - [ ] Should complete without errors
  - [ ] Check Docker logs for any issues
  
- [ ] **Check & Repair**:
  - [ ] Should run successfully
  - [ ] No data corruption

### 1.6 Concurrent Access
- [ ] **Open in two browser tabs**:
  - [ ] Edit different people simultaneously
  - [ ] Both saves should work
  - [ ] No "tuple concurrently updated" errors

## 2. Docker Container Logs Check

```bash
# Monitor for errors during testing
docker logs -f grampsweb-test 2>&1 | grep -E "ERROR|WARNING|CRITICAL"
```

### Expected Issues to Watch For:
- [ ] No "AttributeError: 'PostgreSQLEnhanced' object has no attribute"
- [ ] No "tuple concurrently updated" errors
- [ ] No "syntax error at or near $1" (search issue)
- [ ] No "DbGenericUndo object has no attribute 'get_transactions'"

## 3. Database Verification

```bash
# Check PostgreSQL tables
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user \
  -d gramps_monolithic_v13_test -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE 'tree_6894f36d_%'
ORDER BY table_name;"
```

### Tables to Verify:
- [ ] tree_6894f36d_person (should have 93 rows)
- [ ] tree_6894f36d_family
- [ ] tree_6894f36d_event
- [ ] tree_6894f36d_metadata
- [ ] tree_6894f36d_transactions (new - undo system)
- [ ] tree_6894f36d_changes (new - undo system)

## 4. Gramps Desktop GUI Tests

```bash
# Start Gramps with v1.5
cd /home/greg/gramps-postgresql-enhanced
export GRAMPS_POSTGRESQL_DEBUG=1
export POSTGRESQL_ENHANCED_MODE=monolithic
export GRAMPSWEB_POSTGRES_HOST=192.168.10.90
export GRAMPSWEB_POSTGRES_DB=gramps_monolithic_v13_test
export GRAMPSWEB_POSTGRES_USER=genealogy_user
export GRAMPSWEB_POSTGRES_PASSWORD=GenealogyData2025
gramps
```

### 4.1 Tree Management
- [ ] **Open Tree 6894f36d**:
  - [ ] Should load without upgrade prompts
  - [ ] All 93 people visible
  - [ ] No "Last Accessed: NEVER" issue

### 4.2 Data Operations
- [ ] **View People**:
  - [ ] List loads quickly
  - [ ] Sort by name/date works
  - [ ] Filter options work

- [ ] **Edit Person**:
  - [ ] Open edit dialog
  - [ ] Make changes
  - [ ] Save successfully
  - [ ] Changes visible in GrampsWeb too

### 4.3 Database Tools
- [ ] **Tools > Database Processing > Check and Repair**:
  - [ ] Runs without errors
  - [ ] Reports completion

- [ ] **Tools > Database Processing > Rebuild Reference Maps**:
  - [ ] Completes successfully

- [ ] **Tools > Database Processing > Rebuild Secondary Indices**:
  - [ ] Completes successfully

### 4.4 Search
- [ ] **Search for "Henderson"**:
  - [ ] Results appear in search sidebar
  - [ ] Can navigate to results

### 4.5 Import/Export
- [ ] **Export small GEDCOM**:
  - [ ] Select a few families
  - [ ] Export to file
  - [ ] File should be valid GEDCOM

- [ ] **Import GEDCOM**:
  - [ ] Import the exported file
  - [ ] No duplicate key errors
  - [ ] Data imports correctly

## 5. Performance Tests

### 5.1 Response Times
- [ ] Person list loads in < 2 seconds
- [ ] Person details load in < 1 second
- [ ] Search results in < 3 seconds

### 5.2 Memory Usage
- [ ] Monitor container memory during operations
- [ ] Should stay under 1GB for normal operations

## 6. Integration Tests

### 6.1 Data Consistency
- [ ] Changes in Gramps GUI visible in GrampsWeb
- [ ] Changes in GrampsWeb visible in Gramps GUI
- [ ] No data corruption after multiple edits

### 6.2 Undo System
- [ ] Check if undo tables are being populated:
```bash
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user \
  -d gramps_monolithic_v13_test -c "
SELECT COUNT(*) as transaction_count 
FROM tree_6894f36d_transactions;

SELECT COUNT(*) as changes_count 
FROM tree_6894f36d_changes;"
```

## 7. Error Recovery Tests

### 7.1 Connection Loss
- [ ] Disconnect network briefly
- [ ] Reconnect
- [ ] Operations should resume

### 7.2 Container Restart
- [ ] Make edits
- [ ] Restart container
- [ ] Edits should persist
- [ ] No corruption

## 8. Known Issues / Expected Behavior

### Working Features:
- ✅ Basic CRUD operations
- ✅ Monolithic mode with table prefixes
- ✅ GrampsWeb authentication
- ✅ Concurrent update retry logic
- ✅ Public metadata methods
- ✅ Transaction history stub (returns empty)

### Limitations:
- ⚠️ PostgreSQL native search not fully working (uses SQLite fallback)
- ⚠️ Transaction history returns empty (stub implementation)
- ⚠️ Undo/Redo not yet implemented in PostgreSQL tables

## 9. Test Results Summary

### Critical Tests (Must Pass):
- [ ] GrampsWeb loads and authenticates
- [ ] Can view all 93 Henderson family members
- [ ] Can edit and save changes
- [ ] No crashes or critical errors
- [ ] Gramps GUI can open the tree

### Important Tests (Should Pass):
- [ ] Search returns results (even if using fallback)
- [ ] Database tools complete without errors
- [ ] Concurrent edits work
- [ ] Import/Export functions

### Nice to Have (Can Fail):
- [ ] Transaction history shows data
- [ ] PostgreSQL native search works
- [ ] Undo/Redo in Gramps GUI

## Test Execution Log

```
Date: ________________
Tester: ________________
Version: PostgreSQL Enhanced 1.5.0
Container: grampsweb-test
```

### Issues Found:
1. _______________________________
2. _______________________________
3. _______________________________

### Notes:
_____________________________________
_____________________________________
_____________________________________