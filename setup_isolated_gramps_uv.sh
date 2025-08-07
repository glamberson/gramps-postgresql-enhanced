#!/bin/bash
# Setup Isolated Gramps 6.0.3 with PostgreSQL Enhanced for Gramps Web
# Using uv for fast, reliable package management

set -e  # Exit on error

echo "=========================================="
echo "Setting up Isolated Gramps 6.0.3 with uv"
echo "=========================================="

# Configuration
GRAMPS_VERSION="6.0.3"
INSTALL_DIR="$HOME/gramps-web-env"
VENV_DIR="$INSTALL_DIR/.venv"
GRAMPS_HOME_DIR="$INSTALL_DIR/gramps_home"
GRAMPS_SRC_DIR="$INSTALL_DIR/gramps-${GRAMPS_VERSION}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create installation directory
echo "1. Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create virtual environment with uv
echo "2. Creating virtual environment with uv..."
uv venv "$VENV_DIR" --python 3.11  # Use Python 3.11 for better compatibility
source "$VENV_DIR/bin/activate"

# Install Python dependencies with uv
echo "3. Installing Python dependencies with uv..."
uv pip install --upgrade pip wheel setuptools

# Install required packages
echo "4. Installing Gramps dependencies..."
uv pip install \
    PyGObject \
    cairo \
    pycairo \
    "psycopg[binary]>=3.1" \
    gramps-webapi \
    pillow \
    geocode-glib \
    pyicu \
    osmgpsmap

# Download Gramps 6.0.3 source
echo "5. Downloading Gramps ${GRAMPS_VERSION}..."
if [ ! -f "gramps-${GRAMPS_VERSION}.tar.gz" ]; then
    wget "https://github.com/gramps-project/gramps/archive/refs/tags/v${GRAMPS_VERSION}.tar.gz" -O "gramps-${GRAMPS_VERSION}.tar.gz"
fi

# Extract Gramps
echo "6. Extracting Gramps..."
tar -xzf "gramps-${GRAMPS_VERSION}.tar.gz"

# Build and install Gramps
echo "7. Building and installing Gramps..."
cd "$GRAMPS_SRC_DIR"
python setup.py build
python setup.py install

# Create isolated GRAMPSHOME
echo "8. Creating isolated GRAMPSHOME: $GRAMPS_HOME_DIR"
mkdir -p "$GRAMPS_HOME_DIR/gramps60/plugins/PostgreSQLEnhanced"

# Copy PostgreSQL Enhanced to plugins directory
echo "9. Installing PostgreSQL Enhanced plugin..."
PLUGIN_DIR="$GRAMPS_HOME_DIR/gramps60/plugins/PostgreSQLEnhanced"
cp -r /home/greg/gramps-postgresql-enhanced/*.py "$PLUGIN_DIR/"
cp -r /home/greg/gramps-postgresql-enhanced/*.md "$PLUGIN_DIR/" 2>/dev/null || true
cp -r /home/greg/gramps-postgresql-enhanced/po "$PLUGIN_DIR/" 2>/dev/null || true

# Create launcher script
echo "10. Creating launcher script..."
cat > "$INSTALL_DIR/gramps-isolated.sh" << 'EOF'
#!/bin/bash
# Launch Isolated Gramps with PostgreSQL Enhanced

# Set paths
INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$INSTALL_DIR/.venv"
GRAMPS_HOME_DIR="$INSTALL_DIR/gramps_home"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set Gramps environment variables
export GRAMPSHOME="$GRAMPS_HOME_DIR"
export GRAMPS_RESOURCES="$VENV_DIR/lib/python*/site-packages/gramps"

# Optional: Set for Gramps Web mode
export POSTGRESQL_ENHANCED_MODE="monolithic"
export GRAMPSWEB_POSTGRES_HOST="192.168.10.90"
export GRAMPSWEB_POSTGRES_PORT="5432"
export GRAMPSWEB_POSTGRES_DB="henderson_unified"
export GRAMPSWEB_POSTGRES_USER="genealogy_user"
export GRAMPSWEB_POSTGRES_PASSWORD="GenealogyData2025"

echo "Starting Isolated Gramps 6.0.3..."
echo "GRAMPSHOME: $GRAMPSHOME"
echo "Virtual Environment: $VENV_DIR (managed by uv)"
echo ""

# Launch Gramps with all arguments passed through
gramps "$@"
EOF

chmod +x "$INSTALL_DIR/gramps-isolated.sh"

# Create Gramps Web launcher
echo "11. Creating Gramps Web launcher..."
cat > "$INSTALL_DIR/grampsweb-start.sh" << 'EOF'
#!/bin/bash
# Start Gramps Web API with PostgreSQL Enhanced

# Set paths
INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$INSTALL_DIR/.venv"
GRAMPS_HOME_DIR="$INSTALL_DIR/gramps_home"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set environment
export GRAMPSHOME="$GRAMPS_HOME_DIR"
export GRAMPS_RESOURCES="$VENV_DIR/lib/python*/site-packages/gramps"

# Gramps Web configuration
export DATABASE_BACKEND="postgresqlenhanced"
export TREE="*"
export POSTGRESQL_ENHANCED_MODE="monolithic"
export GRAMPSWEB_POSTGRES_HOST="192.168.10.90"
export GRAMPSWEB_POSTGRES_PORT="5432"
export GRAMPSWEB_POSTGRES_DB="henderson_unified"
export GRAMPSWEB_POSTGRES_USER="genealogy_user"
export GRAMPSWEB_POSTGRES_PASSWORD="GenealogyData2025"
export GRAMPSWEB_USER_DB_URI="postgresql://genealogy_user:GenealogyData2025@192.168.10.90/henderson_unified"
export GRAMPSWEB_SECRET_KEY="change-this-to-random-string-$(openssl rand -hex 16)"

echo "Starting Gramps Web API..."
echo "GRAMPSHOME: $GRAMPSHOME"
echo "Database: PostgreSQL Enhanced (monolithic mode)"
echo "Access at: http://localhost:5000"
echo ""

# Start Gramps Web API
python -m gramps_webapi --host 0.0.0.0 --port 5000
EOF

chmod +x "$INSTALL_DIR/grampsweb-start.sh"

# Create uv update script
echo "12. Creating uv package update script..."
cat > "$INSTALL_DIR/update-packages.sh" << 'EOF'
#!/bin/bash
# Update packages using uv

INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$INSTALL_DIR/.venv"

source "$VENV_DIR/bin/activate"

echo "Updating packages with uv..."
uv pip install --upgrade \
    PyGObject \
    cairo \
    pycairo \
    "psycopg[binary]>=3.1" \
    gramps-webapi

echo "Packages updated!"
EOF

chmod +x "$INSTALL_DIR/update-packages.sh"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Isolated Gramps 6.0.3 has been installed to: $INSTALL_DIR"
echo ""
echo "Commands:"
echo "  Start Gramps:     $INSTALL_DIR/gramps-isolated.sh"
echo "  Start Gramps Web: $INSTALL_DIR/grampsweb-start.sh"
echo "  Update packages:  $INSTALL_DIR/update-packages.sh"
echo ""
echo "This installation is completely separate from your existing Gramps."
echo "Data is stored in: $GRAMPS_HOME_DIR"
echo ""
echo "Virtual environment managed by uv for fast, reliable package management."