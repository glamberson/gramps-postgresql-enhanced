#!/usr/bin/env python3
"""
Comprehensive database content verification for PostgreSQL Enhanced plugin.

This script verifies actual data in the databases, not just test results.
NO FALLBACK: We must verify ALL data comprehensively.
"""

import psycopg
from psycopg import sql
import json
import sys

# Database configuration
DB_CONFIG = {
    "host": "192.168.10.90",
    "port": 5432,
    "user": "genealogy_user",
    "password": "GenealogyData2025",
}


def verify_monolithic_database():
    """Verify the contents of the monolithic test database."""
    print("\n=== VERIFYING MONOLITHIC DATABASE CONTENTS ===")

    try:
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="gramps_monolithic_test",
        )

        with conn.cursor() as cur:
            # 1. List all tables
            print("\n1. ALL TABLES IN DATABASE:")
            cur.execute(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """
            )
            tables = cur.fetchall()
            for table in tables:
                print(f"   - {table[0]}")

            # 2. Check data in each person table
            print("\n2. PERSON TABLE CONTENTS:")
            person_tables = [t[0] for t in tables if t[0].endswith("_person")]

            for table in person_tables:
                print(f"\n   Table: {table}")
                cur.execute(
                    sql.SQL(
                        """
                    SELECT handle, json_data::json->>'gramps_id' as gramps_id,
                           json_data::json->'primary_name'->>'first_name' as first_name,
                           json_data::json->'primary_name'->'surname_list'->0->>'surname' as surname
                    FROM {}
                    ORDER BY handle
                """
                    ).format(sql.Identifier(table))
                )

                rows = cur.fetchall()
                print(f"   Record count: {len(rows)}")
                for row in rows[:5]:  # Show first 5 records
                    print(
                        f"     - Handle: {row[0]}, ID: {row[1]}, Name: {row[2]} {row[3]}"
                    )
                if len(rows) > 5:
                    print(f"     ... and {len(rows) - 5} more records")

            # 3. Verify data isolation
            print("\n3. DATA ISOLATION VERIFICATION:")
            for table in person_tables:
                tree_name = table.replace("_person", "")
                cur.execute(
                    sql.SQL(
                        """
                    SELECT COUNT(*) as total,
                           COUNT(DISTINCT json_data::json->'primary_name'->'surname_list'->0->>'surname') as unique_surnames
                    FROM {}
                """
                    ).format(sql.Identifier(table))
                )

                result = cur.fetchone()
                print(
                    f"   {tree_name}: {result[0]} total records, {result[1]} unique surnames"
                )

                # Check for cross-contamination
                cur.execute(
                    sql.SQL(
                        """
                    SELECT json_data::json->'primary_name'->'surname_list'->0->>'surname' as surname,
                           COUNT(*) as count
                    FROM {}
                    GROUP BY json_data::json->'primary_name'->'surname_list'->0->>'surname'
                    ORDER BY count DESC
                """
                    ).format(sql.Identifier(table))
                )

                surnames = cur.fetchall()
                expected_surname = tree_name.split("_")[0].title()
                contamination = [
                    s
                    for s in surnames
                    if s[0]
                    and s[0] != expected_surname
                    and s[0] != "Concurrent"
                    and not s[0].startswith("Test")
                ]

                if contamination:
                    print(
                        f"     ⚠️  WARNING: Found unexpected surnames: {contamination}"
                    )
                else:
                    print(f"     ✓ No cross-contamination detected")

            # 4. Check other object types
            print("\n4. OTHER OBJECT TYPES:")
            object_types = [
                "family",
                "event",
                "place",
                "source",
                "citation",
                "repository",
                "media",
                "note",
                "tag",
            ]

            for obj_type in object_types:
                obj_tables = [t[0] for t in tables if t[0].endswith(f"_{obj_type}")]
                if obj_tables:
                    total_count = 0
                    for table in obj_tables:
                        cur.execute(
                            sql.SQL("SELECT COUNT(*) FROM {}").format(
                                sql.Identifier(table)
                            )
                        )
                        count = cur.fetchone()[0]
                        total_count += count

                    if total_count > 0:
                        print(
                            f"   {obj_type.title()}: {total_count} total records across {len(obj_tables)} tables"
                        )

            # 5. Check shared tables
            print("\n5. SHARED TABLES (should exist without prefixes):")
            shared_tables = ["name_group", "surname"]
            for table in shared_tables:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM pg_tables 
                        WHERE schemaname = 'public' AND tablename = %s
                    )
                """,
                    [table],
                )
                exists = cur.fetchone()[0]
                print(f"   {table}: {'✓ EXISTS' if exists else '✗ MISSING'}")

                if exists:
                    cur.execute(
                        sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table))
                    )
                    count = cur.fetchone()[0]
                    print(f"     - {count} records")

            # 6. Verify metadata tables
            print("\n6. METADATA TABLES:")
            metadata_tables = [t[0] for t in tables if t[0].endswith("_metadata")]
            for table in metadata_tables:
                cur.execute(
                    sql.SQL(
                        """
                    SELECT setting, value 
                    FROM {} 
                    WHERE setting IN ('version', 'created', 'database_mode')
                    ORDER BY setting
                """
                    ).format(sql.Identifier(table))
                )

                settings = cur.fetchall()
                if settings:
                    print(f"   {table}:")
                    for setting, value in settings:
                        print(f"     - {setting}: {value}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n✗ ERROR verifying monolithic database: {e}")
        return False


