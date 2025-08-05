#!/usr/bin/env python3
"""
Simple test to verify basic database operations work.
Tests at the SQL level to bypass mock issues.
"""

import os
import sys
import tempfile
import shutil
import psycopg
from psycopg import sql
from psycopg.types.json import Json

# Add plugin directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}

def test_direct_sql_operations():
    """Test direct SQL operations to verify database connectivity."""
    print("=== Testing Direct SQL Operations ===\n")
    
    test_db = "gramps_test_sql_ops"
    
    try:
        # Create test database
        print(f"1. Creating test database {test_db}...")
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
            autocommit=True
        )
        
        with admin_conn.cursor() as cur:
            # Drop if exists
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db)))
            # Create new
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db)))
            print("   ✓ Database created")
        
        admin_conn.close()
        
        # Connect to test database
        print(f"\n2. Connecting to {test_db}...")
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=test_db
        )
        print("   ✓ Connected")
        
        # Create a simple table
        print("\n3. Creating test table...")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE test_person (
                    handle TEXT PRIMARY KEY,
                    json_data JSONB,
                    gramps_id TEXT,
                    given_name TEXT,
                    surname TEXT
                )
            """)
            conn.commit()
            print("   ✓ Table created")
        
        # Insert test data
        print("\n4. Inserting test data...")
        test_data = [
            ("HANDLE001", {"name": "John Smith"}, "I0001", "John", "Smith"),
            ("HANDLE002", {"name": "Jane Doe"}, "I0002", "Jane", "Doe"),
            ("HANDLE003", {"name": "Bob Wilson"}, "I0003", "Bob", "Wilson")
        ]
        
        with conn.cursor() as cur:
            for handle, json_data, gramps_id, given, surname in test_data:
                cur.execute(
                    """
                    INSERT INTO test_person (handle, json_data, gramps_id, given_name, surname)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (handle, Json(json_data), gramps_id, given, surname)
                )
            conn.commit()
            print(f"   ✓ Inserted {len(test_data)} records")
        
        # Query data back
        print("\n5. Querying data...")
        with conn.cursor() as cur:
            cur.execute("SELECT handle, given_name, surname FROM test_person ORDER BY handle")
            rows = cur.fetchall()
            print(f"   ✓ Found {len(rows)} records:")
            for row in rows:
                print(f"     - {row[0]}: {row[1]} {row[2]}")
        
        # Test JSONB query
        print("\n6. Testing JSONB query...")
        with conn.cursor() as cur:
            cur.execute("SELECT handle FROM test_person WHERE json_data->>'name' LIKE '%Smith%'")
            rows = cur.fetchall()
            print(f"   ✓ Found {len(rows)} records with 'Smith' in JSON data")
        
        # Test table prefix simulation
        print("\n7. Testing table prefix simulation...")
        prefix = "tree1_"
        
        with conn.cursor() as cur:
            # Create prefixed table
            cur.execute(sql.SQL("""
                CREATE TABLE {} (
                    handle TEXT PRIMARY KEY,
                    json_data JSONB
                )
            """).format(sql.Identifier(f"{prefix}person")))
            
            # Insert into prefixed table
            cur.execute(
                sql.SQL("INSERT INTO {} (handle, json_data) VALUES (%s, %s)").format(
                    sql.Identifier(f"{prefix}person")
                ),
                ("PREFIX001", Json({"test": "data"}))
            )
            conn.commit()
            
            # Query from prefixed table
            cur.execute(sql.SQL("SELECT handle FROM {}").format(sql.Identifier(f"{prefix}person")))
            rows = cur.fetchall()
            print(f"   ✓ Prefixed table {prefix}person works correctly")
        
        # Clean up connection
        conn.close()
        
        # Drop test database
        print("\n8. Cleaning up...")
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
            autocommit=True
        )
        
        with admin_conn.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(test_db)))
        admin_conn.close()
        print("   ✓ Test database dropped")
        
        print("\n✅ All direct SQL operations successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to clean up
        try:
            admin_conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname="postgres",
                autocommit=True
            )
            with admin_conn.cursor() as cur:
                cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db)))
            admin_conn.close()
        except:
            pass
        
        return False

def test_plugin_config_loading():
    """Test that the plugin can load configuration correctly."""
    print("\n\n=== Testing Plugin Configuration Loading ===\n")
    
    # Import after setting up mocks
    import mock_gramps
    from postgresqlenhanced import PostgreSQLEnhanced
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_config_")
    tree_name = "config_test"
    tree_path = os.path.join(temp_dir, tree_name)
    os.makedirs(tree_path, exist_ok=True)
    
    # Create config file
    config_file = os.path.join(tree_path, "connection_info.txt")
    with open(config_file, "w") as f:
        f.write(f"""# Test configuration
host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = separate
database_name = config_test_db
""")
    
    try:
        # Create plugin instance
        print("1. Creating PostgreSQLEnhanced instance...")
        plugin = PostgreSQLEnhanced()
        print("   ✓ Instance created")
        
        # Test config loading
        print("\n2. Loading configuration...")
        config = plugin._load_connection_config(tree_path)
        print("   ✓ Configuration loaded:")
        for key, value in config.items():
            if key == "password":
                print(f"     {key}: ***")
            else:
                print(f"     {key}: {value}")
        
        # Verify config values
        assert config["host"] == DB_CONFIG["host"]
        assert config["database_mode"] == "separate"
        assert config["database_name"] == "config_test_db"
        print("\n   ✓ Configuration values correct")
        
        print("\n✅ Configuration loading successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Test 1: Direct SQL operations
    sql_ok = test_direct_sql_operations()
    
    # Test 2: Configuration loading
    config_ok = test_plugin_config_loading()
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Direct SQL Operations: {'✅ PASSED' if sql_ok else '❌ FAILED'}")
    print(f"Configuration Loading: {'✅ PASSED' if config_ok else '❌ FAILED'}")
    
    if sql_ok and config_ok:
        print("\n✅ All basic tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)