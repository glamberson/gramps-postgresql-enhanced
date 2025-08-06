# PostgreSQL Enhanced Addon - Handover Document
## Date: 2025-08-04

### 🎯 Project Overview
The PostgreSQL Enhanced addon for Gramps provides a modern database backend using PostgreSQL with JSONB storage, enabling advanced queries, better performance, and multi-user capabilities.

### 📍 Current State
- **Functionality**: Plugin loads and works with Gramps 6.0.1
- **Database**: Successfully connects to PostgreSQL and creates schema
- **UI Integration**: Full editing capabilities enabled
- **Code Quality**: All verification checks pass

### 🗂️ Repository Structure
```
/home/greg/gramps-postgresql-enhanced/
├── postgresqlenhanced.py      # Main plugin class
├── postgresqlenhanced.gpr.py  # Plugin registration
├── __init__.py                # Package initialization
├── connection.py              # PostgreSQL connection handling
├── schema.py                  # Schema creation and management
├── schema_columns.py          # NEW: Systematic column definitions
├── queries.py                 # Enhanced query capabilities
├── migration.py               # SQLite to PostgreSQL migration
├── MANIFEST                   # Plugin manifest
├── po/                        # Translations
├── test/                      # Unit tests
└── docs/                      # Documentation
```

### 🔧 Development Environment

#### Key Locations
- **Repository**: `/home/greg/gramps-postgresql-enhanced/`
- **Installed Plugin**: `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/`
- **Test Database**: PostgreSQL at 192.168.10.90
  - Database: gramps_test_db
  - User: genealogy_user
  - Password: GenealogyData2025

#### Gramps Installation
- **Version**: 6.0.1 (from Debian apt)
- **Location**: System-wide in `/usr`
- **Command**: `gramps` (working after fixes)

### 📝 Key Technical Decisions

#### 1. **Import Handling**
Problem: Gramps loads plugins differently than normal Python modules
Solution: Try/except block for imports with fallback to absolute imports

#### 2. **Schema Design**
Problem: Gramps expects specific columns that aren't in JSONB
Solution: Systematic GENERATED columns defined in schema_columns.py

#### 3. **Cursor Management**
Problem: DBAPI expects persistent cursor for fetch operations
Solution: Persistent cursor instead of context manager

#### 4. **Connection String**
Problem: Gramps preferences UI doesn't support PostgreSQL connection parameters
Solution: Hardcoded connection string when detecting Gramps file path

### 🚦 Testing Workflow

```bash
# 1. Copy changes to plugin directory
cp /home/greg/gramps-postgresql-enhanced/*.py ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/

# 2. Start Gramps
gramps

# 3. Create new database
- Edit → Preferences → Database backend: PostgreSQL Enhanced
- Family Trees → New
- Should connect to PostgreSQL automatically

# 4. Test functionality
- Add person (right-click → Add Person)
- Import GEDCOM (File → Import)
```

### 🐛 Troubleshooting Guide

#### Plugin Not Loading
1. Check console for import errors
2. Verify psycopg3 is installed: `pip3 show psycopg`
3. Check Plugin Manager for error messages

#### Database Connection Issues
1. Verify PostgreSQL is accessible: `psql -h 192.168.10.90 -U genealogy_user -d gramps_test_db`
2. Check connection string in postgresqlenhanced.py line 226
3. Look for transaction errors in console

#### Missing Column Errors
1. Check schema_columns.py for column definition
2. Drop and recreate tables if schema changed
3. Verify GENERATED column syntax is correct

### 📊 Database Schema

#### Core Design
- Dual storage: blob_data (pickle) + json_data (JSONB)
- GENERATED columns for Gramps compatibility
- GIN indexes for JSONB performance

#### Required Columns (from schema_columns.py)
- person: surname, given_name, gramps_id
- tag: name, gramps_id
- place: enclosed_by, gramps_id
- All tables: gramps_id

### 🔄 Git Workflow

```bash
# Check status
git -C /home/greg/gramps-postgresql-enhanced status

# Add all changes
git -C /home/greg/gramps-postgresql-enhanced add -A

# Commit with detailed message
git -C /home/greg/gramps-postgresql-enhanced commit -m "feat: Major fixes for Gramps 6.0.1 compatibility

- Fix import handling for Gramps plugin environment
- Add systematic schema column generation
- Fix cursor management for DBAPI compatibility
- Add proper plugin methods (load, open, is_open, close)
- Fix logging to use module logger
- Add schema_columns.py for systematic column definitions
- Change audience to EVERYONE for visibility
- Fix email address in registration"

# Push to GitHub
git -C /home/greg/gramps-postgresql-enhanced push
```

### 🚀 Future Enhancements

#### Immediate Priorities
1. **Configuration System**
   - Move hardcoded connection to config file
   - Add UI for connection parameters
   - Support multiple databases

2. **JSONB Features**
   - Expose advanced queries through Gramps filters
   - Add JSON-based export/import
   - Implement full-text search

3. **Multi-User Support**
   - Test concurrent access
   - Add user tracking
   - Implement conflict resolution

#### Advanced Features
1. **Performance Optimization**
   - Materialized views for complex queries
   - Query plan analysis
   - Automatic index recommendations

2. **Migration Tools**
   - Complete SQLite migration
   - Progress reporting
   - Rollback capability

3. **Integration Features**
   - REST API endpoint
   - WebSocket for real-time updates
   - External tool integration

### 📚 Reference Materials

#### Gramps DBAPI
- Source: `/usr/lib/python3/dist-packages/gramps/plugins/db/dbapi/dbapi.py`
- Key methods: load, close, get_summary, readonly property
- Expected columns: Defined in table creation, used in direct SQL

#### PostgreSQL Features
- JSONB: https://www.postgresql.org/docs/current/datatype-json.html
- Generated Columns: https://www.postgresql.org/docs/current/ddl-generated-columns.html
- GIN Indexes: https://www.postgresql.org/docs/current/gin.html

#### Gramps Development
- Wiki: https://gramps-project.org/wiki/index.php/Main_Page
- Addons: https://github.com/gramps-project/addons-source
- GEPS (Enhancement Proposals): https://gramps-project.org/wiki/index.php/GEPS

### ⚠️ Important Notes

1. **psycopg3 vs psycopg2**: We use psycopg3 (modern, async-capable)
2. **Python 3.13**: Current environment, ensure compatibility
3. **Gramps 6.0.1**: Older than latest, some features may differ
4. **Connection Pooling**: Implemented but not fully tested
5. **JSONB Toggle**: use_jsonb flag exists but not fully implemented

### 🔍 Debugging Commands

```bash
# Check installed Gramps version
gramps --version

# List PostgreSQL tables
PGPASSWORD="GenealogyData2025" psql -h 192.168.10.90 -U genealogy_user -d gramps_test_db -c "\dt"

# Check specific table schema
PGPASSWORD="GenealogyData2025" psql -h 192.168.10.90 -U genealogy_user -d gramps_test_db -c "\d person"

# View Gramps debug output
gramps --debug=database

# Check plugin loading
gramps -L | grep PostgreSQL
```

### 📋 Session Context for Next Time

The plugin is now functional but needs:
1. Proper configuration management
2. Full GEDCOM import testing
3. Performance benchmarking
4. Multi-user testing
5. UI for connection settings

All core functionality works: creating databases, adding data, and the schema is systematically handled to avoid missing column errors.

---
*Handover prepared for seamless continuation of development*