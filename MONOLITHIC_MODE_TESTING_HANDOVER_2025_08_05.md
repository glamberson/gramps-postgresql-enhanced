# PostgreSQL Enhanced Monolithic Mode Testing - Complete Handover
## Date: 2025-08-05
## Context: Rigorous testing needed for monolithic database mode

### 🎯 Executive Summary

The gramps-postgresql-enhanced plugin supports two database modes:
1. **Separate mode** (tested ✅) - Each family tree gets its own PostgreSQL database
2. **Monolithic mode** (untested ❌) - All family trees share one database using table prefixes

This handover provides everything needed to rigorously test monolithic mode to the same standard as separate mode.

### 📚 Required Reading

Before starting testing, review these key documents in order:

1. **`/home/greg/gramps-postgresql-enhanced/COMPREHENSIVE_HANDOVER_2025_08_04_EVENING.md`**
   - Complete architectural understanding
   - How the plugin works
   - Previous fixes and learnings

2. **`/home/greg/gramps-postgresql-enhanced/NO_FALLBACK_COMPLIANCE_20250804_191740.md`**
   - **CRITICAL**: NO FALLBACK POLICY
   - Plugin must NEVER use SQLite fallback
   - Must fail cleanly if PostgreSQL unavailable

3. **`/home/greg/gramps-postgresql-enhanced/test_database_modes.py`**
   - Original test showing both modes
   - Good for understanding the concept

### 🔧 Environment Configuration

#### PostgreSQL Database
```bash
Host: 192.168.10.90
Port: 5432
User: genealogy_user
Password: GenealogyData2025
Test Database: gramps_monolithic_test
```

#### Gramps Installation
```bash
# System Gramps (v6.0.1)
Location: /usr/lib/python3/dist-packages/gramps/

# Plugin Installation
~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/

# Copy files to plugin directory
cd /home/greg/gramps-postgresql-enhanced
cp *.py ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/
```

#### Repository
```bash
Path: /home/greg/gramps-postgresql-enhanced
GitHub: https://github.com/glamberson/gramps-postgresql-enhanced
```

### 🏗️ How Monolithic Mode Works

1. **Configuration**: Set in `connection_info.txt`:
   ```ini
   database_mode = monolithic
   shared_database_name = gramps_shared
   ```

2. **Table Prefix Generation** (postgresqlenhanced.py, line 298):
   ```python
   self.table_prefix = re.sub(r'[^a-zA-Z0-9_]', '_', tree_name) + "_"
   ```

3. **Example**: Tree "smith_family" creates tables:
   - `smithfamily_person`
   - `smithfamily_family`
   - `smithfamily_event`
   - etc.

4. **Schema Creation**: All tables created with prefix via `PostgreSQLSchema` class

### 📋 Test Files Created

#### 1. `/home/greg/gramps-postgresql-enhanced/test_monolithic_comprehensive.py`
Comprehensive test suite covering:
- Multiple tree creation in one database
- Data isolation verification
- Concurrent access testing
- Full CRUD operations on all object types
- Performance comparison

**Run with:**
```bash
cd /home/greg/gramps-postgresql-enhanced
./test_monolithic_comprehensive.py
```

#### 2. `/home/greg/gramps-postgresql-enhanced/test_table_prefix_mechanism.py`
Focused tests for prefix mechanism:
- Prefix generation for various tree names
- Query modification verification
- SQL injection prevention
- Edge case handling

**Run with:**
```bash
cd /home/greg/gramps-postgresql-enhanced
./test_table_prefix_mechanism.py
```

### ⚠️ Critical Testing Requirements

1. **NO FALLBACK POLICY**:
   - Plugin must NEVER fall back to SQLite
   - All PostgreSQL failures must be explicit
   - Check `_parse_connection_options()` method
   - Verify no SQLite imports or usage

2. **Table Prefix Isolation**:
   - Each tree's data MUST be completely isolated
   - No cross-contamination between prefixes
   - Verify all queries use correct prefix

3. **Gramps UI Testing**:
   - Create multiple trees via UI
   - Verify each tree only sees its own data
   - Test switching between trees
   - Check performance with multiple trees

### 🔍 What to Test

1. **Basic Functionality**:
   ```bash
   # Run automated tests first
   ./test_table_prefix_mechanism.py
   ./test_monolithic_comprehensive.py
   ```

2. **Manual UI Testing**:
   - Start Gramps
   - Create new tree with monolithic config
   - Add people, families, events
   - Create second tree in same database
   - Verify complete isolation

3. **Edge Cases**:
   - Special characters in tree names
   - Very long tree names
   - Concurrent access from multiple Gramps instances
   - Database permissions (no CREATEDB privilege)

### 🐛 Known Issues to Watch For

1. **Query Modification**:
   - All table references must be prefixed
   - JOINs need all tables prefixed
   - Subqueries need careful handling

2. **Transaction Handling**:
   - Undo/redo must work per tree
   - No cross-tree transaction leakage

3. **Performance**:
   - Prefix overhead in queries
   - Index usage with prefixed tables
   - Connection pooling efficiency

### 📊 Expected Test Results

Monolithic mode should:
- ✅ Create all tables with correct prefixes
- ✅ Maintain complete data isolation
- ✅ Handle concurrent access safely
- ✅ Support all Gramps operations
- ✅ Perform acceptably (within 10% of separate mode)
- ✅ NEVER fall back to SQLite

### 🚀 Quick Start Commands

```bash
# 1. Update plugin files
cd /home/greg/gramps-postgresql-enhanced
cp *.py ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/

# 2. Create test config
mkdir ~/gramps_mono_test
cat > ~/gramps_mono_test/connection_info.txt << EOF
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = monolithic
shared_database_name = gramps_monolithic_test
EOF

# 3. Run automated tests
./test_table_prefix_mechanism.py
./test_monolithic_comprehensive.py

# 4. Start Gramps for UI testing
gramps
```

### 📝 Testing Checklist

- [ ] Run test_table_prefix_mechanism.py - all pass
- [ ] Run test_monolithic_comprehensive.py - all pass
- [ ] Create 3+ trees via Gramps UI
- [ ] Verify data isolation in UI
- [ ] Test GEDCOM import/export
- [ ] Check performance metrics
- [ ] Verify NO SQLite fallback
- [ ] Test with restricted DB user (no CREATEDB)
- [ ] Document any issues found

### 🎯 Success Criteria

Monolithic mode is ready when:
1. All automated tests pass
2. UI testing shows complete isolation
3. Performance is acceptable
4. NO FALLBACK to SQLite ever occurs
5. Works with restricted database permissions

### 📞 Contact

Repository: https://github.com/glamberson/gramps-postgresql-enhanced
Author: Greg Lamberson <lamberson@yahoo.com>

---

## Key Code Locations

### Monolithic Mode Implementation
- `postgresqlenhanced.py:285-300` - Mode detection and prefix generation
- `schema.py:84-99` - Table prefix support in schema
- `connection.py` - Query execution (needs prefix injection)

### Configuration Loading
- `postgresqlenhanced.py:_load_connection_config()` - Reads connection_info.txt
- `postgresqlenhanced.py:_initialize()` - Sets up connection based on mode

### Critical Methods to Review
- `_table_name()` - Adds prefix to table names
- `_update_secondary_values()` - Override to prevent duplicate data
- All query construction in `queries.py`

This handover contains everything needed to complete rigorous testing of monolithic mode. The emphasis is on maintaining the NO FALLBACK policy while ensuring complete data isolation between family trees sharing a database.