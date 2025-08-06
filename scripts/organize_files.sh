#!/bin/bash

# PostgreSQL Enhanced Repository Organization Script
# Date: 2025-08-06
# Purpose: Organize files according to PROJECT_ORGANIZATION_POLICY.md standards

echo "=== Starting PostgreSQL Enhanced Repository Organization ==="
echo "Creating backup first..."

# Create backup
BACKUP_DIR="archive/backups/2025-08-06/pre-organization"
mkdir -p "$BACKUP_DIR"

# Move session handover documents to sessions/
echo "Moving session documents..."
mv -v *HANDOVER*.md sessions/ 2>/dev/null
mv -v SESSION_*.md sessions/ 2>/dev/null
mv -v *SESSION_*.md sessions/ 2>/dev/null
mv -v CONTINUATION_*.md sessions/ 2>/dev/null
mv -v NEXT_SESSION*.md sessions/ 2>/dev/null

# Move reports to reports/
echo "Moving report documents..."
mv -v *REPORT*.md reports/ 2>/dev/null
mv -v *ANALYSIS*.md reports/ 2>/dev/null
mv -v *RESULTS*.md reports/ 2>/dev/null
mv -v *STATUS*.md reports/ 2>/dev/null
mv -v *SUMMARY*.md reports/ 2>/dev/null
mv -v IMPORT_*.md reports/ 2>/dev/null

# Move architecture and technical docs to docs/architecture/
echo "Moving architecture documents..."
mv -v ARCHITECTURE*.md docs/architecture/ 2>/dev/null
mv -v FUTURE*.md docs/architecture/ 2>/dev/null
mv -v TECHNICAL*.md docs/architecture/ 2>/dev/null
mv -v EXTENSION*.md docs/architecture/ 2>/dev/null
mv -v NATIVE*.md docs/architecture/ 2>/dev/null
mv -v POSTGRES*.md docs/architecture/ 2>/dev/null

# Move guides to docs/guides/
echo "Moving guide documents..."
mv -v SETUP_GUIDE*.md docs/guides/ 2>/dev/null
mv -v *GUIDE*.md docs/guides/ 2>/dev/null
mv -v DATABASE_CONFIGURATION_GUIDE.md docs/guides/ 2>/dev/null
mv -v DATABASE_MODES*.md docs/guides/ 2>/dev/null
mv -v CONFIGURATION*.md docs/guides/ 2>/dev/null

# Move procedures to docs/procedures/
echo "Moving procedure documents..."
mv -v TESTING*.md docs/procedures/ 2>/dev/null
mv -v SUBMISSION*.md docs/procedures/ 2>/dev/null
mv -v FEATURE*.md docs/procedures/ 2>/dev/null
mv -v MIGRATION*.md docs/procedures/ 2>/dev/null

# Move troubleshooting docs
echo "Moving troubleshooting documents..."
mv -v *BUG*.md docs/troubleshooting/ 2>/dev/null
mv -v *FIX*.md docs/troubleshooting/ 2>/dev/null
mv -v *ISSUE*.md docs/troubleshooting/ 2>/dev/null

# Move test files to tests/
echo "Moving test files..."
mv -v test_*.py tests/ 2>/dev/null
mv -v *test*.log tests/ 2>/dev/null

# Move scripts to scripts/
echo "Moving scripts..."
mv -v *.sh scripts/ 2>/dev/null
mv -v fix_*.py scripts/ 2>/dev/null
mv -v add_*.py scripts/ 2>/dev/null
mv -v apply_*.py scripts/ 2>/dev/null
mv -v lint_*.py scripts/ 2>/dev/null
mv -v run_*.py scripts/ 2>/dev/null
mv -v debug_*.py scripts/ 2>/dev/null
mv -v verify_*.py scripts/ 2>/dev/null

# Move source files to src/
echo "Moving source files..."
# Keep the main addon files in root for Gramps compatibility
# But copy supporting modules to src/
cp -v connection.py src/ 2>/dev/null
cp -v schema.py src/ 2>/dev/null
cp -v migration.py src/ 2>/dev/null
cp -v queries.py src/ 2>/dev/null
cp -v schema_columns.py src/ 2>/dev/null
cp -v debug_utils.py src/ 2>/dev/null
cp -v mock_gramps.py src/ 2>/dev/null
cp -v type_*.py src/ 2>/dev/null
cp -v performance_test.py src/ 2>/dev/null

# Move config files to config/
echo "Moving configuration files..."
mv -v connection_info*.txt config/ 2>/dev/null
cp -v connection_info_template.txt config/ 2>/dev/null

# Move deprecated/old documents to archive/deprecated/
echo "Moving deprecated documents..."
mv -v *2025_08_04*.md archive/deprecated/ 2>/dev/null
mv -v *2025_08_05*.md archive/deprecated/ 2>/dev/null
mv -v *20250804*.md archive/deprecated/ 2>/dev/null
mv -v *20250805*.md archive/deprecated/ 2>/dev/null
mv -v BULLETPROOF*.md archive/deprecated/ 2>/dev/null
mv -v CLEANUP*.md archive/deprecated/ 2>/dev/null
mv -v COMMIT_ANALYSIS*.md archive/deprecated/ 2>/dev/null
mv -v EXHAUSTIVE*.md archive/deprecated/ 2>/dev/null

# Move backup files
echo "Moving backup files..."
mv -v *.backup* archive/backups/2025-08-06/ 2>/dev/null

# Move logs to logs/
echo "Moving log files..."
mv -v *.log logs/ 2>/dev/null
mv -v pylint_report.txt logs/ 2>/dev/null

# Create proper README files for each directory
echo "Creating directory README files..."

cat > docs/INDEX.md << 'EOF'
# Documentation Index

## Guides
- [Setup Guides](guides/) - Installation and configuration
- [Database Configuration](guides/DATABASE_CONFIGURATION_GUIDE.md) - How to configure the addon
- [Database Modes](guides/DATABASE_MODES_DELETION_BEHAVIOR.md) - Understanding database modes

## Architecture
- [Technical Documentation](architecture/) - System design and implementation details

## Procedures
- [Testing](procedures/TESTING.md) - Testing procedures
- [Submission](procedures/SUBMISSION_GUIDE.md) - How to submit to Gramps

## Troubleshooting
- [Known Issues](troubleshooting/) - Common problems and solutions

## Standards
- [Project Standards](standards/) - Coding and documentation standards
EOF

cat > sessions/README.md << 'EOF'
# Session Documents

This directory contains session handover documents organized by date.
Latest session: See the most recent HANDOVER file.
EOF

cat > reports/README.md << 'EOF'
# Reports and Analysis

This directory contains analysis reports, test results, and status documents.
EOF

cat > scripts/README.md << 'EOF'
# Scripts

Utility scripts for testing, maintenance, and development.
EOF

cat > tests/README.md << 'EOF'
# Tests

Test files and test artifacts for the PostgreSQL Enhanced addon.
EOF

echo "=== Organization Complete ==="
echo "Files have been organized according to standards."
echo "Review the changes and commit when ready."