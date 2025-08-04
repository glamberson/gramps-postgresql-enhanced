# Testing Guide for PostgreSQL Enhanced Addon

This guide provides step-by-step instructions for testing the PostgreSQL Enhanced addon with Gramps.

## Prerequisites

1. **PostgreSQL Database**: Ensure you have PostgreSQL installed and running
2. **Test Database**: Create a test database with the required extensions
3. **Gramps 6.0+**: Install Gramps 6.0.3 or higher
4. **psycopg 3.1+**: Install the PostgreSQL adapter

## Quick Test Setup

### 1. Database Setup

```bash
# Create test database and user
sudo -u postgres psql <<EOF
CREATE USER gramps_test WITH PASSWORD 'GrampsTest2025';
CREATE DATABASE gramps_test_db OWNER gramps_test;
\c gramps_test_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
GRANT ALL ON DATABASE gramps_test_db TO gramps_test;
EOF
```

### 2. Install psycopg3

```bash
pip install 'psycopg[binary]>=3.1'
```

### 3. Install the Addon

```bash
# Ensure addon is in the correct location
ls -la ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/

# If not installed, create a symlink to your development directory
ln -s /home/greg/gramps-postgresql-enhanced ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced
```

## GUI Testing Steps

### 1. Start Gramps

```bash
# If using system-installed Gramps
gramps

# If running from source (e.g., /home/greg/genealogy-ai/gramps-project-gramps-e960164)
cd /home/greg/genealogy-ai/gramps-project-gramps-e960164
python3 -m gramps
```

### 2. Verify Addon is Loaded

1. Go to **Tools** → **Plugin Manager**
2. Click on **Loaded Plugins** tab
3. Look for "PostgreSQL Enhanced" in the list
4. Status should show as "Loaded"

### 3. Create Test Family Tree

1. Go to **File** → **Family Trees**
2. Click **New**
3. Enter details:
   - **Name**: "PostgreSQL Test"
   - **Database Type**: Select "PostgreSQL Enhanced" from dropdown
   - **Database Path**: Enter connection string:
     ```
     postgresql://gramps_test:GrampsTest2025@localhost:5432/gramps_test_db
     ```
4. Click **OK**

### 4. Test Basic Operations

1. **Add a Person**:
   - Click the "Add Person" button
   - Enter: First Name: "Test", Last Name: "Person"
   - Add birth date: 1 Jan 1900
   - Click OK

2. **Add a Family**:
   - Click "Families" in sidebar
   - Click "Add Family"
   - Add the test person as a parent
   - Click OK

3. **Save and Close**:
   - File → Close
   - Confirm save if prompted

4. **Reopen and Verify**:
   - File → Family Trees
   - Double-click "PostgreSQL Test"
   - Verify the test person and family are still there

### 5. Test Advanced Features

1. **Test JSONB Queries** (in Python Evaluation Shell):
   ```python
   # Tools → Python Evaluation Window
   db = self.dbstate.db
   
   # Test if enhanced features are available
   if hasattr(db, 'enhanced_queries'):
       print("Enhanced queries available!")
       stats = db.get_statistics()
       print(f"Database contains: {stats}")
   ```

2. **Test Migration** (if you have an existing SQLite tree):
   ```python
   # Check migration capability
   if hasattr(db, 'has_migration_available'):
       print("Migration features available")
   ```

## Command Line Testing

### 1. Basic Connection Test

```bash
cd /home/greg/gramps-postgresql-enhanced
python3 -c "
import psycopg
conn = psycopg.connect('postgresql://gramps_test:GrampsTest2025@localhost:5432/gramps_test_db')
print('Connection successful!')
print(f'Server version: {conn.info.server_version}')
conn.close()
"
```

### 2. Run Verification Script

```bash
cd /home/greg/gramps-postgresql-enhanced
python3 verify_addon.py
```

### 3. Run Unit Tests

```bash
cd /home/greg/gramps-postgresql-enhanced/test
python3 run_tests.py
```

## Performance Testing

### 1. Run Benchmark Script

```bash
# Copy and modify the benchmark script if needed
cd /home/greg/genealogy-ai
python3 benchmark_postgresql_addon.py
```

### 2. Monitor Database Performance

```bash
# Check database size
psql -U gramps_test -d gramps_test_db -c "
SELECT pg_database_size('gramps_test_db') as size_bytes,
       pg_size_pretty(pg_database_size('gramps_test_db')) as size_pretty;"

# Check table statistics
psql -U gramps_test -d gramps_test_db -c "
SELECT schemaname, tablename, n_live_tup as rows
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;"
```

## Troubleshooting

### Common Issues

1. **"PostgreSQL Enhanced" not in dropdown**:
   - Check addon is in correct directory
   - Restart Gramps
   - Check for errors in: `~/.gramps/gramps60/gramps.log`

2. **Connection fails**:
   - Test with psql: `psql -U gramps_test -d gramps_test_db -h localhost`
   - Check pg_hba.conf allows local connections
   - Verify password has no special characters

3. **Import errors**:
   - Ensure psycopg3 is installed: `pip show psycopg`
   - Check Python version: `python3 --version` (must be 3.9+)

### Debug Mode

Run Gramps with debug output:
```bash
GRAMPS_RESOURCES=/home/greg/genealogy-ai/gramps-project-gramps-e960164 \
python3 -m gramps -d plugin 2>&1 | grep -i postgresql
```

## Cleanup

To remove test data:

```bash
# Drop test database
sudo -u postgres dropdb gramps_test_db
sudo -u postgres dropuser gramps_test

# Remove test family tree from Gramps
# (Done through GUI: Family Trees → select test tree → Remove)
```

## Report Issues

If you encounter any issues:

1. Check the Gramps log: `~/.gramps/gramps60/gramps.log`
2. Report at: https://github.com/glamberson/gramps-postgresql-enhanced/issues
3. Include:
   - Gramps version
   - PostgreSQL version
   - Error messages
   - Steps to reproduce