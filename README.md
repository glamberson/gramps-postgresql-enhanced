# PostgreSQL Enhanced Database Backend for Gramps

This addon provides an enhanced PostgreSQL database backend for Gramps genealogy software, offering advanced features while maintaining full compatibility with the Gramps data model.

**Project Status:** Active development | [GitHub Repository](https://github.com/glamberson/gramps-postgresql-enhanced) | [Submit Issues](https://github.com/glamberson/gramps-postgresql-enhanced/issues)

## Key Features

- **Modern psycopg3** - Uses the latest PostgreSQL adapter (not psycopg2)
- **Dual Storage** - Both pickle blobs (compatibility) and JSONB (queryability)
- **Advanced Queries** - Recursive CTEs, full-text search, relationship paths
- **Migration Support** - From SQLite and standard PostgreSQL addon
- **Performance** - Optimized for large databases (50,000+ persons)
- **Multi-user Safe** - True concurrent access with proper locking

## Requirements

- Gramps 6.0 or higher (tested with 6.0.3)
- PostgreSQL 15 or higher
- Python 3.9 or higher (as required by Gramps 6.0)
- psycopg 3.1 or higher (NOT psycopg2!)

### PostgreSQL Extensions Required

The following extensions must be installed in your PostgreSQL database:
- `uuid-ossp` - For UUID generation
- `btree_gin` - For improved JSONB indexing
- `pg_trgm` - For fuzzy text matching (optional but recommended)

## Installation

### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

### 2. Install Python Dependencies

```bash
pip install 'psycopg[binary]>=3.1'
```

### 3. Install the Addon

#### Option A: From GitHub Release
```bash
# Download the latest release
wget https://github.com/glamberson/gramps-postgresql-enhanced/releases/latest/download/PostgreSQLEnhanced.addon.tgz

# Install via Gramps
# 1. Open Gramps
# 2. Tools → Plugin Manager
# 3. Install Addon
# 4. Browse to downloaded .addon.tgz file
```

#### Option B: Manual Installation from Source
```bash
# Clone to Gramps addon directory
cd ~/.local/share/gramps/gramps60/plugins/
git clone https://github.com/glamberson/gramps-postgresql-enhanced.git PostgreSQLEnhanced

# Or for system-wide installation:
cd /usr/share/gramps/plugins/
sudo git clone https://github.com/glamberson/gramps-postgresql-enhanced.git PostgreSQLEnhanced
```

#### Option C: Development Installation (for testing)
```bash
# Clone anywhere
git clone https://github.com/glamberson/gramps-postgresql-enhanced.git
cd gramps-postgresql-enhanced

# Create symlink to Gramps plugins directory
ln -s $(pwd) ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced
```

## Setup

### 1. Create PostgreSQL Database

```bash
# Create user and database
sudo -u postgres createuser -P gramps_user
sudo -u postgres createdb -O gramps_user gramps_db

# Grant permissions and install extensions
sudo -u postgres psql -d gramps_db <<EOF
GRANT ALL ON DATABASE gramps_db TO gramps_user;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOF
```

**Important:** When setting the password, avoid special characters like `!` which can cause authentication issues. Use only alphanumeric characters.

### 2. Create Family Tree

1. File → Family Trees
2. New
3. Database Type: "PostgreSQL Enhanced"
4. Connection string options:
   ```
   # URL format (recommended)
   postgresql://gramps_user:password@localhost:5432/gramps_db
   
   # Traditional format
   localhost:5432:gramps_db:public
   
   # Simple format (local only)
   gramps_db
   ```

## Migration

### From SQLite

```python
# In Gramps Python shell (Tools → Python Evaluation)
from gramps.gen.db import DbTxn
db = self.dbstate.db

# Check if migration available
if db.has_migration_available():
    db.migrate_from_sqlite('/path/to/sqlite.db')
```

### From Standard PostgreSQL Addon

The addon automatically detects standard PostgreSQL databases and offers upgrade:

1. Open existing PostgreSQL family tree
2. If prompted, accept upgrade to Enhanced
3. JSONB columns will be added and populated

## Advanced Features

### 1. Relationship Queries

```python
# Find common ancestors
ancestors = db.find_common_ancestors(person1_handle, person2_handle)

# Find relationship path
path = db.find_relationship_path(person1_handle, person2_handle)
```

### 2. Full-Text Search

```python
# Search all text fields
results = db.search_all_text("immigration")
```

### 3. Duplicate Detection

```python
# Find potential duplicates (requires pg_trgm extension)
duplicates = db.enhanced_queries.find_potential_duplicates(threshold=0.8)
```

### 4. Statistics

```python
# Get detailed statistics
stats = db.get_statistics()
```

## Performance Tuning

### PostgreSQL Configuration

Edit `postgresql.conf`:

```ini
# Recommended for genealogy workloads
shared_buffers = 256MB
work_mem = 8MB
maintenance_work_mem = 128MB
effective_cache_size = 2GB

# Enable query optimization
random_page_cost = 1.1  # for SSD storage
```

### Connection Options

```
# Enable connection pooling
postgresql://user:pass@host/db?pool_size=10

# Disable JSONB (blob-only mode)
postgresql://user:pass@host/db?use_jsonb=false
```

## Troubleshooting

### Connection Issues

1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Test connection:
   ```bash
   psql -U gramps_user -d gramps_db -h localhost
   ```

3. Check pg_hba.conf allows connections

### Performance Issues

1. Update statistics:
   ```sql
   ANALYZE;
   ```

2. Check slow queries:
   ```sql
   SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
   ```

### Extension Errors

Some features require PostgreSQL extensions:

```sql
-- For duplicate detection
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- For better performance
CREATE EXTENSION IF NOT EXISTS btree_gin;
```

## Testing the Addon

### Quick Test with Gramps GUI

1. **Start Gramps**:
   ```bash
   gramps
   # Or if running from source:
   python3 -m gramps
   ```

2. **Create Test Database**:
   - File → Family Trees → New
   - Name: "PostgreSQL Test"
   - Database Type: Select "PostgreSQL Enhanced"
   - Connection string: `postgresql://gramps_user:password@localhost:5432/gramps_db`

3. **Verify Installation**:
   - The tree should create successfully
   - Tools → Plugin Manager → Loaded Plugins
   - Look for "PostgreSQL Enhanced" in the list

4. **Test Basic Operations**:
   - Add a test person
   - Add a test family
   - Save and close the tree
   - Reopen to verify data persistence

### Command Line Testing

```bash
# Test connection
python3 -c "import psycopg; print(psycopg.connect('postgresql://gramps_user:password@localhost:5432/gramps_db').info)"

# Run addon verification
cd /path/to/gramps-postgresql-enhanced
python3 verify_addon.py
```

### Performance Testing

```bash
# Run benchmark script (if available)
python3 benchmark_postgresql_addon.py

# Monitor PostgreSQL performance
psql -U gramps_user -d gramps_db -c "SELECT * FROM pg_stat_database WHERE datname='gramps_db';"
```

## Differences from Standard PostgreSQL Addon

| Feature | Standard | Enhanced |
|---------|----------|----------|
| psycopg version | 2 | 3 |
| Storage | Blob only | Blob + JSONB |
| Config | settings.ini | Connection string |
| Queries | Basic | Advanced CTEs |
| Migration | No | Yes |
| Pool support | No | Yes |

## Contributing

Contributions welcome! Please:

1. Follow Gramps coding standards
2. Add tests for new features
3. Update documentation
4. Test with large databases

## License

GNU General Public License v2 or later

## Author

Greg Lamberson <greg@aigenealogyinsights.com>

## See Also

- [Gramps Project](https://gramps-project.org)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg3 Documentation](https://www.psycopg.org/psycopg3/)