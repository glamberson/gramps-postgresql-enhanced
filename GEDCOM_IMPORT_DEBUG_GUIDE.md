# GEDCOM Import Debug Guide for PostgreSQL Enhanced

## Complete Debug Command for Maximum Logging

Run Gramps with ALL debug loggers enabled:

```bash
gramps \
  --debug=. \
  --debug=.GedcomImport \
  --debug=.libgedcom \
  --debug=.PostgreSQLEnhanced \
  --debug=.PostgreSQLEnhanced.TablePrefixWrapper \
  --debug=database \
  --debug=.clidbman \
  2>&1 | tee gramps_debug_$(date +%Y%m%d_%H%M%S).log
```

## Available Debug Loggers

### Core Database Loggers
- `--debug=.` - Root logger (catches everything)
- `--debug=database` - Database operations
- `--debug=.clidbman` - Database manager operations

### GEDCOM-Specific Loggers
- `--debug=.GedcomImport` - Main GEDCOM import logger
- `--debug=.libgedcom` - GEDCOM library operations

### PostgreSQL Enhanced Loggers
- `--debug=.PostgreSQLEnhanced` - Main addon logger
- `--debug=.PostgreSQLEnhanced.TablePrefixWrapper` - Table prefix operations
- `--debug=.PostgreSQLEnhanced.Schema` - Schema operations
- `--debug=.PostgreSQLEnhanced.Migration` - Migration operations
- `--debug=.PostgreSQLEnhanced.Queries` - Query operations
- `--debug=.PostgreSQLEnhanced.Debug` - Debug utilities
- `--debug=.PostgreSQLEnhanced.TypeValidator` - Type validation
- `--debug=.PostgreSQLEnhanced.TypeSanitizer` - Type sanitization

## Step-by-Step Debug Procedure

### 1. Start Gramps with Full Logging
```bash
# Create debug log directory
mkdir -p ~/gramps_debug_logs

# Start Gramps with all debug options and capture output
gramps \
  --debug=. \
  --debug=.GedcomImport \
  --debug=.libgedcom \
  --debug=.PostgreSQLEnhanced \
  2>&1 | tee ~/gramps_debug_logs/gramps_debug_$(date +%Y%m%d_%H%M%S).log
```

### 2. Monitor Real-Time Logs
In another terminal:
```bash
# Watch the latest log file
tail -f ~/gramps_debug_logs/gramps_debug_*.log | grep -E "ERROR|WARNING|PostgreSQL|GEDCOM"
```

### 3. Database Activity Monitoring
In a third terminal:
```bash
# Monitor PostgreSQL activity
watch -n 1 'PGPASSWORD="GenealogyData2025" psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -c "SELECT pid, state, query FROM pg_stat_activity WHERE usename = '\''genealogy_user'\'' AND state != '\''idle'\'';"'
```

### 4. Enable PostgreSQL Statement Logging (Server-Side)
```bash
# SSH to database server and enable statement logging temporarily
ssh 192.168.10.90 "sudo -u postgres psql -c \"ALTER SYSTEM SET log_statement = 'all';\""
ssh 192.168.10.90 "sudo -u postgres psql -c \"SELECT pg_reload_conf();\""

# View PostgreSQL logs
ssh 192.168.10.90 "sudo tail -f /var/log/postgresql/postgresql-17-main.log"

# After debugging, disable statement logging
ssh 192.168.10.90 "sudo -u postgres psql -c \"ALTER SYSTEM SET log_statement = 'none';\""
ssh 192.168.10.90 "sudo -u postgres psql -c \"SELECT pg_reload_conf();\""
```

## Analyzing GEDCOM Import Errors

### Common Error Patterns to Look For

1. **Type Conversion Errors**
   ```
   grep -E "TypeError|ValueError|cannot convert" gramps_debug_*.log
   ```

2. **SQL Errors**
   ```
   grep -E "psycopg|SQL|syntax error|constraint violation" gramps_debug_*.log
   ```

3. **GEDCOM Parsing Errors**
   ```
   grep -E "GEDCOM|parse|invalid tag|unknown tag" gramps_debug_*.log
   ```

4. **Table Prefix Issues**
   ```
   grep -E "TablePrefix|tree_.*_|table.*not found" gramps_debug_*.log
   ```

## Quick Debug Commands

### Minimal GEDCOM Debug
```bash
gramps --debug=.GedcomImport --debug=.PostgreSQLEnhanced
```

### Database Operations Only
```bash
gramps --debug=database --debug=.PostgreSQLEnhanced
```

### Full Debug with Error Filtering
```bash
gramps --debug=. 2>&1 | grep -E "ERROR|CRITICAL|FAIL" | tee errors.log
```

## Programmatic Logging Enhancement

Add these to postgresqlenhanced.py for more detailed GEDCOM import logging:

```python
# At the top of the file
import logging
LOG = logging.getLogger(".PostgreSQLEnhanced")

# In critical methods, add:
def commit_person(self, person, trans, change_time=None):
    LOG.debug(f"Committing person: {person.handle}, gramps_id: {person.gramps_id}")
    LOG.debug(f"Person data structure: {person.__dict__}")
    # ... rest of method

def _execute_sql(self, sql, params=None):
    LOG.debug(f"Executing SQL: {sql}")
    LOG.debug(f"Parameters: {params}")
    # ... rest of method
```

## Testing Procedure with Debug Logging

1. **Clear Previous Test Data**
   ```bash
   # Remove old debug logs
   rm ~/gramps_debug_logs/*
   
   # Start fresh Gramps with logging
   gramps --debug=. --debug=.GedcomImport --debug=.PostgreSQLEnhanced 2>&1 | tee ~/gramps_debug_logs/test_$(date +%Y%m%d_%H%M%S).log
   ```

2. **In Gramps GUI**
   - Delete any test databases
   - Plugin Manager → Refresh
   - Create new PostgreSQL Enhanced database
   - Import GEDCOM file
   - Note any errors in GUI

3. **Analyze Logs**
   ```bash
   # Extract errors and warnings
   grep -E "ERROR|WARNING" ~/gramps_debug_logs/test_*.log > errors_summary.txt
   
   # Extract GEDCOM-specific issues
   grep -i gedcom ~/gramps_debug_logs/test_*.log > gedcom_issues.txt
   
   # Extract SQL statements
   grep -E "Executing SQL|INSERT|UPDATE|SELECT" ~/gramps_debug_logs/test_*.log > sql_trace.txt
   ```

## Environment Variables for Additional Debug

```bash
# Python warnings
export PYTHONWARNINGS=default

# PostgreSQL client logging
export PGOPTIONS='-c client_min_messages=DEBUG5'

# Gramps specific
export GRAMPS_RESOURCES=/usr/share/gramps
```

## Log File Locations

- **Gramps Debug Logs**: `~/gramps_debug_logs/`
- **PostgreSQL Server Logs**: `/var/log/postgresql/postgresql-17-main.log` (on 192.168.10.90)
- **System Journal**: `journalctl -f -u postgresql`

## Remember

- Always copy postgresqlenhanced.py to plugin directory after changes:
  ```bash
  cp postgresqlenhanced.py ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/
  ```
- Refresh plugins in Gramps after copying
- NO direct database manipulation during GUI testing!