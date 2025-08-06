# Configuration Switch Log - Monolithic to Separate Mode

## Date: 2025-08-06 17:30 EEST

## Actions Taken

### 1. Backed Up Monolithic Configuration
- **Original**: `connection_info.txt` 
- **Backup**: `connection_info_monolithic_backup.txt`
- **Location**: `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/`

### 2. Created Separate Mode Configuration
- **File**: `connection_info_separate.txt`
- **Key Change**: `database_mode = separate`
- **Removed**: `shared_database_name` line (not used in separate mode)

### 3. Verified Prerequisites
- **User Privileges**: ✅ genealogy_user has CREATE DB privilege
- **Connection**: ✅ Can connect to PostgreSQL server

### 4. Activated Separate Mode
- **Copied**: `connection_info_separate.txt` → `connection_info.txt`
- **Status**: ACTIVE

## What Changes in Separate Mode

### Database Naming
- **Monolithic**: All trees in `gramps_monolithic` with prefixes `tree_<id>_*`
- **Separate**: Each tree creates database `gramps_<tree_id>`

### Table Naming
- **Monolithic**: `tree_68935c66_person`, `tree_68935c66_family`, etc.
- **Separate**: `person`, `family`, etc. (no prefix needed)

### Database Creation
- **Monolithic**: Uses existing `gramps_monolithic` database
- **Separate**: Creates new database for each tree

## Current State

### Existing Trees (in Monolithic Database)
- 12 trees in `gramps_monolithic` database
- Will remain accessible if you switch back to monolithic mode

### Registered Trees in Gramps
1. `689363c4` - "thug" 
2. `68932301` - "Ancestry 86k Import" (just registered)

## Testing Plan for Separate Mode

1. **Create New Tree**
   - Should create database `gramps_<new_tree_id>`
   - Tables should have no prefix

2. **Import Small GEDCOM**
   - Test basic functionality
   - Verify data isolation

3. **Verify Operations**
   - All CRUD operations
   - Reports and tools
   - Export functions

## How to Switch Back to Monolithic

```bash
cd ~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/
cp connection_info_monolithic_backup.txt connection_info.txt
```

## Important Notes

- **Existing monolithic trees are NOT migrated** - they stay in gramps_monolithic
- **New trees will create separate databases**
- **To access old trees, must switch back to monolithic mode**
- **Both modes work, just can't access both simultaneously**

## File Locations

```
~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/
├── connection_info.txt                   # ACTIVE (separate mode)
├── connection_info_monolithic_backup.txt # Backup (monolithic mode)
├── connection_info_separate.txt          # Separate mode template
└── connection_info_template.txt          # Original template
```

## Next Steps

1. **Restart Gramps** to load new configuration
2. **Create test tree** to verify separate mode works
3. **Document any issues** found during testing
4. **Consider migration strategy** for existing trees if needed