# PostgreSQL Enhanced - Gramps Web Deployment Guide

## Quick Start

PostgreSQL Enhanced now has **full Gramps Web compatibility** with support for both database modes:
- **Monolithic Mode**: All trees in one database (recommended for Henderson project)
- **Separate Mode**: Each tree gets its own database

## Prerequisites

1. PostgreSQL 15+ server running (already at 192.168.10.90)
2. PostgreSQL Enhanced installed in Gramps
3. Gramps Web API installed

## Deployment Steps

### 1. Deploy PostgreSQL Enhanced to Gramps

```bash
# Copy the updated addon to Gramps plugins directory
cp -r /home/greg/gramps-postgresql-enhanced/* \
      /home/greg/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/

# Verify installation
gramps --version
```

### 2. Configure Gramps Web (Native Installation)

Create `~/grampsweb_config.py`:

```python
import os

# Database backend
DATABASE_BACKEND = 'postgresqlenhanced'

# Multi-tree mode
TREE = '*'  # Enable multi-tree mode

# Database mode selection
os.environ['POSTGRESQL_ENHANCED_MODE'] = 'monolithic'  # or 'separate'

# PostgreSQL connection
os.environ['GRAMPSWEB_POSTGRES_HOST'] = '192.168.10.90'
os.environ['GRAMPSWEB_POSTGRES_PORT'] = '5432'
os.environ['GRAMPSWEB_POSTGRES_DB'] = 'henderson_unified'
os.environ['GRAMPSWEB_POSTGRES_USER'] = 'genealogy_user'
os.environ['GRAMPSWEB_POSTGRES_PASSWORD'] = 'GenealogyData2025'

# User authentication database
USER_DB_URI = 'postgresql://genealogy_user:GenealogyData2025@192.168.10.90/henderson_unified'

# Flask configuration
SECRET_KEY = 'change-this-to-random-string-at-least-32-chars'
DEBUG = False

# File storage
MEDIA_BASE_DIR = '/var/lib/grampsweb/media'
SEARCH_INDEX_DIR = '/var/lib/grampsweb/index'
```

### 3. Start Gramps Web API

```bash
# Install Gramps Web API if not already installed
pip install gramps-webapi

# Set configuration
export GRAMPSWEB_CONFIG=~/grampsweb_config.py

# Start the API server
python -m gramps_webapi
```

### 4. Create Initial Tree

```bash
# Via API
curl -X POST http://localhost:5000/api/trees/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Henderson Master Tree"}'

# Or via Python
python3 << EOF
import os
os.environ['POSTGRESQL_ENHANCED_MODE'] = 'monolithic'
from postgresqlenhanced import PostgreSQLEnhanced
tree_id = PostgreSQLEnhanced.create_tree(name="Henderson Master Tree")
print(f"Created tree: {tree_id}")
EOF
```

## Docker Deployment (Alternative)

If you prefer Docker despite your preference for native:

```yaml
version: "3.7"

services:
  grampsweb:
    image: ghcr.io/gramps-project/grampsweb:latest
    restart: unless-stopped
    ports:
      - "5555:5000"
    environment:
      GRAMPSWEB_TREE: "*"
      GRAMPSWEB_NEW_DB_BACKEND: postgresqlenhanced
      POSTGRESQL_ENHANCED_MODE: monolithic
      GRAMPSWEB_POSTGRES_HOST: 192.168.10.90
      GRAMPSWEB_POSTGRES_PORT: 5432
      GRAMPSWEB_POSTGRES_DB: henderson_unified
      GRAMPSWEB_POSTGRES_USER: genealogy_user
      GRAMPSWEB_POSTGRES_PASSWORD: GenealogyData2025
      GRAMPSWEB_USER_DB_URI: postgresql://genealogy_user:GenealogyData2025@192.168.10.90/henderson_unified
      GRAMPSWEB_SECRET_KEY: "change-this-to-random-string"
    volumes:
      - /home/greg/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced:/app/plugins/PostgreSQLEnhanced:ro
      - gramps_media:/app/media

volumes:
  gramps_media:
```

