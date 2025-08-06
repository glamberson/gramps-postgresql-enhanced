# Linting Errors Fixed - PostgreSQL Enhanced Addon

## Date: 2025-08-06

## Background
On commit 47e7247, an attempt was made to lint all plugin files to remove f-strings and trailing whitespace for Gramps compatibility. This blanket conversion broke the addon in multiple critical ways.

## Critical Finding
**F-strings CANNOT be blindly converted to % formatting**. Many f-strings are required for runtime interpolation where variables are only available during execution, not at definition time.

## Errors Found and Fixed

### 1. SQL Query String Interpolation (schema.py)
**Error**: SQL queries with `{self._table_name('metadata')}` were not being interpolated
**Location**: schema.py lines 143, 155, 169, 183, 190, 197, 286, 300, 308, 319, 336, 344, 354, 364, 374, 384, 403, 501, 513
**Symptom**: `psycopg.errors.SyntaxError: syntax error at or near "{"`
**Fix**: Restored f-string prefixes to all SQL query strings
**Commit**: cd342d4

### 2. Lambda Functions with Runtime Variables (postgresqlenhanced.py)
**Error**: Lambda functions using `{self._prefix}` and `{m.group()}` broken
**Location**: postgresqlenhanced.py lines 1238, 1275 (and duplicates at 1370, 1407)
**Original**:
```python
lambda m: f"SELECT {m.group(1)} FROM {self._prefix}{m.group(2)}"
```
**Broken by linting**:
```python
lambda m: "SELECT %(val)s FROM {self._prefix}{m.group(2)}" % {"val": m.group(1)}
```
**Fix**: Restored f-strings for lambda functions
**Commit**: 25b9058

### 3. Mixed SQL Parameters and String Formatting (postgresqlenhanced.py)
**Error**: Mixing SQL parameter placeholders (%s) with Python string formatting
**Location**: postgresqlenhanced.py lines 1079, 1092
**Broken**:
```python
"SELECT 1 FROM %(val)smetadata WHERE setting = %s" % {"val": self.table_prefix}, [key]
```
**Fix**: Use f-string for prefix, keep %s for SQL parameter:
```python
f"SELECT 1 FROM {self.table_prefix}metadata WHERE setting = %s", [key]
```
**Commit**: 9bb9695

### 4. UPDATE Query Generation (postgresqlenhanced.py)
**Error**: Table name and json_path variables not interpolated in UPDATE queries
**Location**: postgresqlenhanced.py lines 667, 675
**Symptom**: `psycopg.errors.SyntaxError: syntax error at or near "{"`
**Broken**:
```python
table_name = "%(val)s{table}" % {"val": self.table_prefix}
sets.append("%s = ({json_path})" % col_name)
```
**Fix**:
```python
table_name = f"{self.table_prefix}{table}"
sets.append(f"{col_name} = ({json_path})")
```
**Commit**: 0b751c0

## Lessons Learned

### When F-strings Are REQUIRED:
1. **Runtime variable interpolation** - When variables like `m.group()` only exist at execution time
2. **Lambda functions** - Variables in lambda scope need runtime evaluation
3. **Dynamic SQL generation** - Table names and column paths that vary at runtime
4. **Mixed formatting contexts** - When SQL parameters (%s) and Python variables coexist

### When % Formatting Works:
1. **Static string formatting** - All variables available at definition time
2. **Simple substitutions** - No nested expressions or method calls
3. **Log messages** - Where lazy evaluation isn't critical

## Testing Impact
These linting errors prevented:
- Database connection and initialization
- GEDCOM import operations  
- Secondary value updates
- SQL function creation

All issues have been resolved, but comprehensive testing must continue.

## Recommendations
1. Never do blanket f-string conversions
2. Test after every linting change
3. Understand the difference between definition-time and runtime evaluation
4. Keep f-strings where runtime interpolation is needed