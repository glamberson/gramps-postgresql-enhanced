# Answers to Your Configuration Questions

## 1. How GUI Database Configuration Works

### Current Implementation
- The GUI doesn't pass database configuration parameters to the PostgreSQL addon
- When you create a tree through GUI, it only passes the directory path
- The addon ALWAYS reads from `connection_info.txt` for actual database credentials

### Monolithic Mode (current)
- Reads: `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt`
- All trees use same PostgreSQL database with prefixes: `tree_<id>_*`
- GUI username/password fields are ignored

### Separate Mode (to be tested)
- Would read: `~/.local/share/gramps/grampsdb/<tree_id>/connection_info.txt`
- Each tree gets its own PostgreSQL database
- Still needs config file - GUI params insufficient

## 2. Configuration File Documentation

The config file system works as follows:

**Priority Order**:
1. Central plugin config (monolithic mode)
2. Per-tree config (separate mode)  
3. Hardcoded defaults

**File Format**: Simple key=value pairs
```
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = monolithic
shared_database_name = gramps_monolithic
```

**Key Finding**: The GUI connection dialog fields are NOT used by the addon!

## 3. Adding Existing Database Trees

### The Problem
When you delete a tree from Gramps, it only removes the registration in `~/.local/share/gramps/grampsdb/`, not the PostgreSQL tables. Your 86k import (tree_68932301) was orphaned this way.

### The Solution
I created `register_existing_tree.sh` which:
1. Creates the registration directory
2. Marks it as postgresqlenhanced 
3. Sets the tree name
4. Shows statistics

### Usage
```bash
./register_existing_tree.sh 68932301 "Ancestry 86k Import"
```

**Result**: Your 86k person tree is now registered and will appear in Gramps!

## 4. Switching to Standalone Mode

To switch from monolithic to separate mode:

### Step 1: Export Current Trees
```bash
# In Gramps, for each tree you want to keep:
# Family Trees -> Export -> GEDCOM
```

### Step 2: Change Configuration
Edit `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt`:
```
database_mode = separate  # Changed from 'monolithic'
# shared_database_name line becomes ignored
```

### Step 3: Create New Trees
- Each new tree will create its own PostgreSQL database
- Database name will be: `gramps_<tree_id>`
- User needs CREATE DATABASE privilege

### Step 4: Import GEDCOMs
- Import your exported data into the new separate databases

## Key Discoveries

1. **GUI fields don't work** - Must use config file
2. **Trees can be orphaned** - Delete from Gramps doesn't drop tables
3. **Registration is simple** - Just two text files in a directory
4. **Config is centralized** - One file controls all trees in monolithic mode

## Recommendations

1. **Keep using config file** - It's more reliable than GUI
2. **Document orphaned trees** - They're a feature (data safety) not a bug
3. **Test separate mode carefully** - Needs CREATE DATABASE privilege
4. **Consider discovery tool** - Could scan for orphaned trees

## Current Status

- ✅ Monolithic mode working perfectly
- ✅ Can register orphaned trees
- ✅ Config file system understood
- ⏳ Separate mode needs testing
- ❌ GUI configuration non-functional (by design?)