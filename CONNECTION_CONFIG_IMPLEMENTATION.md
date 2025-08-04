# Connection Configuration Implementation

## What We've Implemented

### 1. Connection Configuration (connection_info.txt)
When creating a new database in Gramps, the addon will:
1. Look for `connection_info.txt` in the database directory
2. If not found, copy `connection_info_template.txt` there
3. Load settings from the file

### 2. Database Modes

#### Separate Database Mode (database_mode = separate)
- Each family tree gets its own PostgreSQL database
- Database name = tree name from Gramps
- Requires user to have CREATEDB privilege
- Automatically creates database if it doesn't exist
- Clean isolation between trees

#### Shared Database Mode (database_mode = shared)  
- All family trees in one PostgreSQL database
- Uses table prefixes (e.g., `smith_family_person`, `smith_family_event`)
- Only requires basic table creation privileges
- Specified by `shared_database_name` in config

### 3. Configuration File Format
```ini
# Connection details
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025

# Database mode: 'separate' or 'shared'
database_mode = separate

# For shared mode
shared_database_name = gramps_shared
```

### 4. How It Works

1. **User creates new family tree in Gramps**
   - Names it "Smith Family"
   - Selects PostgreSQL Enhanced

2. **Addon extracts tree name**
   - From path: `/home/user/.local/share/gramps/grampsdb/smith_family/`
   - Tree name: `smith_family`

3. **Loads connection_info.txt**
   - From: `/home/user/.local/share/gramps/grampsdb/smith_family/connection_info.txt`
   - If missing, creates from template

4. **Based on database_mode:**
   - **separate**: Creates/connects to database `smith_family`
   - **shared**: Connects to `gramps_shared`, uses prefix `smith_family_`

### 5. Benefits
- **Flexibility**: Users choose their preferred approach
- **Compatibility**: Works with limited DB privileges (shared mode)
- **Power**: Full isolation when user has privileges (separate mode)
- **User-friendly**: Auto-creates config template