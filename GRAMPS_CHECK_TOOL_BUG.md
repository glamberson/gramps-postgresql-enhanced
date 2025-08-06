# Gramps Check Tool Bug Report

## Date: 2025-08-06
## Tool: Database Repair Tool (Check and Repair Database)
## File: gramps/plugins/tool/check.py

## Bug Description
The Check and Repair Database tool crashes when it encounters a reference to a non-existent family handle during the broken family links check.

## Error Details
```python
File "/usr/lib/python3/dist-packages/gramps/plugins/tool/check.py", line 724, in check_for_broken_family_links
    if family.get_father_handle() == person_handle:
       ^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'get_father_handle'
```

## Root Cause
The tool doesn't check if `family` is None before calling methods on it. When a person has a reference to a family handle that doesn't exist in the database (like 'InvalidHandle3'), the database correctly returns None, but the check tool doesn't handle this case.

## Reproduction Steps
1. Have a database with a person referencing a non-existent family handle
2. Run Tools -> Family Tree Repair -> Check and Repair Database
3. Tool crashes with AttributeError

## Code Analysis
In check.py around line 724:
```python
# Current code (BROKEN):
family = self.db.get_family_from_handle(family_handle)
if family.get_father_handle() == person_handle:  # <-- Crashes if family is None
    # ...
```

## Required Fix
```python
# Fixed code:
family = self.db.get_family_from_handle(family_handle)
if family is None:
    # Handle broken reference - add to broken links list
    self.broken_links.append((person_handle, family_handle))
    continue
if family.get_father_handle() == person_handle:
    # ...
```

## Impact
- The tool cannot complete when there are broken family references
- Users cannot repair their databases
- This affects any database backend that correctly returns None for invalid handles

## Test Case from Debug Log
- Successfully processed 441,342+ reference inserts
- Crashed on family handle 'InvalidHandle3'
- Person handle: ff4fc84bb3962549ee79ac44e0b

## PostgreSQL Addon Behavior
The PostgreSQL Enhanced addon is working correctly:
1. Returns None for non-existent handles (as per API contract)
2. Logs the attempt: `Getting family with handle: InvalidHandle3`
3. Handles the exception gracefully

## Upstream Bug Report
This should be reported to Gramps as a bug in the check tool, not the database backend.

## Workaround Options
1. **Fix in Gramps**: Add null checks in check.py (correct solution)
2. **Addon workaround**: Could return empty Family object instead of None (not recommended - violates API contract)
3. **Pre-check**: Run a query to find and remove broken references before running check tool

## Related Code Locations
- `/usr/lib/python3/dist-packages/gramps/plugins/tool/check.py:724`
- Similar null check issues may exist in other methods:
  - check_for_broken_family_links()
  - check_parent_relationships()
  - check_events()

## Recommendation
Submit bug report to Gramps project with:
1. This analysis
2. Proposed fix adding null checks
3. Test database demonstrating the issue