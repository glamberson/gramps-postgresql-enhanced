# PostgreSQL Enhanced v1.3.0 Release Notes

**Release Date**: 2025-08-07  
**Status**: Development Complete  
**Branch**: v1.3-development

## 🎉 Major Release Highlights

PostgreSQL Enhanced v1.3.0 delivers enterprise-grade multi-user support with advanced PostgreSQL-specific features that were identified as missing in earlier versions.

## ✨ New Features

### Advanced Concurrency Control
- **LISTEN/NOTIFY**: Real-time notifications of database changes across multiple users
- **Advisory Locks**: Prevent conflicting edits with object-level locking
- **Transaction Isolation**: Support for all PostgreSQL isolation levels
- **Optimistic Concurrency**: Version-based conflict detection

### Enhanced Search Capabilities
- **Native Full-text Search**: PostgreSQL tsvector/tsquery integration
- **Fuzzy Matching**: pg_trgm extension for duplicate detection
- **Phonetic Search**: fuzzystrmatch extension support
- **Cross-tree Search**: Search across all family trees in monolithic mode

### Architecture Improvements
- **Capabilities System**: Abstract interfaces with graceful fallbacks
- **Extension Detection**: Automatic detection of available PostgreSQL extensions
- **Search API**: Unified search interface with multiple backends
- **Gramps Web Compatibility**: Full sifts replacement for Gramps Web

## 📊 Addressed Criticisms

This release specifically addresses the valid criticisms about v1.0 missing PostgreSQL's advanced features:

| Feature | v1.0 Status | v1.3 Status |
|---------|-------------|-------------|
| LISTEN/NOTIFY | ❌ Missing | ✅ Complete |
| Advisory Locks | ❌ Missing | ✅ Complete |
| Transaction Isolation | ❌ Missing | ✅ Complete |
| Optimistic Concurrency | ❌ Missing | ✅ Complete |
| Full-text Search | ⚠️ Basic | ✅ Native tsvector |
| Fuzzy Search | ❌ Missing | ✅ pg_trgm integrated |
| Extension Support | ❌ Missing | ✅ Auto-detection |

## 🔧 Technical Details

### New Modules
- `concurrency.py`: Complete concurrency control implementation
- `capabilities_base.py`: Abstract capability interfaces
- `search_capabilities.py`: Extension detection and management
- `postgresql_search_indexer.py`: Gramps Web sifts replacement

### API Additions
```python
# Real-time notifications
db.setup_listen_notify(['person_changes', 'family_changes'])
db.add_change_listener('person', callback_function)
db.notify_object_change('person', handle, 'update')

# Concurrent access control
with db.object_lock('person', handle, exclusive=True):
    # Safe modification of person object
    person = db.get_person_from_handle(handle)
    # ... modify person ...
    db.commit_person(person, trans)

# Transaction isolation
db.begin_transaction_with_isolation('SERIALIZABLE')

# Optimistic concurrency
version = db.get_object_version('person', handle)
# ... user edits ...
db.check_object_version('person', handle, version)  # Raises if modified
```

## 🚀 Performance Improvements

- Recursive CTEs for efficient ancestry traversal
- JSONB indexing for complex queries
- Prepared statement support (coordinating with Doug Blank's PR #2098)
- Connection pooling improvements

## 🔄 Backward Compatibility

- All new features gracefully fallback when not available
- Compatible with PostgreSQL 12+ (optimal with 15+)
- Maintains compatibility with existing Gramps databases
- Works with both monolithic and separate database modes

## 📝 Migration Notes

No database migration required. New features are automatically available after upgrading.

## 🐛 Bug Fixes

- Fixed NULL first name handling
- Improved error handling in concurrent scenarios
- Better connection recovery after network issues

## 🔮 Future Roadmap

- Integration with Doug Blank's prepared statements (PR #2098)
- Apache AGE graph database support
- pgvector for AI/ML capabilities
- Partial and expression indexes

## 📚 Documentation

Updated documentation includes:
- Concurrency control guide
- Multi-user deployment best practices
- Performance tuning recommendations
- API reference for new features

## 🙏 Acknowledgments

Special thanks to:
- The Gramps community for feedback
- Doug Blank for SQLite optimization work
- Contributors to the PostgreSQL extensions

## 📦 Installation

```bash
# Copy to Gramps plugins directory
cp -r PostgreSQLEnhanced ~/.local/share/gramps/gramps60/plugins/

# Install dependencies
pip install psycopg[binary]
```

## ⚠️ Known Issues

- Prepared statements pending coordination with Doug Blank's PR #2098
- Some Gramps Web features may need updates for full notification support

## 📞 Support

- GitHub Issues: https://github.com/glamberson/gramps-postgresql-enhanced
- Email: greg@aigenealogyinsights.com

---

**PostgreSQL Enhanced v1.3.0** - Enterprise-grade genealogy database backend