#!/bin/bash
# Simple Test Setup for PostgreSQL Enhanced with psycopg3 ONLY
# No gramps-webapi, no psycopg2 dependencies

set -e

echo "=========================================="
echo "Simple Gramps + PostgreSQL Enhanced Test"
echo "=========================================="

# Configuration
TEST_DIR="$HOME/gramps-psql-test"
VENV_DIR="$TEST_DIR/.venv"
GRAMPS_HOME_DIR="$TEST_DIR/gramps_home"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create test directory
echo "1. Creating test directory: $TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create minimal venv with ONLY psycopg3
echo "2. Creating virtual environment with uv..."
uv venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install ONLY psycopg3 (no psycopg2!)
echo "3. Installing ONLY psycopg3..."
uv pip install "psycopg[binary]>=3.1"

# Create isolated GRAMPSHOME
echo "4. Setting up isolated Gramps home..."
mkdir -p "$GRAMPS_HOME_DIR/gramps60/plugins/PostgreSQLEnhanced"

# Copy PostgreSQL Enhanced plugin
echo "5. Installing PostgreSQL Enhanced plugin..."
PLUGIN_DIR="$GRAMPS_HOME_DIR/gramps60/plugins/PostgreSQLEnhanced"
cp /home/greg/gramps-postgresql-enhanced/*.py "$PLUGIN_DIR/"
cp -r /home/greg/gramps-postgresql-enhanced/po "$PLUGIN_DIR/" 2>/dev/null || true

# Copy required support modules
for module in connection.py schema.py migration.py queries.py schema_columns.py debug_utils.py; do
    if [ -f "/home/greg/gramps-postgresql-enhanced/$module" ]; then
        cp "/home/greg/gramps-postgresql-enhanced/$module" "$PLUGIN_DIR/"
    fi
done

# Create launcher
echo "6. Creating launcher..."
cat > "$TEST_DIR/run-gramps.sh" << 'EOF'
#!/bin/bash
# Run System Gramps with psycopg3 and PostgreSQL Enhanced

TEST_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$TEST_DIR/.venv"
GRAMPS_HOME_DIR="$TEST_DIR/gramps_home"

# Activate venv for psycopg3
source "$VENV_DIR/bin/activate"

# Set isolated Gramps home
export GRAMPSHOME="$GRAMPS_HOME_DIR"

# PostgreSQL Enhanced configuration for monolithic mode
export POSTGRESQL_ENHANCED_MODE="monolithic"
export GRAMPSWEB_POSTGRES_HOST="192.168.10.90"
export GRAMPSWEB_POSTGRES_PORT="5432"
export GRAMPSWEB_POSTGRES_DB="henderson_unified"
export GRAMPSWEB_POSTGRES_USER="genealogy_user"
export GRAMPSWEB_POSTGRES_PASSWORD="GenealogyData2025"

clear
echo "=========================================="
echo "Gramps with PostgreSQL Enhanced"
echo "=========================================="
echo "GRAMPSHOME: $GRAMPSHOME"
echo "psycopg3: $(python -c 'import psycopg; print(psycopg.__version__)')"
echo "Database: PostgreSQL @ 192.168.10.90"
echo "Mode: Monolithic (henderson_unified)"
echo ""
echo "This is completely isolated from ~/.gramps/"
echo ""
echo "To create a new tree:"
echo "1. Family Trees -> Manage Family Trees"
echo "2. New -> Enter a name"
echo "3. Database Backend: PostgreSQL Enhanced"
echo ""

# Run system Gramps with our psycopg3
gramps "$@"
EOF

chmod +x "$TEST_DIR/run-gramps.sh"

# Create test script
echo "7. Creating test script..."
cat > "$TEST_DIR/test-connection.sh" << 'EOF'
#!/bin/bash
# Test PostgreSQL connection with psycopg3

TEST_DIR="$(dirname "$(readlink -f "$0")")"
source "$TEST_DIR/.venv/bin/activate"

echo "Testing PostgreSQL Enhanced Setup"
echo "=================================="
echo ""

# Test psycopg3
echo "1. psycopg3 version:"
python -c "import psycopg; print(f'   psycopg3 {psycopg.__version__} ✓')" || echo "   psycopg3 NOT FOUND ✗"
echo ""

# Test connection
echo "2. PostgreSQL connection test:"
python << PYTEST
import psycopg
try:
    conn = psycopg.connect(
        host='192.168.10.90',
        port=5432,
        user='genealogy_user',
        password='GenealogyData2025',
        dbname='postgres',
        connect_timeout=3
    )
    print("   Connection successful ✓")
    
    # Check if henderson_unified exists
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'henderson_unified'")
        if cur.fetchone():
            print("   Database 'henderson_unified' exists ✓")
        else:
            print("   Database 'henderson_unified' does not exist (will be created)")
    
    conn.close()
except Exception as e:
    print(f"   Connection failed: {e} ✗")
PYTEST
echo ""

# Check plugin
echo "3. PostgreSQL Enhanced plugin:"
if [ -f "$TEST_DIR/gramps_home/gramps60/plugins/PostgreSQLEnhanced/postgresqlenhanced.py" ]; then
    echo "   Plugin installed ✓"
    echo "   Version: $(grep 'version=' "$TEST_DIR/gramps_home/gramps60/plugins/PostgreSQLEnhanced/postgresqlenhanced.gpr.py" | cut -d'"' -f2)"
else
    echo "   Plugin NOT FOUND ✗"
fi
echo ""

# Test Gramps Web compatibility
echo "4. Gramps Web compatibility:"
python << PYTEST
import sys
sys.path.insert(0, '$TEST_DIR/gramps_home/gramps60/plugins/PostgreSQLEnhanced')
try:
    from postgresqlenhanced import PostgreSQLEnhanced
    required = ['get_dbid', 'get_dbname', 'get_summary', 'create_tree', 'list_trees']
    missing = []
    for method in required:
        if not hasattr(PostgreSQLEnhanced, method):
            missing.append(method)
    
    if missing:
        print(f"   Missing methods: {', '.join(missing)} ✗")
    else:
        print("   All required methods present ✓")
except Exception as e:
    print(f"   Could not load plugin: {e} ✗")
PYTEST
echo ""
echo "Test complete!"
EOF

chmod +x "$TEST_DIR/test-connection.sh"

# Create database setup script
echo "8. Creating database setup script..."
cat > "$TEST_DIR/setup-database.sh" << 'EOF'
#!/bin/bash
# Create henderson_unified database if needed

TEST_DIR="$(dirname "$(readlink -f "$0")")"
source "$TEST_DIR/.venv/bin/activate"

echo "Setting up PostgreSQL database..."
python << PYSETUP
import psycopg

try:
    # Connect to postgres database
    conn = psycopg.connect(
        host='192.168.10.90',
        port=5432,
        user='genealogy_user',
        password='GenealogyData2025',
        dbname='postgres',
        autocommit=True
    )
    
    with conn.cursor() as cur:
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'henderson_unified'")
        if not cur.fetchone():
            print("Creating database 'henderson_unified'...")
            cur.execute("CREATE DATABASE henderson_unified")
            print("Database created successfully!")
        else:
            print("Database 'henderson_unified' already exists.")
    
    conn.close()
    
    # Test connection to the new database
    conn = psycopg.connect(
        host='192.168.10.90',
        port=5432,
        user='genealogy_user',
        password='GenealogyData2025',
        dbname='henderson_unified'
    )
    print("Successfully connected to henderson_unified")
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    exit(1)
PYSETUP
EOF

chmod +x "$TEST_DIR/setup-database.sh"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Installation location: $TEST_DIR"
echo ""
echo "Next steps:"
echo "1. Test the setup:     $TEST_DIR/test-connection.sh"
echo "2. Setup database:     $TEST_DIR/setup-database.sh"
echo "3. Run Gramps:         $TEST_DIR/run-gramps.sh"
echo ""
echo "This setup uses:"
echo "  • psycopg3 ONLY (no psycopg2!)"
echo "  • PostgreSQL Enhanced with Gramps Web compatibility"
echo "  • Isolated data directory"
echo "  • System Gramps 6.0.1"
echo ""
echo "NO gramps-webapi installed (it requires psycopg2)"
echo "We'll handle Gramps Web differently later."