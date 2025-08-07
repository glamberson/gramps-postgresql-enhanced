#!/bin/bash
# Run System Gramps with Isolated Data Directory
# This uses your existing Gramps 6.0.1 but with completely separate data

# Create isolated home for this Gramps instance
ISOLATED_HOME="$HOME/gramps-web-testing"
ISOLATED_GRAMPS_HOME="$ISOLATED_HOME/.gramps"

echo "=========================================="
echo "Running System Gramps with Isolated Data"
echo "=========================================="

# Create directories
mkdir -p "$ISOLATED_GRAMPS_HOME/gramps60/plugins/PostgreSQLEnhanced"

# Copy PostgreSQL Enhanced plugin
echo "Installing PostgreSQL Enhanced plugin..."
cp -r /home/greg/gramps-postgresql-enhanced/*.py \
      /home/greg/gramps-postgresql-enhanced/*.md \
      /home/greg/gramps-postgresql-enhanced/po \
      "$ISOLATED_GRAMPS_HOME/gramps60/plugins/PostgreSQLEnhanced/" 2>/dev/null || true

# Set environment for Gramps Web compatibility
export GRAMPSHOME="$ISOLATED_GRAMPS_HOME"
export POSTGRESQL_ENHANCED_MODE="monolithic"
export GRAMPSWEB_POSTGRES_HOST="192.168.10.90"
export GRAMPSWEB_POSTGRES_PORT="5432"
export GRAMPSWEB_POSTGRES_DB="henderson_unified"
export GRAMPSWEB_POSTGRES_USER="genealogy_user"
export GRAMPSWEB_POSTGRES_PASSWORD="GenealogyData2025"

echo ""
echo "Configuration:"
echo "  GRAMPSHOME: $GRAMPSHOME"
echo "  Database Mode: monolithic"
echo "  PostgreSQL: 192.168.10.90"
echo ""
echo "This is completely isolated from your regular Gramps at ~/.gramps/"
echo ""

# Launch Gramps
gramps "$@"