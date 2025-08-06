# Linux Setup Guide - Gramps PostgreSQL Enhanced

This guide helps Linux users set up the PostgreSQL Enhanced addon for Gramps.

## Prerequisites

### 1. Install PostgreSQL (15 or newer)

**Ubuntu/Debian:**
```bash
# Add PostgreSQL APT repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL
sudo apt install postgresql-15 postgresql-client-15
```

**Fedora/RHEL/CentOS:**
```bash
# Install PostgreSQL
sudo dnf install postgresql15-server postgresql15
sudo postgresql-15-setup --initdb
sudo systemctl enable --now postgresql-15
```

**Arch Linux:**
```bash
sudo pacman -S postgresql
sudo -u postgres initdb -D /var/lib/postgres/data
sudo systemctl enable --now postgresql
```

**openSUSE:**
```bash
sudo zypper install postgresql15-server
sudo systemctl enable --now postgresql
```

### 2. Install Python Dependencies

```bash
# Install pip if needed
sudo apt install python3-pip  # Debian/Ubuntu
sudo dnf install python3-pip  # Fedora
sudo pacman -S python-pip     # Arch

# Install psycopg
pip3 install --user psycopg[binary]
```

### 3. Install Gramps

**From Distribution Packages:**
```bash
# Debian/Ubuntu
sudo apt install gramps

# Fedora
sudo dnf install gramps

# Arch
sudo pacman -S gramps

# openSUSE
sudo zypper install gramps
```

**From Flatpak (Universal):**
```bash
flatpak install flathub org.gramps_project.Gramps
```

## PostgreSQL Setup

### 1. Create Database User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create user and grant permissions
CREATE USER gramps_user WITH PASSWORD 'your_password_here';
ALTER USER gramps_user CREATEDB;
\q
```

### 2. Configure Authentication

Edit PostgreSQL configuration:
```bash
# Find the config file location
sudo -u postgres psql -c "SHOW hba_file;"

# Edit pg_hba.conf (adjust path as needed)
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Add or modify this line:
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all            gramps_user                             scram-sha-256
host    all            gramps_user     127.0.0.1/32           scram-sha-256
host    all            gramps_user     ::1/128                scram-sha-256
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 3. Create Extensions (Optional but Recommended)

```bash
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS btree_gin;"
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS intarray;"
```

## Install the Addon

### 1. Download the Addon

```bash
# Create plugins directory if it doesn't exist
mkdir -p ~/.gramps/gramps51/plugins/

# Download latest release
cd ~/.gramps/gramps51/plugins/
wget https://github.com/glamberson/gramps-postgresql-enhanced/releases/latest/download/postgresqlenhanced.zip
unzip postgresqlenhanced.zip
rm postgresqlenhanced.zip
```

### 2. Create Connection Configuration

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

### 3. Set Permissions

```bash
# Ensure plugin has correct permissions
chmod -R 755 ~/.gramps/gramps51/plugins/postgresqlenhanced/
```

## Using the Addon

### 1. Launch Gramps

```bash
# From terminal
gramps

# With debug mode
GRAMPS_POSTGRESQL_DEBUG=1 gramps

# Or create an alias
echo 'alias gramps-debug="GRAMPS_POSTGRESQL_DEBUG=1 gramps"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Create a New Family Tree

1. Family Trees → Manage Family Trees
2. Click "New"
3. Choose "PostgreSQL Enhanced" as database backend
4. Browse to your `connection.txt` file
5. Enter tree name
6. Click "Load Family Tree"

## Performance Optimization

### PostgreSQL Tuning

Edit PostgreSQL configuration:
```bash
# Find config file
sudo -u postgres psql -c "SHOW config_file;"

# Edit configuration
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Recommended settings for 8GB RAM system:
```ini
# Memory
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 512MB

# Checkpoint
checkpoint_completion_target = 0.9
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB

# Query Planning
random_page_cost = 1.1  # for SSD
effective_io_concurrency = 200  # for SSD
```

Apply changes:
```bash
sudo systemctl restart postgresql
```

### System Optimization

1. **Increase File Limits:**
   ```bash
   # Edit limits
   sudo nano /etc/security/limits.conf
   
   # Add:
   gramps_user soft nofile 65536
   gramps_user hard nofile 65536
   ```

2. **Tune Kernel Parameters:**
   ```bash
   # Edit sysctl
   sudo nano /etc/sysctl.conf
   
   # Add:
   vm.swappiness = 10
   vm.dirty_ratio = 15
   vm.dirty_background_ratio = 5
   
   # Apply
   sudo sysctl -p
   ```

## Network Setup

For remote access:

1. Edit `postgresql.conf`:
   ```ini
   listen_addresses = '*'  # or specific IP
   ```

2. Update firewall:
   ```bash
   # UFW (Ubuntu)
   sudo ufw allow 5432/tcp
   
   # firewalld (Fedora)
   sudo firewall-cmd --permanent --add-port=5432/tcp
   sudo firewall-cmd --reload
   
   # iptables
   sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT
   ```

## Distribution-Specific Notes

### Ubuntu/Debian
- PostgreSQL runs as `postgres` user
- Config files in `/etc/postgresql/15/main/`
- Data directory: `/var/lib/postgresql/15/main/`

### Fedora/RHEL
- SELinux may require adjustment:
  ```bash
  sudo setsebool -P httpd_can_network_connect_db on
  ```

### Arch Linux
- Use systemd for service management
- AUR has additional PostgreSQL extensions

### Using with Flatpak Gramps
Special configuration needed:
```bash
# Allow Flatpak access to config
flatpak override --user --filesystem=~/Documents/GrampsConfig:ro org.gramps_project.Gramps
```

## Troubleshooting

### "psycopg not found"

Ensure Python path includes user packages:
```bash
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="$HOME/.local/lib/python3.x/site-packages:$PYTHONPATH"
```

### "Connection refused"

Check PostgreSQL status:
```bash
sudo systemctl status postgresql
sudo journalctl -u postgresql -n 50
```

### SELinux Issues (Fedora/RHEL)

Check for denials:
```bash
sudo ausearch -m avc -ts recent
sudo grep postgres /var/log/audit/audit.log
```

### Permission Denied

Check file ownership:
```bash
ls -la ~/.gramps/gramps51/plugins/
sudo chown -R $USER:$USER ~/.gramps/
```

## Backup and Restore

### Automated Backups

Create backup script:
```bash
#!/bin/bash
# ~/bin/backup-gramps.sh
BACKUP_DIR="$HOME/GrampsBackups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
pg_dump -h localhost -U gramps_user -d your_tree_name | gzip > "$BACKUP_DIR/gramps_$DATE.sql.gz"

# Keep only last 7 days
find "$BACKUP_DIR" -name "gramps_*.sql.gz" -mtime +7 -delete
```

Add to cron:
```bash
crontab -e
# Add: 0 2 * * * ~/bin/backup-gramps.sh
```

### Manual Backup/Restore

```bash
# Backup
pg_dump -h localhost -U gramps_user -d your_tree_name > backup.sql

# Restore
createdb -h localhost -U gramps_user new_tree_name
psql -h localhost -U gramps_user -d new_tree_name < backup.sql
```

## Getting Help

- Check logs: `sudo journalctl -u postgresql -f`
- Enable debug: `export GRAMPS_POSTGRESQL_DEBUG=1`
- PostgreSQL logs: `/var/log/postgresql/`
- Report issues: https://github.com/glamberson/gramps-postgresql-enhanced/issues

The PostgreSQL Enhanced addon works excellently on Linux with native package management!