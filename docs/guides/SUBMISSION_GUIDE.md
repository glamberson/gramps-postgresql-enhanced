# Submission Guide for gramps-project/addons-source

This guide describes how to submit the PostgreSQL Enhanced addon to the official Gramps addons repository.

## Overview

The Gramps project maintains addons in two repositories:
- `gramps-project/addons-source` - Source code (where we submit)
- `gramps-project/addons` - Built packages (automatically generated)

## Submission Process

### 1. Fork the addons-source Repository

```bash
# Fork via GitHub CLI
gh repo fork gramps-project/addons-source --clone=false

# Or use the GitHub web interface:
# https://github.com/gramps-project/addons-source
```

### 2. Clone Your Fork

```bash
# Clone your fork
git clone https://github.com/glamberson/addons-source.git
cd addons-source

# Add upstream remote
git remote add upstream https://github.com/gramps-project/addons-source.git

# Fetch and checkout the correct branch
git fetch upstream
git checkout -b maintenance/gramps60 upstream/maintenance/gramps60
```

### 3. Add PostgreSQL Enhanced Addon

```bash
# Create a branch for your changes
git checkout -b add-postgresql-enhanced

# Copy the addon to the repository
cp -r /home/greg/gramps-postgresql-enhanced PostgreSQLEnhanced

# Ensure proper structure
ls -la PostgreSQLEnhanced/
# Should contain: *.py files, po/, README.md, etc.
```

### 4. Prepare the Addon

```bash
# Initialize the addon structure and create .pot file
python3 make.py gramps60 init PostgreSQLEnhanced

# Build the addon package for testing
python3 make.py gramps60 build PostgreSQLEnhanced

# Create listing entry
python3 make.py gramps60 listing PostgreSQLEnhanced
```

### 5. Test the Built Package

```bash
# The built package will be in ../addons/gramps60/download/
ls -la ../addons/gramps60/download/PostgreSQLEnhanced.addon.tgz

# Test installation in Gramps
# 1. Open Gramps
# 2. Tools → Plugin Manager → Install Addon
# 3. Browse to the .addon.tgz file
```

### 6. Commit and Push

```bash
# Add all new files
git add PostgreSQLEnhanced/
git add ../addons/gramps60/download/PostgreSQLEnhanced.addon.tgz
git add ../addons/gramps60/listings/addons-*.json

# Commit with descriptive message
git commit -m "Add PostgreSQL Enhanced addon

- Modern PostgreSQL backend using psycopg3
- Dual storage with blobs and JSONB
- Advanced query capabilities
- Migration support from SQLite
- Full documentation and tests included"

# Push to your fork
git push origin add-postgresql-enhanced
```

### 7. Create Pull Request

```bash
# Create PR via GitHub CLI
gh pr create \
  --repo gramps-project/addons-source \
  --base maintenance/gramps60 \
  --head glamberson:add-postgresql-enhanced \
  --title "Add PostgreSQL Enhanced addon for Gramps 6.0" \
  --body "## Description

This PR adds the PostgreSQL Enhanced addon, which provides an advanced PostgreSQL database backend for Gramps.

## Key Features
- Uses modern psycopg3 (not psycopg2)
- Dual storage: pickle blobs (compatibility) + JSONB (queryability)
- Advanced queries with recursive CTEs and full-text search
- Migration support from SQLite and standard PostgreSQL addon
- Optimized for large databases (50,000+ persons)
- True multi-user support with proper locking

## Testing
- Tested with Gramps 6.0.3
- Includes comprehensive test suite
- Performance benchmarks included
- Documentation: https://github.com/glamberson/gramps-postgresql-enhanced

## Requirements
- PostgreSQL 15+
- Python 3.9+
- psycopg 3.1+

Fixes #[issue-number] (if applicable)"
```

### 8. Alternative: Manual PR Creation

If you prefer the web interface:

1. Go to: https://github.com/gramps-project/addons-source
2. You should see a banner about your recently pushed branch
3. Click "Compare & pull request"
4. Ensure:
   - Base repository: `gramps-project/addons-source`
   - Base branch: `maintenance/gramps60`
   - Head repository: `glamberson/addons-source`
   - Compare branch: `add-postgresql-enhanced`
5. Fill in the PR template with the description above
6. Create pull request

## PR Guidelines

### Do's
- Target the correct branch (`maintenance/gramps60` for Gramps 6.0)
- Include clear description of features
- Mention testing performed
- Follow Gramps coding standards
- Include documentation

### Don'ts
- Don't target `master` unless developing for unreleased Gramps
- Don't include binary files except the built .addon.tgz
- Don't modify other addons in the same PR

## After Submission

1. **Monitor CI/CD**: Travis CI will run automated tests
2. **Respond to feedback**: Maintainers may request changes
3. **Update as needed**: Push additional commits to your branch
4. **Patience**: Review may take time

## Maintenance

Once accepted, you'll be responsible for:
- Bug fixes
- Compatibility updates for new Gramps versions
- Responding to user issues
- Keeping documentation updated

## Contact

- Gramps Discourse: https://gramps.discourse.group/
- GitHub Issues: https://github.com/gramps-project/gramps/issues
- Your addon repo: https://github.com/glamberson/gramps-postgresql-enhanced