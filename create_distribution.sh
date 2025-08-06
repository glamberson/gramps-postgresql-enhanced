#!/bin/bash
# Create a clean distribution package for Gramps submission

ADDON_NAME="PostgreSQLEnhanced"
VERSION="1.0.0"
DIST_DIR="dist"

echo "Creating distribution package for $ADDON_NAME v$VERSION"

# Clean up any existing dist directory
rm -rf $DIST_DIR
mkdir -p $DIST_DIR/$ADDON_NAME

# Core Python files (required)
echo "Copying core files..."
cp postgresqlenhanced.py $DIST_DIR/$ADDON_NAME/
cp postgresqlenhanced.gpr.py $DIST_DIR/$ADDON_NAME/
cp connection.py $DIST_DIR/$ADDON_NAME/
cp schema.py $DIST_DIR/$ADDON_NAME/
cp schema_columns.py $DIST_DIR/$ADDON_NAME/
cp migration.py $DIST_DIR/$ADDON_NAME/
cp queries.py $DIST_DIR/$ADDON_NAME/
cp __init__.py $DIST_DIR/$ADDON_NAME/ 2>/dev/null || touch $DIST_DIR/$ADDON_NAME/__init__.py

# Translation files
echo "Copying translation files..."
mkdir -p $DIST_DIR/$ADDON_NAME/po
cp -r po/* $DIST_DIR/$ADDON_NAME/po/ 2>/dev/null || true

# Documentation
echo "Copying documentation..."
cp README.md $DIST_DIR/$ADDON_NAME/
cp INSTALL.md $DIST_DIR/$ADDON_NAME/
cp requirements.txt $DIST_DIR/$ADDON_NAME/

# Essential config template
mkdir -p $DIST_DIR/$ADDON_NAME/config
cp config/connection_info_template.txt $DIST_DIR/$ADDON_NAME/config/

# Essential scripts for users
mkdir -p $DIST_DIR/$ADDON_NAME/scripts
cp scripts/register_existing_tree.sh $DIST_DIR/$ADDON_NAME/scripts/
cp scripts/verify_addon.py $DIST_DIR/$ADDON_NAME/scripts/
cp scripts/verify_database_contents.py $DIST_DIR/$ADDON_NAME/scripts/

# Create simplified test suite
mkdir -p $DIST_DIR/$ADDON_NAME/tests
cp tests/test_postgresql_enhanced.py $DIST_DIR/$ADDON_NAME/tests/
cp tests/test_simple_operations.py $DIST_DIR/$ADDON_NAME/tests/
cp tests/README.md $DIST_DIR/$ADDON_NAME/tests/ 2>/dev/null || echo "# Tests\n\nRun test_postgresql_enhanced.py to verify installation." > $DIST_DIR/$ADDON_NAME/tests/README.md

# Create the tarball
echo "Creating distribution archive..."
cd $DIST_DIR
tar -czf ${ADDON_NAME}-${VERSION}.tar.gz $ADDON_NAME/
cd ..

# Create .addon.tgz for Gramps
echo "Creating Gramps addon package..."
cd $DIST_DIR/$ADDON_NAME
tar -czf ../${ADDON_NAME}.addon.tgz *
cd ../..

echo "Distribution package created:"
echo "  - $DIST_DIR/${ADDON_NAME}-${VERSION}.tar.gz (general distribution)"
echo "  - $DIST_DIR/${ADDON_NAME}.addon.tgz (Gramps addon format)"

# Verify package size
SIZE=$(du -sh $DIST_DIR/${ADDON_NAME}.addon.tgz | cut -f1)
echo "Package size: $SIZE"

# List contents
echo ""
echo "Package contents:"
tar -tzf $DIST_DIR/${ADDON_NAME}.addon.tgz | head -20
echo "..."

echo ""
echo "To install in Gramps:"
echo "  1. Open Gramps"
echo "  2. Tools → Plugin Manager → Install Addon"
echo "  3. Browse to: $PWD/$DIST_DIR/${ADDON_NAME}.addon.tgz"