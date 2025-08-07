#!/usr/bin/env python3
"""
Test PostgreSQL Enhanced Gramps Web Compatibility

This script verifies that PostgreSQL Enhanced has all required methods
and functionality for Gramps Web integration.
"""

import os
import sys
import tempfile
import traceback
from pathlib import Path

# Add the addon directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up test environment variables to simulate Gramps Web
TEST_ENV = {
    'GRAMPSWEB_TREE': '*',
    'GRAMPSWEB_POSTGRES_HOST': '192.168.10.90',
    'GRAMPSWEB_POSTGRES_PORT': '5432',
    'GRAMPSWEB_POSTGRES_DB': 'henderson_unified',
    'GRAMPSWEB_POSTGRES_USER': 'genealogy_user',
    'GRAMPSWEB_POSTGRES_PASSWORD': 'GenealogyData2025',
    'POSTGRESQL_ENHANCED_MODE': 'monolithic',  # Test monolithic mode
}

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def print_test(name, success, message=""):
    """Print test result"""
    symbol = "✅" if success else "❌"
    status = "PASS" if success else "FAIL"
    print(f"{symbol} {name:40} [{status}]")
    if message:
        print(f"   {message}")

def test_basic_compatibility():
    """Test basic Gramps Web compatibility"""
    print_header("Testing PostgreSQL Enhanced Gramps Web Compatibility")
    
    # Set environment variables
    for key, value in TEST_ENV.items():
        os.environ[key] = value
    
    results = []
    
    # Test 1: Import the module
    print("\n1. Module Import Test")
    try:
        from postgresqlenhanced import PostgreSQLEnhanced
        print_test("Module import", True)
        results.append(True)
    except Exception as e:
        print_test("Module import", False, str(e))
        print(traceback.format_exc())
        return False
    
    # Test 2: Check required methods exist
    print("\n2. Required Methods Test")
    required_methods = [
        'get_dbid',
        'get_dbname', 
        'get_summary',
        '_detect_grampsweb_environment',
        'is_read_only',
        'get_mediapath',
        'set_mediapath',
    ]
    
    for method in required_methods:
        if hasattr(PostgreSQLEnhanced, method):
            print_test(f"Method {method}", True)
            results.append(True)
        else:
            print_test(f"Method {method}", False, "Method not found")
            results.append(False)
    
    # Test 3: Check class methods
    print("\n3. Class Methods Test")
    class_methods = ['create_tree', 'list_trees']
    
    for method in class_methods:
        if hasattr(PostgreSQLEnhanced, method):
            print_test(f"Class method {method}", True)
            results.append(True)
        else:
            print_test(f"Class method {method}", False, "Class method not found")
            results.append(False)
    
    # Test 4: Create test instance
    print("\n4. Instance Creation Test")
    test_dir = None
    try:
        # Create test directory
        test_dir = tempfile.mkdtemp(prefix='gramps_test_')
        
        # Write test configuration
        config_file = os.path.join(test_dir, 'connection_info.txt')
        with open(config_file, 'w') as f:
            f.write("""
# Test configuration
host = 192.168.10.90
port = 5432
user = genealogy_user
password = GenealogyData2025
database_mode = monolithic
monolithic_database = test_db
tree_prefix = test_
""")
        
        # Create instance
        db = PostgreSQLEnhanced()
        print_test("Instance creation", True)
        results.append(True)
        
        # Test 5: Check Gramps Web detection
        print("\n5. Gramps Web Detection Test")
        if hasattr(db, 'grampsweb_active'):
            if db.grampsweb_active:
                print_test("Gramps Web environment detected", True)
                results.append(True)
            else:
                print_test("Gramps Web environment detected", False, 
                          "Environment variables set but not detected")
                results.append(False)
        else:
            print_test("Gramps Web environment detected", False,
                      "grampsweb_active attribute missing")
            results.append(False)
        
        # Test 6: Test method execution
        print("\n6. Method Execution Test")
        
        # Test get_dbid (should work without database connection)
        try:
            # We can't call get_dbid without proper initialization,
            # but we can verify the method exists and is callable
            if callable(getattr(db, 'get_dbid', None)):
                print_test("get_dbid() callable", True)
                results.append(True)
            else:
                print_test("get_dbid() callable", False, "Method not callable")
                results.append(False)
        except Exception as e:
            print_test("get_dbid() callable", False, str(e))
            results.append(False)
        
        # Test get_dbname
        try:
            if callable(getattr(db, 'get_dbname', None)):
                # Call should work even without full initialization
                name = db.get_dbname()
                print_test("get_dbname() callable", True, f"Returns: {name}")
                results.append(True)
            else:
                print_test("get_dbname() callable", False, "Method not callable")
                results.append(False)
        except Exception as e:
            print_test("get_dbname() callable", False, str(e))
            results.append(False)
        
        # Test is_read_only
        try:
            readonly = db.is_read_only()
            print_test("is_read_only() callable", True, f"Returns: {readonly}")
            results.append(True)
        except Exception as e:
            print_test("is_read_only() callable", False, str(e))
            results.append(False)
        
    except Exception as e:
        print_test("Instance creation", False, str(e))
        print(traceback.format_exc())
        results.append(False)
    finally:
        # Clean up test directory
        if test_dir and os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
    
    # Test 7: Registration file check
    print("\n7. Registration File Test")
    try:
        import postgresqlenhanced_gpr as gpr_module
        # Check if features is defined (might not be in older versions)
        print_test("Registration file import", True)
        results.append(True)
    except:
        # Try alternate import
        try:
            exec(open('postgresqlenhanced.gpr.py').read())
            print_test("Registration file import", True, "Via exec")
            results.append(True)
        except Exception as e:
            print_test("Registration file import", False, str(e))
            results.append(False)
    
    # Summary
    print_header("Test Summary")
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! PostgreSQL Enhanced is Gramps Web compatible.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the failures above.")
        return False

