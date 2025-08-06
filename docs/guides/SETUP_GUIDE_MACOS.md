# macOS Setup Guide - Gramps PostgreSQL Enhanced

This guide helps macOS users set up the PostgreSQL Enhanced addon for Gramps.

## Prerequisites

### 1. Install PostgreSQL (15 or newer)

**Option A: Postgres.app (Easiest)**
1. Download from: https://postgresapp.com/
2. Drag to Applications folder
3. Launch Postgres.app
4. Click "Initialize" to create a new server
5. Note the port (usually 5432)

**Option B: Homebrew**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15
```

**Option C: MacPorts**
```bash
sudo port install postgresql15-server
sudo port load postgresql15-server
```

### 2. Install Python Dependencies

```bash
# Ensure pip is up to date
python3 -m pip install --upgrade pip

# Install psycopg
python3 -m pip install psycopg[binary]
```

### 3. Install Gramps

**Option A: DMG Package**
Download from: https://gramps-project.org/

**Option B: MacPorts**
```bash
sudo port install gramps5
```

## PostgreSQL Setup

### 1. Create Database User

Using Postgres.app:
1. Click the elephant icon in menu bar
2. Select "Open psql"

Or use Terminal:
```bash
psql -U postgres
```

Then create user:
```sql
CREATE USER gramps_user WITH PASSWORD 'your_password_here';
ALTER USER gramps_user CREATEDB;
\q
```

### 2. Create Extensions (Optional but Recommended)

```bash
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS btree_gin;"
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS intarray;"
```

## Install the Addon

### 1. Download the Addon

```bash
# Using curl
curl -L https://github.com/glamberson/gramps-postgresql-enhanced/releases/latest/download/postgresqlenhanced.zip -o postgresqlenhanced.zip

# Or using wget
wget https://github.com/glamberson/gramps-postgresql-enhanced/releases/latest/download/postgresqlenhanced.zip
```

### 2. Install in Gramps

Find your Gramps plugin directory:
```bash
# Usually one of these:
~/Library/Application Support/gramps/gramps51/plugins/
~/.gramps/gramps51/plugins/
```

Extract the addon:
```bash
cd ~/Library/Application\ Support/gramps/gramps51/plugins/
unzip ~/Downloads/postgresqlenhanced.zip
```

### 3. Create Connection Configuration

```bash
# Create config directory
mkdir -p ~/Documents/GrampsConfig

# Create connection file
cat > ~/Documents/GrampsConfig/connection.txt << 'EOF'
# PostgreSQL Connection Configuration
host = localhost
port = 5432
user = gramps_user
password = your_password_here
database_mode = separate
EOF

# Secure the file
chmod 600 ~/Documents/GrampsConfig/connection.txt
```

## Using the Addon

### 1. Create a New Family Tree

1. Launch Gramps
2. Family Trees → Manage Family Trees
3. Click "New"
4. Choose "PostgreSQL Enhanced" as database backend
5. Browse to your `connection.txt` file
6. Enter tree name
7. Click "Load Family Tree"

### 2. Enable Debug Mode (Optional)

For troubleshooting:
```bash
export GRAMPS_POSTGRESQL_DEBUG=1
export GRAMPS_POSTGRESQL_SLOW_QUERY=0.1
gramps
```

Or create a launch script:
```bash
#!/bin/bash
export GRAMPS_POSTGRESQL_DEBUG=1
/Applications/Gramps.app/Contents/MacOS/Gramps
```

## Performance Optimization

### PostgreSQL Tuning

Edit PostgreSQL configuration:
```bash
# Find config file
psql -U postgres -c "SHOW config_file;"

# Edit with your preferred editor
nano /usr/local/var/postgresql@15/postgresql.conf
```

Recommended settings:
```ini
# Memory (adjust based on your Mac's RAM)
shared_buffers = 512MB          # 25% of RAM for dedicated use
effective_cache_size = 2GB      # 50-75% of RAM
work_mem = 8MB
maintenance_work_mem = 128MB

# SSD optimizations (if applicable)
random_page_cost = 1.1
effective_io_concurrency = 200
```

Restart PostgreSQL:
```bash
brew services restart postgresql@15
# or for Postgres.app: Click elephant → Quit → Relaunch
```

### macOS-Specific Tips

1. **Disable App Nap** for PostgreSQL:
   ```bash
   defaults write -g NSAppSleepDisabled -bool YES
   ```

2. **Increase File Descriptors**:
   ```bash
   sudo launchctl limit maxfiles 65536 200000
   ```

3. **Use Native Architecture**: Ensure you're using arm64 binaries on Apple Silicon

## Network Access

To access PostgreSQL from another computer:

1. Edit `postgresql.conf`:
   ```ini
   listen_addresses = '*'
   ```

2. Edit `pg_hba.conf`:
   ```
   # Allow local network
   host    all    gramps_user    192.168.1.0/24    scram-sha-256
   ```

3. Configure macOS Firewall:
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/opt/postgresql@15/bin/postgres
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/opt/postgresql@15/bin/postgres
   ```

## Troubleshooting

### "psql: command not found"

Add PostgreSQL to PATH:
```bash
# For Postgres.app
echo 'export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"' >> ~/.zshrc

# For Homebrew
echo 'export PATH="/usr/local/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc

source ~/.zshrc
```

### "Connection refused"

Check if PostgreSQL is running:
```bash
# Homebrew
brew services list

# Postgres.app
ps aux | grep postgres
```

### "Library not loaded" errors

Install/reinstall psycopg:
```bash
pip3 uninstall psycopg psycopg-binary
pip3 install psycopg[binary]
```

### Permission Issues

Fix plugin permissions:
```bash
chmod -R 755 ~/Library/Application\ Support/gramps/gramps51/plugins/postgresqlenhanced/
```

## Backup and Restore

### Time Machine

PostgreSQL databases are automatically backed up by Time Machine if using default locations.

### Manual Backup

```bash
# Single database
pg_dump -h localhost -U gramps_user -d your_tree_name > ~/Desktop/tree_backup.sql

# All databases
pg_dumpall -h localhost -U postgres > ~/Desktop/all_gramps_backup.sql
```

### Restore

```bash
# Single database
createdb -h localhost -U gramps_user restored_tree
psql -h localhost -U gramps_user -d restored_tree < ~/Desktop/tree_backup.sql
```

## Upgrading

1. Backup all databases
2. Download new addon version
3. Remove old version:
   ```bash
   rm -rf ~/Library/Application\ Support/gramps/gramps51/plugins/postgresqlenhanced/
   ```
4. Install new version
5. Restart Gramps

## Getting Help

- Enable debug mode for detailed logs
- Check PostgreSQL logs:
  - Homebrew: `/usr/local/var/log/postgresql@15.log`
  - Postgres.app: `~/Library/Application Support/Postgres/var-15/postgresql.log`
- Report issues: https://github.com/glamberson/gramps-postgresql-enhanced/issues

The PostgreSQL Enhanced addon provides excellent performance on macOS, especially on Apple Silicon Macs!