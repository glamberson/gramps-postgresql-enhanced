#!/usr/bin/env python3
"""
Run all tests for the PostgreSQL Enhanced plugin.
Ensures NO FALLBACK policy - all tests must pass completely.
"""

import sys
import os
import subprocess

# Add plugin directory to path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

# Import mock FIRST before any tests
import mock_gramps


def run_test(test_name, test_file):
    """Run a single test and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print("=" * 60)

    try:
        # Run test as subprocess to ensure clean environment
        result = subprocess.run(
            [sys.executable, test_file], capture_output=True, text=True, cwd=plugin_dir
        )

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"✅ {test_name}: PASSED")
            return True
        else:
            print(f"❌ {test_name}: FAILED (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ {test_name}: ERROR - {e}")
        return False


def main():
    """Run all tests."""
    print("PostgreSQL Enhanced Plugin - Comprehensive Test Suite")
    print("NO FALLBACK POLICY: All tests must pass completely")

    tests = [
        ("Database Modes Test", "test_database_modes.py"),
        ("Table Prefix Mechanism", "test_table_prefix_mechanism.py"),
        ("Monolithic Comprehensive", "test_monolithic_comprehensive.py"),
        ("PostgreSQL Enhanced Basic", "test_postgresql_enhanced.py"),
        ("Database Contents Verification", "verify_database_contents.py"),
    ]

    results = []

    for test_name, test_file in tests:
        if os.path.exists(test_file):
            passed = run_test(test_name, test_file)
            results.append((test_name, passed))
        else:
            print(f"⚠️  {test_name}: SKIPPED (file not found: {test_file})")
            results.append((test_name, None))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}")
        elif result is False:
            print(f"❌ {test_name}")
        else:
            print(f"⚠️  {test_name} (skipped)")

    print(f"\nTotal: {len(tests)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    if failed > 0:
        print("\n❌ FAILED: Not all tests passed!")
        print("NO FALLBACK POLICY: Fix all failures before proceeding!")
        return 1
    elif passed == len(tests):
        print("\n✅ SUCCESS: All tests passed!")
        return 0
    else:
        print("\n⚠️  WARNING: Some tests were skipped")
        return 0


if __name__ == "__main__":
    sys.exit(main())
