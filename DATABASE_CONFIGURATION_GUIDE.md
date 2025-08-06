# PostgreSQL Enhanced Database Configuration Guide

## How Gramps Manages PostgreSQL Trees

### Tree Registration
Gramps tracks PostgreSQL family trees in: `~/.local/share/gramps/grampsdb/<tree_id>/`

Each tree directory contains:
- `database.txt` - Contains "postgresqlenhanced" to identify the backend
- `name.txt` - The user-friendly name shown in Gramps

### Configuration File System

#### Central Configuration (Monolithic Mode)
**Location**: `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt`

This file is used when:
- `database_mode = monolithic` 
- All trees share one PostgreSQL database with table prefixes

#### Per-Tree Configuration (Separate Mode) 
**Location**: `~/.local/share/gramps/grampsdb/<tree_id>/connection_info.txt`

This would be used when:
- `database_mode = separate`
- Each tree gets its own PostgreSQL database

### Configuration Priority Order
1. Central plugin config (for monolithic mode)
2. Per-tree config (for separate mode)  
3. Built-in defaults

## GUI Database Creation Process

When creating a new tree through the GUI:

1. **Gramps generates a unique tree ID** (8 character hex string)
2. **Creates directory**: `~/.local/share/gramps/grampsdb/<tree_id>/`
3. **Writes metadata files**:
   - `database.txt` with "postgresqlenhanced"
   - `name.txt` with the user's chosen name
4. **PostgreSQL addon reads central config** from plugin directory
5. **Creates tables with prefix**: `tree_<tree_id>_*` in monolithic mode

## How to Register an Existing Database Tree

If you have a tree in PostgreSQL that Gramps doesn't know about (e.g., tree_68932301):

### Method 1: Manual Registration
```bash
# 1. Create the tree directory
TREE_ID="68932301"
TREE_NAME="My Large Import"
mkdir -p ~/.local/share/gramps/grampsdb/${TREE_ID}

# 2. Register it as PostgreSQL Enhanced
echo "postgresqlenhanced" > ~/.local/share/gramps/grampsdb/${TREE_ID}/database.txt

# 3. Give it a name
echo "${TREE_NAME}" > ~/.local/share/gramps/grampsdb/${TREE_ID}/name.txt

# 4. Restart Gramps - the tree will appear in the Family Tree Manager
```

### Method 2: Database Discovery Tool (Not Yet Implemented)
A future enhancement could scan the PostgreSQL database for unregistered trees and offer to register them.

## Configuration File Format

### connection_info.txt
```ini
# Connection details
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025

# Database mode
database_mode = monolithic    # or 'separate'
shared_database_name = gramps_monolithic

# Optional settings
pool_size = 10
sslmode = prefer
connect_timeout = 10
```

## Switching Between Modes

### From Monolithic to Separate
1. Export tree as GEDCOM
2. Change `database_mode = separate` in config
3. Create new tree (will create separate database)
4. Import GEDCOM

### From Separate to Monolithic  
1. Export tree as GEDCOM
2. Change `database_mode = monolithic` in config
3. Set `shared_database_name` 
4. Create new tree (will use shared database with prefix)
5. Import GEDCOM

## Current Limitations

1. **No GUI configuration** - Must edit connection_info.txt manually
2. **No tree discovery** - Must manually register existing trees
3. **No migration tool** - Must export/import to switch modes
4. **Single config file** - All trees in monolithic mode share same database

## Testing Notes

### What Works
- Monolithic mode with central config file
- Tree creation through GUI (uses central config)
- Manual tree registration

### To Test
- Separate database mode
- Per-tree configuration files
- GUI parameter passing (username/password)
- Mode switching

### Known Issues
- Trees deleted from Gramps remain in PostgreSQL (orphaned)
- No way to discover/register existing trees through GUI
- Config changes require Gramps restart