## Henderson Project Specific Setup

### 1. Create Henderson Database

```sql
-- Connect to PostgreSQL
psql -h 192.168.10.90 -U genealogy_user

-- Create the unified database
CREATE DATABASE henderson_unified;

-- Connect to it
\c henderson_unified
```

### 2. Import 400 GEDCOMs

```python
#!/usr/bin/env python3
"""Import Henderson GEDCOMs into monolithic database"""

import os
from pathlib import Path

# Set monolithic mode
os.environ['POSTGRESQL_ENHANCED_MODE'] = 'monolithic'
os.environ['GRAMPSWEB_POSTGRES_DB'] = 'henderson_unified'

from postgresqlenhanced import PostgreSQLEnhanced

gedcom_dir = Path('/path/to/henderson/gedcoms')

for i, gedcom_file in enumerate(gedcom_dir.glob('*.ged'), 1):
    # Create tree with meaningful ID
    tree_id = f"chs_{i:04d}"
    PostgreSQLEnhanced.create_tree(tree_id, name=gedcom_file.stem)
    
    # Import GEDCOM via Gramps
    os.system(f"""
        gramps -C {tree_id} \
            --config=database.backend:postgresqlenhanced \
            --import {gedcom_file}
    """)
    
    print(f"Imported {i}/400: {gedcom_file.name}")
```

### 3. Cross-Tree Analysis

```python
# Direct SQL analysis without Gramps Web
import psycopg

conn = psycopg.connect(
    host='192.168.10.90',
    dbname='henderson_unified',
    user='genealogy_user'
)

# Find all Hendersons across all trees
with conn.cursor() as cur:
    cur.execute("""
        SELECT 
            substring(table_name from 'tree_(.*)_person') as tree_id,
            count(*) as person_count
        FROM information_schema.tables
        WHERE table_name LIKE 'tree_%_person'
        GROUP BY tree_id
    """)
    
    for tree_id, count in cur.fetchall():
        print(f"Tree {tree_id}: {count} persons")
```

## Verification

### Test Gramps Web Compatibility

```bash
# Run the test script
python3 /home/greg/gramps-postgresql-enhanced/test_grampsweb_compat.py

# Expected output:
# Tests Passed: 16/16 (100.0%)
# ✅ PostgreSQL Enhanced is ready for Gramps Web!
```

### Check API Endpoints

```bash
# Get API status
curl http://localhost:5000/api/

# List trees (after authentication)
curl http://localhost:5000/api/trees/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Features Now Available

1. **Full Gramps Web compatibility** - All required methods implemented
2. **Multi-tree support** - create_tree() and list_trees() methods
3. **Environment detection** - Automatically detects Gramps Web
4. **Both database modes** - Monolithic and separate modes work
5. **Media path management** - get_mediapath() and set_mediapath()
6. **Read-only detection** - is_read_only() for permissions

## Troubleshooting

### "Backend not found"
- Ensure `postgresqlenhanced.gpr.py` has `id="postgresqlenhanced"`
- Check that files are in the correct plugin directory

### "Cannot connect to database"
- Verify PostgreSQL is running: `psql -h 192.168.10.90 -U genealogy_user -l`
- Check environment variables are set correctly

### "Methods not found"
- Run test script to verify all methods exist
- Check you're on the `grampsweb-compatibility` branch

## Next Steps

1. **Test with small dataset** first
2. **Import Henderson GEDCOMs** in batches
3. **Monitor performance** with 400 trees
4. **Set up regular backups** of henderson_unified database
5. **Configure user access** in Gramps Web

## Support

- PostgreSQL Enhanced issues: [GitHub](https://github.com/glamberson/gramps-postgresql-enhanced)
- Gramps Web documentation: [grampsweb.org](https://www.grampsweb.org/)
- Henderson project specific: lamberson@yahoo.com