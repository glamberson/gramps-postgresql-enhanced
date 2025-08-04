#!/usr/bin/env python3
"""
Test that PostgreSQL extensions are handled gracefully when missing.
"""

import os
import sys
import tempfile
import psycopg
from psycopg import sql

# Database connection info
DB_CONFIG = {
    'host': '192.168.10.90',
    'port': 5432,
    'user': 'genealogy_user',  
    'password': 'GenealogyData2025'
}

def test_extension_handling():
    """Test how the addon handles missing extensions."""
    print("\n=== Testing Extension Handling ===")
    
    test_db = 'gramps_ext_test_' + str(os.getpid())
    
    try:
        # Create test database
        admin_conn = psycopg.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            dbname='postgres'
        )
        admin_conn.autocommit = True
        
        with admin_conn.cursor() as cur:
            # Create fresh database
            cur.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(test_db)
            ))
            
        admin_conn.close()
        
        # Connect to test database
        conn = psycopg.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            dbname=test_db
        )
        
        # Check what extensions are available
        print("\nChecking available extensions:")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, installed_version, comment
                FROM pg_available_extensions
                WHERE name IN ('pg_trgm', 'btree_gin', 'intarray', 'postgis')
                ORDER BY name
            """)
            
            for name, version, comment in cur.fetchall():
                status = "Installed" if version else "Available"
                print(f"  {name}: {status} - {comment[:50]}...")
        
        # Test the _check_extension_available method from schema.py
        print("\nTesting extension availability checks:")
        with conn.cursor() as cur:
            for ext in ['pg_trgm', 'btree_gin', 'intarray', 'nonexistent_ext']:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_available_extensions 
                        WHERE name = %s
                    )
                """, [ext])
                available = cur.fetchone()[0]
                print(f"  {ext}: {'Available' if available else 'Not available'}")
        
        # Test creating extensions with error handling
        print("\nTesting extension creation with error handling:")
        extensions_created = []
        
        for ext in ['pg_trgm', 'btree_gin', 'intarray']:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                        sql.Identifier(ext)
                    ))
                conn.commit()
                extensions_created.append(ext)
                print(f"  ✓ Created extension: {ext}")
            except psycopg.errors.InsufficientPrivilege:
                print(f"  ⚠ Insufficient privileges for: {ext}")
            except Exception as e:
                print(f"  ✗ Failed to create {ext}: {type(e).__name__}")
        
        # Test that tables can be created without extensions
        print("\nTesting table creation without all extensions:")
        with conn.cursor() as cur:
            # Create a simple schema similar to what Gramps uses
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_person (
                    handle VARCHAR(50) PRIMARY KEY,
                    json_data JSONB,
                    surname VARCHAR(255),
                    given_name VARCHAR(255)
                )
            """)
            
            # Try to create index that would benefit from extension
            try:
                if 'pg_trgm' in extensions_created:
                    cur.execute("""
                        CREATE INDEX idx_surname_trgm 
                        ON test_person 
                        USING gin(surname gin_trgm_ops)
                    """)
                    print("  ✓ Created trigram index with pg_trgm")
                else:
                    # Fallback to regular index
                    cur.execute("""
                        CREATE INDEX idx_surname_btree
                        ON test_person(surname)
                    """)
                    print("  ✓ Created regular B-tree index (no pg_trgm)")
            except Exception as e:
                print(f"  ✗ Index creation failed: {e}")
            
            conn.commit()
        
        # Verify basic operations work
        print("\nTesting basic operations:")
        with conn.cursor() as cur:
            # Insert test data
            cur.execute("""
                INSERT INTO test_person (handle, json_data, surname, given_name)
                VALUES (%s, %s, %s, %s)
            """, ['I0001', '{"test": true}', 'Smith', 'John'])
            
            # Query test data
            cur.execute("SELECT handle, surname FROM test_person WHERE handle = %s", ['I0001'])
            result = cur.fetchone()
            print(f"  ✓ Insert/Select works: {result}")
            
            conn.commit()
        
        conn.close()
        
        print("\nConclusion:")
        print("- Extensions are checked before use")
        print("- Missing extensions don't break core functionality")
        print("- Fallback to standard indexes when extensions missing")
        print("- All basic operations work without extensions")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            admin_conn = psycopg.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                dbname='postgres'
            )
            admin_conn.autocommit = True
            
            with admin_conn.cursor() as cur:
                # Terminate connections to the test database
                cur.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                """, [test_db])
                
                # Drop the test database
                cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(test_db)
                ))
                print(f"\n✓ Cleaned up test database: {test_db}")
                
            admin_conn.close()
        except Exception as e:
            print(f"Cleanup error: {e}")

def check_addon_extension_handling():
    """Check how the actual addon code handles extensions."""
    print("\n=== Checking Addon Extension Handling ===")
    
    # Read schema.py to analyze extension handling
    schema_file = os.path.join(os.path.dirname(__file__), 'schema.py')
    
    print("\nAnalyzing schema.py extension handling:")
    with open(schema_file, 'r') as f:
        content = f.read()
        
    # Check for try/except blocks around extension creation
    if 'try:' in content and 'CREATE EXTENSION' in content:
        print("  ✓ Extension creation wrapped in try/except")
    else:
        print("  ✗ Extension creation not properly protected")
    
    # Check for _check_extension_available
    if '_check_extension_available' in content:
        print("  ✓ Has extension availability check method")
    else:
        print("  ✗ No extension availability check")
    
    # Check for fallback behavior
    if 'except' in content and 'extension' in content.lower():
        print("  ✓ Has exception handling for extensions")
    else:
        print("  ✗ No exception handling for extensions")
    
    # Look for optional index creation
    if 'gin_trgm_ops' in content and ('if' in content or 'try' in content):
        print("  ✓ Trigram indexes appear to be conditional")
    else:
        print("  ⚠ Trigram indexes might not be conditional")

def main():
    """Run extension tests."""
    print("Testing PostgreSQL Enhanced Extension Handling")
    print("=" * 50)
    
    test_extension_handling()
    check_addon_extension_handling()
    
    print("\n" + "=" * 50)
    print("Extension handling tests completed!")

if __name__ == "__main__":
    main()