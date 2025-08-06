# Proposed JSONSerializer Improvement for Gramps

## Problem

The current JSONSerializer in Gramps assumes it will always receive JSON as a string:

```python
def string_to_data(string):
    LOG.debug("json, string_to_data: %r...", string[:65])  # Fails if not a string!
    return string_to_data(string)
```

However, modern PostgreSQL adapters (psycopg3, asyncpg) automatically convert JSONB columns to Python dict/list objects for convenience. This causes a KeyError when trying to slice what is actually a dict/list.

## Proposed Fix

Make JSONSerializer more robust by handling both strings and already-parsed objects:

```python
@staticmethod
def string_to_data(data):
    """Convert JSON string or already-parsed data to internal format."""
    if isinstance(data, str):
        # Traditional path - parse JSON string
        LOG.debug("json, string_to_data: %r...", data[:65])
        return string_to_data(data)
    elif isinstance(data, (dict, list)):
        # Modern PostgreSQL adapters return parsed data
        LOG.debug("json, string_to_data: already parsed %s", type(data).__name__)
        return DataDict(data) if isinstance(data, dict) else data
    elif isinstance(data, bytes):
        # Handle bytes (UTF-8 encoded JSON)
        LOG.debug("json, string_to_data: bytes %r...", data[:65])
        return string_to_data(data.decode('utf-8'))
    else:
        raise TypeError(f"Expected str, bytes, dict or list, got {type(data).__name__}")
```

## Benefits

1. **Backward Compatible** - Still works with existing SQLite backend
2. **Modern PostgreSQL Support** - Works with psycopg3, asyncpg
3. **Better Performance** - Avoids unnecessary JSON parsing/serialization roundtrip
4. **Future Proof** - Other databases may also return native types

## Alternative Approaches

1. **Type Check in DBAPI** - Check data type before calling serializer
2. **Backend-Specific Serializers** - PostgreSQL could use a different serializer
3. **Configuration Option** - Let backends specify if they return strings or objects

## Testing

The fix should be tested with:
- SQLite backend (existing functionality)
- PostgreSQL with psycopg2 (returns strings)
- PostgreSQL with psycopg3 (returns objects)
- BSDDB backend (if still supported)