def test_multi_tree_support():
    """Test multi-tree support capabilities"""
    print_header("Testing Multi-Tree Support")
    
    try:
        from postgresqlenhanced import PostgreSQLEnhanced
        
        # Test create_tree
        print("\n1. Testing create_tree() class method")
        if hasattr(PostgreSQLEnhanced, 'create_tree'):
            print_test("create_tree exists", True)
            # We can't actually create a tree without database access
            # but we can verify the method signature
            import inspect
            sig = inspect.signature(PostgreSQLEnhanced.create_tree)
            params = list(sig.parameters.keys())
            expected = ['tree_id', 'name']
            if all(p in params for p in expected):
                print_test("create_tree signature", True, f"Parameters: {params}")
            else:
                print_test("create_tree signature", False, 
                          f"Expected {expected}, got {params}")
        else:
            print_test("create_tree exists", False)
        
        # Test list_trees
        print("\n2. Testing list_trees() class method")
        if hasattr(PostgreSQLEnhanced, 'list_trees'):
            print_test("list_trees exists", True)
            # Try to call it (should return empty list or handle gracefully)
            try:
                trees = PostgreSQLEnhanced.list_trees()
                print_test("list_trees callable", True, 
                          f"Returns: {type(trees).__name__} with {len(trees)} items")
            except Exception as e:
                print_test("list_trees callable", False, str(e))
        else:
            print_test("list_trees exists", False)
            
    except Exception as e:
        print(f"Error in multi-tree test: {e}")
        print(traceback.format_exc())

def main():
    """Main test runner"""
    print("\n" + "=" * 60)
    print("PostgreSQL Enhanced - Gramps Web Compatibility Test Suite")
    print("=" * 60)
    
    # Run basic compatibility tests
    basic_success = test_basic_compatibility()
    
    # Run multi-tree support tests
    test_multi_tree_support()
    
    # Final summary
    print_header("Final Status")
    if basic_success:
        print("✅ PostgreSQL Enhanced is ready for Gramps Web!")
        print("\nNext steps:")
        print("1. Deploy to Gramps plugins directory")
        print("2. Configure Gramps Web to use 'postgresqlenhanced' backend")
        print("3. Test with actual Gramps Web instance")
        return 0
    else:
        print("❌ Some compatibility issues found. Please review and fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())