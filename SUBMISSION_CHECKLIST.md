# PostgreSQL Enhanced Addon - Submission Checklist

## Pre-Submission Testing

- [ ] Test with Gramps 6.0.3
- [ ] Verify psycopg3 compatibility (NOT psycopg2)
- [ ] Test database connection with credentials:
  - Host: localhost (or 192.168.10.90 for your setup)
  - Database: gramps_test_db
  - User: gramps_test
  - Password: GrampsTest2025 (no special characters!)
- [ ] Create test person and family
- [ ] Save and reload to verify persistence
- [ ] Run unit tests: `python3 test/run_tests.py`
- [ ] Run verification: `python3 verify_addon.py`

## Code Quality

- [ ] All Python files follow PEP 8
- [ ] No hardcoded credentials
- [ ] Proper error handling
- [ ] Logging uses Gramps logging framework
- [ ] All strings marked for translation

## Documentation

- [ ] README.md is complete
- [ ] Installation instructions are clear
- [ ] Requirements are documented
- [ ] Connection string examples provided
- [ ] Troubleshooting section included

## Repository Structure

- [ ] .gitignore excludes unnecessary files
- [ ] MANIFEST lists all required files
- [ ] po/template.pot exists
- [ ] postgresqlenhanced.gpr.py has correct metadata
- [ ] All test files in test/ directory

## Submission Steps

1. [ ] Fork gramps-project/addons-source
2. [ ] Clone and checkout maintenance/gramps60 branch
3. [ ] Copy addon to PostgreSQLEnhanced/
4. [ ] Run `python3 make.py gramps60 init PostgreSQLEnhanced`
5. [ ] Run `python3 make.py gramps60 build PostgreSQLEnhanced`
6. [ ] Run `python3 make.py gramps60 listing PostgreSQLEnhanced`
7. [ ] Test built .addon.tgz file
8. [ ] Commit with descriptive message
9. [ ] Push to fork
10. [ ] Create PR targeting maintenance/gramps60

## PR Description Template

```markdown
## Description
PostgreSQL Enhanced addon provides an advanced PostgreSQL database backend for Gramps using modern psycopg3.

## Key Features
- Modern psycopg3 (not psycopg2)
- Dual storage: blobs + JSONB
- Advanced queries with CTEs
- Migration from SQLite
- Multi-user support

## Testing
- Tested with Gramps 6.0.3
- Unit tests included
- Performance benchmarks completed
- Documentation: https://github.com/glamberson/gramps-postgresql-enhanced

## Requirements
- PostgreSQL 15+
- Python 3.9+
- psycopg 3.1+
```

## Post-Submission

- [ ] Monitor Travis CI build status
- [ ] Respond to maintainer feedback
- [ ] Update documentation as needed
- [ ] Announce in Gramps Discourse forum