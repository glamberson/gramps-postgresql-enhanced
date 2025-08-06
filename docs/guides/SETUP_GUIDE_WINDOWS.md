# Windows Setup Guide - Gramps PostgreSQL Enhanced

This guide helps Windows users set up the PostgreSQL Enhanced addon for Gramps.

## Prerequisites

### 1. Install PostgreSQL (15 or newer)

**Option A: PostgreSQL Installer (Recommended)**
1. Download from: https://www.postgresql.org/download/windows/
2. Run the installer
3. Remember your postgres password!
4. Default settings are fine
5. Note the port (usually 5432)

**Option B: Via Chocolatey**
```powershell
# Run as Administrator
choco install postgresql15
```

### 2. Install Python Dependencies

Open Command Prompt or PowerShell:
```cmd
pip install psycopg[binary]
```

### 3. Install Gramps

Download and install Gramps 5.1+ from: https://gramps-project.org/

## PostgreSQL Setup

### 1. Create Database User

Open pgAdmin (installed with PostgreSQL) or use psql:

```sql
-- In pgAdmin, open a query window
CREATE USER gramps_user WITH PASSWORD 'your_password_here';
```

### 2. Create Extensions (Optional but Recommended)

```sql
-- Connect to postgres database first
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS intarray;
```

## Install the Addon

### 1. Download the Addon

Download the latest release from:
https://github.com/glamberson/gramps-postgresql-enhanced/releases

### 2. Install in Gramps

1. Open Gramps
2. Go to Edit → Preferences → General
3. Note your "User plugin directory" path
4. Extract the addon ZIP to that directory
5. Restart Gramps

### 3. Create Connection Configuration

Create a file `connection.txt` in your Documents folder:

```ini
# PostgreSQL Connection Configuration
host = localhost
port = 5432
user = gramps_user
password = your_password_here
database_mode = separate
```

**Security Note**: Protect this file! Right-click → Properties → Security → Edit permissions

## Using the Addon

### 1. Create a New Family Tree

1. In Gramps: Family Trees → Manage Family Trees
2. Click "New"
3. Choose "PostgreSQL Enhanced" as the database backend
4. Browse to your `connection.txt` file
5. Enter a name for your tree
6. Click "Load Family Tree"

### 2. Verify It's Working

Check the Gramps status bar - it should show "PostgreSQL Enhanced" as the backend.

### 3. Enable Debug Mode (Optional)

For troubleshooting, set environment variable:
```cmd
set GRAMPS_POSTGRESQL_DEBUG=1
gramps
```

## Performance Tips

### For Best Performance

1. **Use SSD**: Install PostgreSQL on an SSD if possible
2. **Adjust PostgreSQL Memory**: Edit `postgresql.conf`:
   ```
   shared_buffers = 256MB      # 25% of RAM for dedicated server
   work_mem = 4MB
   maintenance_work_mem = 64MB
   ```
3. **Windows Defender**: Add PostgreSQL data directory to exclusions

### Network Setup

If PostgreSQL is on another computer:
1. Edit `postgresql.conf`:
   ```
   listen_addresses = '*'
   ```
2. Edit `pg_hba.conf`:
   ```
   host    all    gramps_user    192.168.1.0/24    scram-sha-256
   ```
3. Restart PostgreSQL service
4. Update `connection.txt` with the server's IP

## Troubleshooting

### "Connection refused"
- Check PostgreSQL service is running: Win+R → `services.msc` → "postgresql-x64-15"
- Check Windows Firewall allows port 5432

### "Authentication failed"  
- Verify username/password in `connection.txt`
- Check quotes around password if it contains special characters

### "Database does not exist"
- The addon creates databases automatically
- Ensure user has CREATEDB privilege:
  ```sql
  ALTER USER gramps_user CREATEDB;
  ```

### Performance Issues
- Enable debug mode to see slow queries
- Check Windows Task Manager for CPU/memory usage
- Consider upgrading PostgreSQL to latest version

## Backup and Restore

### Backup Your Tree

Using pgAdmin:
1. Right-click your database
2. Backup...
3. Choose filename and format

Using command line:
```cmd
pg_dump -h localhost -U gramps_user -d your_tree_name > backup.sql
```

### Restore from Backup

```cmd
psql -h localhost -U gramps_user -d your_tree_name < backup.sql
```

## Upgrading

1. Backup your databases first!
2. Download new addon version
3. Replace files in plugin directory
4. Restart Gramps

## Getting Help

- Check debug output: `GRAMPS_POSTGRESQL_DEBUG=1`
- Review PostgreSQL logs: `C:\Program Files\PostgreSQL\15\data\log\`
- Open issue on GitHub with debug output

Remember: The PostgreSQL Enhanced addon provides 3-10x better performance than SQLite, especially for large family trees!