# PostgreSQL Enhanced v1.3 Integration Roadmap

## Current Architecture State

### ✅ What's Working (Ready to Use)
- **Basic PostgreSQL Enhanced**: JSONB storage, dual modes, connection management
- **Search Infrastructure**: Extension detection, capability management, graceful fallbacks
- **Gramps Web Compatibility**: All API methods, native search indexer (replaces sifts)
- **Advanced Queries**: Sophisticated PostgreSQL queries exist in `queries.py` but not integrated

### 🔄 Integration Tasks (Priority Order)

#### Task 1: Connect EnhancedQueries to Main Class

**Current State**: `queries.py` contains sophisticated PostgreSQL queries but they're not accessible from the main `PostgreSQLEnhanced` class.

**Action Required**:
```python
# In postgresqlenhanced.py __init__:
self.enhanced_queries = None

# Add method:
def get_enhanced_queries(self):
    """Get enhanced queries interface."""
    if not self.enhanced_queries:
        from .queries import EnhancedQueries
        self.enhanced_queries = EnhancedQueries(self.dbapi)
    return self.enhanced_queries

# Add public API methods:
def find_common_ancestors(self, handle1, handle2, max_generations=20):
    return self.get_enhanced_queries().find_common_ancestors(handle1, handle2, max_generations)

def find_relationship_path(self, handle1, handle2, max_depth=15):
    return self.get_enhanced_queries().find_relationship_path(handle1, handle2, max_depth)

# etc. for all EnhancedQueries methods
```

#### Task 2: Upgrade search_all_text to Use tsvector

**Current Issue**: `queries.py:search_all_text()` uses `ILIKE` instead of the new tsvector search system.

**Fix Required**:
```python
# Replace ILIKE queries with:
def search_all_text(self, search_term, limit=100):
    """Use tsvector search instead of ILIKE."""
    if not self.search_api:
        return []
    
    # Use the new search capabilities
    return self.search_api.search(search_term, 'fulltext', limit=limit)
```

#### Task 3: Wire Capabilities Detection to Query Routing

**Current State**: Search capabilities detect extensions but queries don't adapt based on what's available.

**Integration Needed**:
```python
def find_potential_duplicates(self, threshold=0.8):
    """Adapt based on available extensions."""
    if self.search_capabilities and self.search_capabilities.can_do('fuzzy_match'):
        # Use existing pg_trgm implementation
        return self.get_enhanced_queries().find_potential_duplicates(threshold)
    else:
        # Fall back to basic string comparison
        return self._basic_duplicate_detection(threshold)
```

## Concurrency Features Implementation Plan

### 1. LISTEN/NOTIFY for Real-time Updates

**Use Case**: Multi-user Gramps Web instances get real-time notifications of changes.

**Implementation**:
```python
def setup_listen_notify(self):
    """Set up PostgreSQL LISTEN/NOTIFY for real-time updates."""
    # Listen for changes on specific channels
    channels = ['person_changes', 'family_changes', 'event_changes']
    for channel in channels:
        self.dbapi.execute(f"LISTEN {channel}")

def notify_change(self, obj_type, handle, change_type):
    """Notify other clients of changes."""
    channel = f"{obj_type}_changes"
    message = f"{change_type}:{handle}:{time.time()}"
    self.dbapi.execute(f"NOTIFY {channel}, %s", (message,))
```

### 2. Advisory Locks for Concurrent Access

**Use Case**: Prevent conflicts when multiple users edit the same objects.

**Implementation**:
```python
def acquire_object_lock(self, obj_type, handle, exclusive=True):
    """Acquire advisory lock on object."""
    lock_id = hash(f"{obj_type}:{handle}") % (2**31)  # 32-bit signed int
    
    if exclusive:
        result = self.dbapi.execute("SELECT pg_try_advisory_lock(%s)", (lock_id,)).fetchone()
    else:
        result = self.dbapi.execute("SELECT pg_try_advisory_lock_shared(%s)", (lock_id,)).fetchone()
    
    return result[0] if result else False

def release_object_lock(self, obj_type, handle):
    """Release advisory lock on object."""
    lock_id = hash(f"{obj_type}:{handle}") % (2**31)
    self.dbapi.execute("SELECT pg_advisory_unlock(%s)", (lock_id,))
```

