#!/bin/bash
# Quick Test Environment with uv
# Uses system Gramps but with uv-managed dependencies and isolated data

set -e

echo "=========================================="
echo "Quick Gramps Test Environment with uv"
echo "=========================================="

# Configuration
TEST_DIR="$HOME/gramps-web-test"
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

# Create minimal venv just for psycopg and gramps-webapi
echo "2. Creating virtual environment with uv..."
uv venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install only the additional packages we need
echo "3. Installing PostgreSQL and Gramps Web packages..."
uv pip install \
    "psycopg[binary]>=3.1" \
    gramps-webapi \
    flask \
    flask-cors

# Create isolated GRAMPSHOME
echo "4. Setting up isolated Gramps home..."
mkdir -p "$GRAMPS_HOME_DIR/gramps60/plugins/PostgreSQLEnhanced"

# Copy PostgreSQL Enhanced plugin
echo "5. Installing PostgreSQL Enhanced plugin..."
PLUGIN_DIR="$GRAMPS_HOME_DIR/gramps60/plugins/PostgreSQLEnhanced"
cp /home/greg/gramps-postgresql-enhanced/*.py "$PLUGIN_DIR/"
cp /home/greg/gramps-postgresql-enhanced/GRAMPSWEB_DEPLOYMENT.md "$PLUGIN_DIR/" 2>/dev/null || true

# Create launcher that combines system Gramps with uv packages
echo "6. Creating launcher..."
cat > "$TEST_DIR/run-gramps.sh" << 'EOF'
#!/bin/bash
# Run System Gramps with uv-managed psycopg3 and isolated data

TEST_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$TEST_DIR/.venv"
GRAMPS_HOME_DIR="$TEST_DIR/gramps_home"

# Activate venv for psycopg3
source "$VENV_DIR/bin/activate"

# Set isolated Gramps home
export GRAMPSHOME="$GRAMPS_HOME_DIR"

# PostgreSQL Enhanced configuration
export POSTGRESQL_ENHANCED_MODE="monolithic"
export GRAMPSWEB_POSTGRES_HOST="192.168.10.90"
export GRAMPSWEB_POSTGRES_PORT="5432"
export GRAMPSWEB_POSTGRES_DB="henderson_unified"
export GRAMPSWEB_POSTGRES_USER="genealogy_user"
export GRAMPSWEB_POSTGRES_PASSWORD="GenealogyData2025"

echo "=========================================="
echo "Running Gramps with PostgreSQL Enhanced"
echo "=========================================="
echo "GRAMPSHOME: $GRAMPSHOME"
echo "psycopg3: from $VENV_DIR (managed by uv)"
echo "Database: PostgreSQL Enhanced (monolithic mode)"
echo ""
echo "This is isolated from ~/.gramps/"
echo ""

# Run system Gramps but it will use our venv's psycopg3
gramps "$@"
EOF

chmod +x "$TEST_DIR/run-gramps.sh"

# Create Gramps Web API launcher
echo "7. Creating Gramps Web launcher..."
cat > "$TEST_DIR/run-grampsweb.sh" << 'EOF'
#!/bin/bash
# Run Gramps Web API with PostgreSQL Enhanced

TEST_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$TEST_DIR/.venv"
GRAMPS_HOME_DIR="$TEST_DIR/gramps_home"

# Activate venv
source "$VENV_DIR/bin/activate"

# Set environment
export GRAMPSHOME="$GRAMPS_HOME_DIR"
export DATABASE_BACKEND="postgresqlenhanced"
export TREE="*"
export POSTGRESQL_ENHANCED_MODE="monolithic"
export GRAMPSWEB_POSTGRES_HOST="192.168.10.90"
export GRAMPSWEB_POSTGRES_PORT="5432"
export GRAMPSWEB_POSTGRES_DB="henderson_unified"
export GRAMPSWEB_POSTGRES_USER="genealogy_user"
export GRAMPSWEB_POSTGRES_PASSWORD="GenealogyData2025"
export GRAMPSWEB_USER_DB_URI="postgresql://genealogy_user:GenealogyData2025@192.168.10.90/henderson_unified"
export GRAMPSWEB_SECRET_KEY="test-key-$(date +%s)"

echo "Starting Gramps Web API..."
echo "GRAMPSHOME: $GRAMPSHOME"
echo "URL: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python -m gramps_webapi --host 0.0.0.0 --port 5000
EOF

chmod +x "$TEST_DIR/run-grampsweb.sh"

# Create a script to check everything is working
echo "8. Creating test script..."
cat > "$TEST_DIR/test-setup.sh" << 'EOF'
#!/bin/bash

TEST_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$TEST_DIR/.venv"

source "$VENV_DIR/bin/activate"

echo "Testing installation..."
echo ""
echo "1. Python version:"
python --version
echo ""
echo "2. psycopg version:"
python -c "import psycopg; print(f'psycopg3: {psycopg.__version__}')"
echo ""
echo "3. Gramps Web API:"
python -c "import gramps_webapi; print('gramps-webapi: installed')"
echo ""
echo "4. PostgreSQL Enhanced plugin:"
if [ -f "$TEST_DIR/gramps_home/gramps60/plugins/PostgreSQLEnhanced/postgresqlenhanced.py" ]; then
    echo "PostgreSQL Enhanced: installed"
else
    echo "PostgreSQL Enhanced: NOT FOUND"
fi
echo ""
echo "5. Testing PostgreSQL connection:"
python << PYTEST
import psycopg
try:
    conn = psycopg.connect(
        host='192.168.10.90',
        port=5432,
        user='genealogy_user',
        password='GenealogyData2025',
        connect_timeout=3
    )
    print("PostgreSQL connection: SUCCESS")
    conn.close()
except Exception as e:
    print(f"PostgreSQL connection: FAILED - {e}")
PYTEST
EOF

chmod +x "$TEST_DIR/test-setup.sh"

echo ""
echo "=========================================="
echo "Quick Test Environment Ready!"
echo "=========================================="
echo ""
echo "Installation location: $TEST_DIR"
echo ""
echo "Available commands:"
echo "  Test setup:    $TEST_DIR/test-setup.sh"
echo "  Run Gramps:    $TEST_DIR/run-gramps.sh"
echo "  Run Gramps Web: $TEST_DIR/run-grampsweb.sh"
echo ""
echo "This uses:"
echo "  - Your system Gramps (6.0.1)"
echo "  - uv-managed psycopg3 in virtual environment"
echo "  - Isolated data directory (not touching ~/.gramps/)"
echo ""
echo "Run test-setup.sh first to verify everything is working."