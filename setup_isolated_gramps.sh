#!/bin/bash
# Setup Isolated Gramps 6.0.3 with PostgreSQL Enhanced for Gramps Web
# This creates a completely separate installation that won't interfere with existing Gramps

set -e  # Exit on error

echo "=========================================="
echo "Setting up Isolated Gramps 6.0.3 Environment"
echo "=========================================="

# Configuration
GRAMPS_VERSION="6.0.3"
INSTALL_DIR="$HOME/gramps-web-env"
VENV_DIR="$INSTALL_DIR/venv"
GRAMPS_HOME_DIR="$INSTALL_DIR/gramps_home"
GRAMPS_SRC_DIR="$INSTALL_DIR/gramps-${GRAMPS_VERSION}"

# Create installation directory
echo "1. Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create Python virtual environment
echo "2. Creating Python virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "3. Upgrading pip..."
pip install --upgrade pip wheel setuptools

# Install Python dependencies
echo "4. Installing Python dependencies..."
pip install PyGObject cairo pycairo psycopg[binary] gramps-webapi

# Download Gramps 6.0.3 source
echo "5. Downloading Gramps ${GRAMPS_VERSION}..."
if [ ! -f "gramps-${GRAMPS_VERSION}.tar.gz" ]; then
    wget "https://github.com/gramps-project/gramps/archive/refs/tags/v${GRAMPS_VERSION}.tar.gz" -O "gramps-${GRAMPS_VERSION}.tar.gz"
fi

# Extract Gramps
echo "6. Extracting Gramps..."
tar -xzf "gramps-${GRAMPS_VERSION}.tar.gz"

# Build and install Gramps in the virtual environment
echo "7. Building and installing Gramps..."
cd "$GRAMPS_SRC_DIR"
python setup.py build
python setup.py install

# Create isolated GRAMPSHOME
echo "8. Creating isolated GRAMPSHOME: $GRAMPS_HOME_DIR"
mkdir -p "$GRAMPS_HOME_DIR"

# Copy PostgreSQL Enhanced to plugins directory
echo "9. Installing PostgreSQL Enhanced plugin..."
PLUGIN_DIR="$GRAMPS_HOME_DIR/gramps60/plugins/PostgreSQLEnhanced"
mkdir -p "$PLUGIN_DIR"
cp -r /home/greg/gramps-postgresql-enhanced/* "$PLUGIN_DIR/"

# Create launcher script
echo "10. Creating launcher script..."
cat > "$INSTALL_DIR/gramps-isolated.sh" << 'EOF'
#!/bin/bash
# Launch Isolated Gramps with PostgreSQL Enhanced

# Set paths
INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
VENV_DIR="$INSTALL_DIR/venv"
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
echo "Virtual Environment: $VENV_DIR"
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
VENV_DIR="$INSTALL_DIR/venv"
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

# Create desktop launcher (optional)
echo "12. Creating desktop launcher..."
cat > "$HOME/.local/share/applications/gramps-isolated.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Gramps 6.0.3 (Isolated)
Comment=Genealogy research application (Isolated with PostgreSQL Enhanced)
Icon=gramps
Exec=$INSTALL_DIR/gramps-isolated.sh %F
Categories=Office;Database;
Terminal=false
StartupNotify=true
MimeType=application/x-gramps;application/x-gramps-xml;application/x-gedcom;application/x-gramps-package;
EOF

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Isolated Gramps 6.0.3 has been installed to: $INSTALL_DIR"
echo ""
echo "To run isolated Gramps:"
echo "  $INSTALL_DIR/gramps-isolated.sh"
echo ""
echo "To start Gramps Web API:"
echo "  $INSTALL_DIR/grampsweb-start.sh"
echo ""
echo "This installation is completely separate from your existing Gramps."
echo "Data is stored in: $GRAMPS_HOME_DIR"
echo ""
echo "Next steps:"
echo "1. Run gramps-isolated.sh to start Gramps"
echo "2. Create a new family tree using PostgreSQL Enhanced"
echo "3. Test Gramps Web with grampsweb-start.sh"