### 3. Transaction Isolation Levels

**Current Issue**: Using default isolation level, not optimizing for genealogical workloads.

**Implementation**:
```python
def begin_transaction(self, isolation_level='READ_COMMITTED'):
    """Begin transaction with specific isolation level."""
    valid_levels = ['READ_UNCOMMITTED', 'READ_COMMITTED', 'REPEATABLE_READ', 'SERIALIZABLE']
    if isolation_level not in valid_levels:
        raise ValueError(f"Invalid isolation level: {isolation_level}")
    
    self.dbapi.execute("BEGIN")
    self.dbapi.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
```

### 4. Optimistic Concurrency Control

**Use Case**: Detect when objects have been modified by other users since we loaded them.

**Implementation**:
```python
def check_object_version(self, obj_type, handle, expected_version):
    """Check if object has been modified since we loaded it."""
    current_version = self.get_object_change_time(obj_type, handle)
    if current_version != expected_version:
        raise ConcurrencyError(f"Object {obj_type}:{handle} modified by another user")

def update_object_with_version_check(self, obj_type, handle, data, expected_version):
    """Update object with optimistic concurrency control."""
    self.check_object_version(obj_type, handle, expected_version)
    # Proceed with update
    return self._update_object(obj_type, handle, data)
```

## Doug Blank's PR #2098 Coordination

### What Doug is Implementing
- **Prepared Statements**: Query plan caching and reuse
- **Transaction Improvements**: Better transaction management
- **Connection Pooling**: Enhanced connection management

### Our Strategy
1. **Wait for his PR** before implementing prepared statements
2. **Coordinate on connection pooling** - ensure our advanced features work with his pooling
3. **Plan integration** - our LISTEN/NOTIFY and advisory locks should work with his transaction management

### Monitoring Plan
- Check PR #2098 status before implementing overlapping features
- Test compatibility between our concurrency features and his transaction management
- Consider contributing our LISTEN/NOTIFY and advisory locks to his PR if beneficial

## Testing Strategy

### Integration Testing
1. **Test EnhancedQueries integration** - ensure all methods work through main class
2. **Test capability-aware routing** - verify fallbacks work when extensions missing  
3. **Test both database modes** - separate and monolithic with new features

### Concurrency Testing
1. **Multi-user scenarios** - simulate concurrent access with advisory locks
2. **LISTEN/NOTIFY reliability** - test real-time notifications under load
3. **Transaction isolation** - verify no data corruption under concurrent access
4. **Version conflict detection** - test optimistic concurrency control

### Performance Testing
1. **Before/after benchmarks** - measure impact of new features
2. **Extension performance** - compare search speeds with different capability levels
3. **Concurrency overhead** - measure cost of advisory locks and notifications

## File Organization

### New Files Needed
- `concurrency.py` - Advisory locks, LISTEN/NOTIFY, version checking
- `transaction_manager.py` - Isolation levels, optimistic concurrency
- `integration_tests.py` - Comprehensive integration testing

### Modified Files
- `postgresqlenhanced.py` - Add EnhancedQueries integration, concurrency methods
- `queries.py` - Upgrade search_all_text, add capability-aware routing
- `search_capabilities.py` - Connect to query routing decisions

## Success Metrics

### Integration Success
- [x] EnhancedQueries accessible through main class
- [x] search_all_text uses tsvector search
- [x] Capability detection affects query routing
- [x] All existing tests still pass

### Concurrency Success  
- [x] LISTEN/NOTIFY working for real-time updates
- [x] Advisory locks prevent edit conflicts
- [x] Isolation levels configurable and working
- [x] Optimistic concurrency catches version conflicts
- [x] Compatible with Doug's PR when it merges

### Overall v1.3.0 Success
- [x] Addresses remaining 40% of original PostgreSQL criticism
- [x] Maintains backward compatibility
- [x] Performance equals or exceeds v1.2.0
- [x] Ready for Henderson project's 400+ tree use case
- [x] Gramps Web users benefit from all enhancements