# Installation Guide

## Quick Start

### 1. Install PostgreSQL (15 or higher)
```bash
# Ubuntu/Debian
sudo apt install postgresql-15 postgresql-contrib-15

# macOS
brew install postgresql@15

# Windows: Download from postgresql.org
```

### 2. Install Python Dependencies

**Linux/macOS:**
```bash
pip install 'psycopg[binary]>=3.1'
```

**Windows AIO (IMPORTANT):**

Gramps AIO includes its own Python. Do NOT use system pip!

1. Open Command Prompt as Administrator
2. Navigate to Gramps Python directory:
   ```cmd
   cd "C:\Program Files\GrampsAIO64-6.0.6\bin"
   ```
3. Install using Gramps' Python:
   ```cmd
   python.exe -m pip install "psycopg[binary]>=3.1"
   ```
4. Verify installation:
   ```cmd
   python.exe -c "import psycopg; print(psycopg.__version__)"
   ```

**Flatpak:**
```bash
flatpak run --command=sh org.gramps_project.Gramps
pip3 install --user 'psycopg[binary]>=3.1'
exit
```

### 3. Setup PostgreSQL User
```bash
sudo -u postgres createuser -P genealogy_user
sudo -u postgres psql -c "ALTER USER genealogy_user CREATEDB;"
```

### 4. Configure Connection

Create `connection_info.txt` in the **plugin directory** (not tree directory):

**Linux:**
`~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt`

**Windows:**
`C:\Users\USERNAME\AppData\Roaming\gramps\gramps60\plugins\PostgreSQLEnhanced\connection_info.txt`

**Content:**
```ini
host = localhost
port = 5432
user = genealogy_user
password = YourPassword
database_mode = monolithic
shared_database_name = gramps_monolithic
```

**Note**: Monolithic mode requires the config in the plugin directory so all trees can share the same database connection.

### 5. Install in Gramps
1. Copy this folder to: `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/`
2. Restart Gramps
3. Create new tree with "PostgreSQL Enhanced" backend

## Troubleshooting

### Plugin doesn't appear in Gramps

Check psycopg is installed in the **correct** Python:

**Windows AIO:**
```cmd
"C:\Program Files\GrampsAIO64-6.0.6\bin\python.exe" -c "import psycopg; print(psycopg.__version__)"
```

**Linux:**
```bash
python3 -c "import psycopg; print(psycopg.__version__)"
```

If not found, see Step 2 above for platform-specific installation.

### Connection fails or uses wrong host/port

**Check config file location:**
- Monolithic mode: Config must be in PLUGIN directory (see Step 4)
- Separate mode: Config must be in PLUGIN directory (per-tree not yet supported)

**Enable debug logging:**

Linux/macOS:
```bash
export GRAMPS_POSTGRESQL_DEBUG=1
gramps
# Check: ~/.gramps/postgresql_enhanced_debug.log
```

Windows:
```cmd
set GRAMPS_POSTGRESQL_DEBUG=1
"C:\Program Files\GrampsAIO64-6.0.6\gramps.exe"
REM Check: C:\Users\USERNAME\.gramps\postgresql_enhanced_debug.log
```

### Database doesn't exist

Ensure PostgreSQL user has CREATEDB privilege:
```sql
ALTER USER genealogy_user CREATEDB;
```

## Support

- GitHub Issues: https://github.com/glamberson/gramps-postgresql-enhanced/issues
- Gramps Discourse: https://gramps.discourse.group/