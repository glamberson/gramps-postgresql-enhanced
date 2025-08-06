# PostgreSQL Enhanced - URGENT Recovery Required

## ⚠️ CRITICAL: Read This First
The gramps-postgresql-enhanced addon is currently BROKEN due to a catastrophic commit that destroyed working functionality. This session needs to execute a careful recovery plan.

## Essential Context
1. **Location**: `/home/greg/gramps-postgresql-enhanced/`
2. **Status**: Monolithic mode BROKEN, Separate mode working
3. **Root Cause**: Commit ec231d7 deleted 29,000+ lines of working code claiming it was "mocks"
4. **Solution**: Revert to commit d777c70 and rebuild

## NO FALLBACK Policy (MANDATORY)
- NEVER accept partial solutions
- NEVER silence errors or skip tests  
- NEVER simplify functionality
- ALWAYS fix root causes
- ALWAYS run ALL tests (20+ files, not just 3)

## Your First Actions
1. `cd /home/greg/gramps-postgresql-enhanced`
2. Read `CRITICAL_HANDOVER_AND_RECOVERY_PLAN.md` 
3. Read `COMMIT_ANALYSIS_FOR_REVERT.md`
4. Create backup: `git branch backup-$(date +%Y%m%d-%H%M%S)`
5. Execute revert: `git checkout d777c70`

## The Recovery Process
```bash
# 1. Revert to working state
git checkout d777c70
git checkout -b recovery-branch

# 2. Apply ONLY the SQL fix
git cherry-pick 3266153

# 3. Verify ALL tests pass
python test_monolithic_comprehensive.py
python test_database_modes.py
python test_data_validation.py

# 4. Only if ALL pass, update master
git checkout master
git reset --hard recovery-branch
```

## What You Must Understand
- The "mock" system (mock_gramps.py) is NOT a mock - it's a real test framework
- The deleted tests were testing REAL database operations
- Commit ec231d7's claim of "100% production ready" was false
- The system WAS working before that commit

## Success Criteria
- ✅ test_monolithic_comprehensive.py passes (805 lines)
- ✅ test_database_modes.py passes  
- ✅ Both separate AND monolithic modes work
- ✅ Table prefixes work correctly in monolithic mode
- ✅ No "fixes" that skip or simplify tests

## Do NOT
- ❌ Delete mock_gramps.py
- ❌ Remove any test files
- ❌ Cherry-pick ec231d7 or 03ef7b9
- ❌ Claim success with only 3 tests passing
- ❌ Make any "cleanup" that removes functionality

Remember: This is a RECOVERY from a disaster, not an improvement session.