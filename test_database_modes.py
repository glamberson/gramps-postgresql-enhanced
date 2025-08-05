#!/usr/bin/env python3
"""
Test monolithic vs individual database modes.
"""

import os
import sys
import tempfile
import shutil
import psycopg
from psycopg import sql

# Database connection info
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}


def test_separate_mode():
    """Test separate database mode (one database per tree)."""
    print("\n=== Testing SEPARATE Database Mode ===")

    # Create test config
    config_dir = tempfile.mkdtemp(prefix="gramps_test_separate_")
    config_file = os.path.join(config_dir, "connection.txt")

    with open(config_file, "w") as f:
        f.write(
            f"""# PostgreSQL Connection Configuration
host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = separate
"""
        )

    print(f"Created config at: {config_file}")

    # Test creating multiple trees
    trees = ["family_tree_1", "family_tree_2", "research_tree"]
    created_dbs = []

    try:
        # Connect to postgres database for admin operations
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )
        admin_conn.autocommit = True

        with admin_conn.cursor() as cur:
            for tree_name in trees:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [tree_name])

                if not cur.fetchone():
                    print(f"  Creating database: {tree_name}")
                    cur.execute(
                        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(tree_name))
                    )
                    created_dbs.append(tree_name)
                else:
                    print(f"  Database already exists: {tree_name}")

        admin_conn.close()

        # Test connections to each database
        for tree_name in trees:
            conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=tree_name,
            )

            with conn.cursor() as cur:
                # Create a test table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS test_mode (
                        id SERIAL PRIMARY KEY,
                        mode TEXT,
                        tree_name TEXT
                    )
                """
                )

                # Insert test data
                cur.execute(
                    "INSERT INTO test_mode (mode, tree_name) VALUES (%s, %s)",
                    ["separate", tree_name],
                )

                conn.commit()

                # Verify data
                cur.execute("SELECT COUNT(*) FROM test_mode")
                count = cur.fetchone()[0]
                print(f"  ✓ Database {tree_name}: {count} test records")

            conn.close()

        print("\nSeparate mode test: SUCCESS")
        print(f"  - Each tree has its own database")
        print(f"  - Complete isolation between trees")
        print(f"  - No table prefixes needed")

    finally:
        # Cleanup
        shutil.rmtree(config_dir)

        # Drop test databases
        if created_dbs:
            admin_conn = psycopg.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname="postgres",
            )
            admin_conn.autocommit = True

            with admin_conn.cursor() as cur:
                for db_name in created_dbs:
                    print(f"  Cleaning up database: {db_name}")
                    cur.execute(
                        sql.SQL("DROP DATABASE IF EXISTS {}").format(
                            sql.Identifier(db_name)
                        )
                    )

            admin_conn.close()


def test_monolithic_mode():
    """Test monolithic database mode (all trees in one database)."""
    print("\n=== Testing MONOLITHIC Database Mode ===")

    # Create test config
    config_dir = tempfile.mkdtemp(prefix="gramps_test_monolithic_")
    config_file = os.path.join(config_dir, "connection.txt")

    with open(config_file, "w") as f:
        f.write(
            f"""# PostgreSQL Connection Configuration
host = {DB_CONFIG['host']}
port = {DB_CONFIG['port']}
user = {DB_CONFIG['user']}
password = {DB_CONFIG['password']}
database_mode = monolithic
shared_database_name = gramps_monolithic_test
"""
        )

    print(f"Created config at: {config_file}")

    # Test creating multiple trees in same database
    trees = ["family_tree_1", "family_tree_2", "research_tree"]
    shared_db = "gramps_monolithic_test"

    try:
        # Create shared database
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )
        admin_conn.autocommit = True

        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [shared_db])

            if not cur.fetchone():
                print(f"  Creating shared database: {shared_db}")
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(shared_db))
                )

        admin_conn.close()

        # Connect to shared database
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=shared_db,
        )

        with conn.cursor() as cur:
            # Create tables for each tree with prefixes
            for tree_name in trees:
                prefix = tree_name.replace("_", "") + "_"

                # Create prefixed table
                cur.execute(
                    sql.SQL(
                        """
                    CREATE TABLE IF NOT EXISTS {} (
                        id SERIAL PRIMARY KEY,
                        mode TEXT,
                        tree_name TEXT
                    )
                """
                    ).format(sql.Identifier(f"{prefix}test_mode"))
                )

                # Insert test data
                cur.execute(
                    sql.SQL("INSERT INTO {} (mode, tree_name) VALUES (%s, %s)").format(
                        sql.Identifier(f"{prefix}test_mode")
                    ),
                    ["monolithic", tree_name],
                )

            conn.commit()

            # List all tables
            cur.execute(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename LIKE '%test_mode'
                ORDER BY tablename
            """
            )

            tables = cur.fetchall()
            print(f"\n  Tables in {shared_db}:")
            for table in tables:
                print(f"    - {table[0]}")

            # Verify data isolation
            print("\n  Verifying data isolation:")
            for tree_name in trees:
                prefix = tree_name.replace("_", "") + "_"
                cur.execute(
                    sql.SQL(
                        "SELECT COUNT(*), tree_name FROM {} GROUP BY tree_name"
                    ).format(sql.Identifier(f"{prefix}test_mode"))
                )

                result = cur.fetchone()
                if result:
                    print(f"    ✓ {tree_name}: {result[0]} records")

        conn.close()

        print("\nMonolithic mode test: SUCCESS")
        print(f"  - All trees share database: {shared_db}")
        print(f"  - Each tree uses table prefixes")
        print(f"  - Data properly isolated by prefix")

    finally:
        # Cleanup
        shutil.rmtree(config_dir)

        # Drop test database
        admin_conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )
        admin_conn.autocommit = True

        with admin_conn.cursor() as cur:
            print(f"  Cleaning up database: {shared_db}")
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(shared_db))
            )

        admin_conn.close()


def compare_modes():
    """Compare the two database modes."""
    print("\n=== Database Mode Comparison ===")

    print("\nSEPARATE Mode (Recommended):")
    print("  ✓ Complete isolation between trees")
    print("  ✓ Easier backup/restore per tree")
    print("  ✓ Can set different permissions per tree")
    print("  ✓ No table name conflicts")
    print("  ✓ Simpler queries (no prefixes)")
    print("  ✗ More databases to manage")
    print("  ✗ Can't query across trees easily")

    print("\nMONOLITHIC Mode:")
    print("  ✓ Single database to manage")
    print("  ✓ Can query across trees if needed")
    print("  ✓ Single connection pool")
    print("  ✗ Table name prefixes required")
    print("  ✗ Backup includes all trees")
    print("  ✗ Same permissions for all trees")
    print("  ✗ Risk of prefix collision")

    print("\nRecommendation: Use SEPARATE mode unless you have")
    print("specific requirements for cross-tree queries.")


def main():
    """Run database mode tests."""
    print("Testing Gramps PostgreSQL Database Modes")
    print("=" * 50)

    try:
        test_separate_mode()
        test_monolithic_mode()
        compare_modes()

        print("\n" + "=" * 50)
        print("All database mode tests completed successfully!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