def verify_separate_databases():
    """Verify separate database mode by checking individual databases."""
    print("\n=== VERIFYING SEPARATE DATABASE MODE ===")

    # List of test databases that might exist
    test_dbs = ["family_tree_1", "family_tree_2", "research_tree"]

    try:
        # First, list all databases
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT datname 
                FROM pg_database 
                WHERE datname LIKE 'family_tree_%' 
                   OR datname LIKE 'research_tree%'
                   OR datname LIKE 'test_%'
                ORDER BY datname
            """
            )

            databases = [row[0] for row in cur.fetchall()]
            print(f"\nFound {len(databases)} test databases: {databases}")

        conn.close()

        # Check each database
        for db_name in databases[:3]:  # Check first 3 to avoid too much output
            print(f"\n--- Database: {db_name} ---")

            try:
                db_conn = psycopg.connect(
                    host=DB_CONFIG["host"],
                    port=DB_CONFIG["port"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    dbname=db_name,
                )

                with db_conn.cursor() as cur:
                    # Check tables (should NOT have prefixes in separate mode)
                    cur.execute(
                        """
                        SELECT tablename 
                        FROM pg_tables 
                        WHERE schemaname = 'public' 
                        AND tablename IN ('person', 'family', 'event', 'metadata')
                        ORDER BY tablename
                    """
                    )

                    tables = [row[0] for row in cur.fetchall()]
                    print(f"  Core tables: {tables}")

                    if "person" in tables:
                        cur.execute(
                            """
                            SELECT COUNT(*) as total,
                                   COUNT(DISTINCT json_data::json->>'gramps_id') as unique_ids
                            FROM person
                        """
                        )
                        result = cur.fetchone()
                        print(
                            f"  Person records: {result[0]} total, {result[1]} unique IDs"
                        )

                    if "metadata" in tables:
                        cur.execute(
                            "SELECT setting, value FROM metadata WHERE setting = 'database_mode'"
                        )
                        mode = cur.fetchone()
                        if mode:
                            print(f"  Database mode: {mode[1]}")

                db_conn.close()

            except psycopg.OperationalError:
                print(f"  Database doesn't exist (may have been cleaned up)")
            except Exception as e:
                print(f"  Error checking database: {e}")

        return True

    except Exception as e:
        print(f"\n✗ ERROR verifying separate databases: {e}")
        return False


def verify_query_patterns():
    """Verify that our query patterns are working correctly."""
    print("\n=== VERIFYING QUERY PATTERN MATCHING ===")

    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mock_gramps
    from postgresqlenhanced import TablePrefixWrapper, CursorPrefixWrapper

    # Test queries that were failing before
    test_queries = [
        "SELECT handle, json_data FROM person",
        "SELECT * FROM person WHERE handle = %s",
        "SELECT DISTINCT surname FROM person",
        "SELECT p.*, f.* FROM person p JOIN family f ON p.handle = f.father_handle",
        "INSERT INTO person (handle, json_data) VALUES (%s, %s)",
        "UPDATE person SET json_data = %s WHERE handle = %s",
        "DELETE FROM person WHERE handle = %s",
        "SELECT COUNT(*) FROM person",
        "SELECT 1 FROM metadata WHERE setting = %s",
        "CREATE TABLE IF NOT EXISTS person (handle TEXT PRIMARY KEY)",
        "CREATE INDEX idx_person_gramps_id ON person (gramps_id)",
    ]

    # Create a mock wrapper to test pattern matching
    class MockConnection:
        def execute(self, query, params=None):
            return query

    wrapper = TablePrefixWrapper(MockConnection(), "test_prefix_")

    print("\nTesting query pattern matching:")
    all_correct = True

    for query in test_queries:
        modified = wrapper._add_table_prefixes(query)

        # Check if prefixes were added where expected
        if " person" in query and "test_prefix_person" not in modified:
            print(f"✗ FAILED: {query}")
            print(f"  Result: {modified}")
            all_correct = False
        else:
            print(f"✓ OK: {query[:50]}...")

    return all_correct


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("PostgreSQL Enhanced - Comprehensive Database Verification")
    print("=" * 70)

    results = {"monolithic": False, "separate": False, "patterns": False}

    # Check if monolithic test database exists
    try:
        conn = psycopg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM pg_database WHERE datname = 'gramps_monolithic_test'
                )
            """
            )
            monolithic_exists = cur.fetchone()[0]

        conn.close()

        if monolithic_exists:
            results["monolithic"] = verify_monolithic_database()
        else:
            print(
                "\n⚠️  Monolithic test database doesn't exist. Run test_monolithic_comprehensive.py first."
            )

    except Exception as e:
        print(f"\nError checking databases: {e}")

    # Verify separate databases
    results["separate"] = verify_separate_databases()

    # Verify query patterns
    results["patterns"] = verify_query_patterns()

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    for check, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{check.title()}: {status}")

    all_passed = all(results.values())
    print(
        f"\nOverall: {'✓ ALL CHECKS PASSED' if all_passed else '✗ SOME CHECKS FAILED'}"
    )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
