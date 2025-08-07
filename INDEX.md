# PostgreSQL Enhanced for Gramps - Master Index

## 🚀 Quick Start
- [README](README.md) - Main documentation and setup instructions
- [Configuration Guide](docs/guides/DATABASE_CONFIGURATION_GUIDE.md) - How to configure the addon
- [Connection Template](config/connection_info_template.txt) - Configuration file template

## 📚 Documentation

### Setup Guides
- [Linux Setup](docs/guides/SETUP_GUIDE_LINUX.md) - Installation on Linux systems
- [macOS Setup](docs/guides/SETUP_GUIDE_MACOS.md) - Installation on macOS
- [Windows Setup](docs/guides/SETUP_GUIDE_WINDOWS.md) - Installation on Windows
- [General Setup](docs/guides/SETUP_GUIDE.md) - Platform selection guide

### Configuration & Features
- [Database Configuration](docs/guides/DATABASE_CONFIGURATION_GUIDE.md) - Detailed configuration instructions
- [Database Modes](docs/guides/DATABASE_MODES_DELETION_BEHAVIOR.md) - Monolithic vs Separate modes
- [Feature Comparison](docs/guides/FEATURE_COMPARISON.md) - PostgreSQL Enhanced vs SQLite/Original addon
- [Gramps PostgreSQL Comparison](docs/guides/GRAMPS_POSTGRES_COMPARISON.md) - Detailed comparison
- [Configuration Q&A](docs/guides/ANSWERS_TO_CONFIGURATION_QUESTIONS.md) - Common configuration questions

### Architecture & Technical
- [Technical Reference](docs/architecture/TECHNICAL_CONTEXT_REFERENCE.md) - Technical implementation details
- [PostgreSQL 15 Compatibility](docs/architecture/POSTGRESQL_15_COMPAT.md) - PostgreSQL version requirements
- [Connection Implementation](docs/architecture/CONNECTION_CONFIG_IMPLEMENTATION.md) - How connections work
- [Native JSON Support](docs/architecture/NATIVE_JSON_FIX.md) - JSONB implementation details

### Procedures
- [Testing Procedures](docs/procedures/TESTING.md) - How to test the addon
- [Submission Guide](docs/guides/SUBMISSION_GUIDE.md) - Submitting to Gramps project
- [Submission Checklist](docs/procedures/SUBMISSION_CHECKLIST.md) - Pre-submission requirements
- [Recovery Procedures](docs/procedures/RECOVERY_PROCESS_DOCUMENTATION.md) - Database recovery

### Troubleshooting
- [Known Issues](docs/troubleshooting/) - Common problems and solutions
- [Gramps Check Tool Bug](docs/troubleshooting/GRAMPS_CHECK_TOOL_BUG.md) - Known Gramps issue
- [Linting Errors Fixed](docs/troubleshooting/LINTING_ERRORS_FIXED.md) - Code quality fixes

## 🔧 Source Code

### Main Addon Files (Root - Required for Gramps)
- [postgresqlenhanced.py](postgresqlenhanced.py) - Main addon implementation
- [postgresqlenhanced.gpr.py](postgresqlenhanced.gpr.py) - Gramps plugin registration
- [__init__.py](__init__.py) - Python package initialization

### Supporting Modules
- [connection.py](connection.py) - Database connection handling
- [schema.py](schema.py) - Schema creation and management
- [migration.py](migration.py) - Migration utilities
- [queries.py](queries.py) - Enhanced query functions
- [schema_columns.py](schema_columns.py) - Column definitions
- [debug_utils.py](debug_utils.py) - Debug utilities

## 🧪 Testing
- [Test Directory](tests/) - All test files
- [Test Runner](scripts/run_tests.py) - Run all tests
- [Performance Test](tests/test_postgresql_enhanced.py) - Main test suite

## 🛠️ Scripts & Tools
- [Scripts Directory](scripts/) - Utility scripts
- [Register Existing Tree](scripts/register_existing_tree.sh) - Register PostgreSQL trees in Gramps
- [Debug Gramps](scripts/START_GRAMPS_DEBUG.sh) - Start Gramps with debugging
- [Monitor Import](scripts/monitor_import.sh) - Monitor GEDCOM imports

## 📊 Reports & Analysis
- [Latest Status](reports/CURRENT_STATUS_2025_08_06.md) - Current project status
- [Test Reports](reports/) - All test results and analyses
- [Session Documents](sessions/) - Development session handovers

## 🗂️ Project Organization

### Active Directories
```
.
├── config/           # Configuration files and templates
├── docs/            # All documentation
│   ├── guides/      # Setup and usage guides
│   ├── procedures/  # Step-by-step procedures
│   ├── architecture/# Technical documentation
│   └── troubleshooting/ # Problem solutions
├── scripts/         # Utility scripts
├── src/            # Source code copies (originals in root for Gramps)
├── tests/          # Test files
├── logs/           # Log files
├── reports/        # Analysis reports
└── sessions/       # Session handover documents
```

### Archive
- [Archive Directory](archive/) - Deprecated files and backups
- [Today's Backups](archive/backups/2025-08-06/) - Files backed up during organization

## 🔑 Key Features

### Performance
- **100,000+ persons** tested successfully
- **3-10x faster** than SQLite
- **Network capable** with excellent performance
- **True concurrent access** without locking

### Database Modes
- **Monolithic Mode** - All trees in one database with prefixes
- **Separate Mode** - Each tree gets its own database
- Both modes fully tested and working

### Advanced Capabilities
- **JSONB storage** for advanced queries
- **Full-text search** when pg_trgm installed
- **Relationship path finding** using recursive CTEs
- **Duplicate detection** with fuzzy matching
- **Direct SQL access** for power users

## 📝 License & Contact
- **License**: GNU General Public License v2 or later
- **Author**: Greg Lamberson (lamberson@yahoo.com)
- **Repository**: https://github.com/glamberson/gramps-postgresql-enhanced
- **Issues**: https://github.com/glamberson/gramps-postgresql-enhanced/issues