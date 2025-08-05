#!/usr/bin/env python3
"""
Test the debug_utils module functionality.
"""

import os
import sys
import time
import json
import logging

# Set debug environment variable
os.environ["GRAMPS_POSTGRESQL_DEBUG"] = "1"
os.environ["GRAMPS_POSTGRESQL_SLOW_QUERY"] = "0.05"  # 50ms threshold for testing

from debug_utils import (
    QueryProfiler,
    TransactionTracker,
    ConnectionMonitor,
    DebugContext,
    format_sql_query,
    timed_method,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_debug")


def test_query_profiler():
    """Test QueryProfiler functionality."""
    print("\n=== Testing QueryProfiler ===")
    profiler = QueryProfiler()

    # Simulate various queries
    queries = [
        ("SELECT * FROM person WHERE handle = %s", ["I0001"], 0.010, 1),
        ("SELECT * FROM person WHERE surname = %s", ["Smith"], 0.045, 25),
        (
            "INSERT INTO person (handle, json_data) VALUES (%s, %s)",
            ["I0002", "{}"],
            0.020,
            1,
        ),
        (
            "UPDATE person SET json_data = %s WHERE handle = %s",
            ["{}", "I0001"],
            0.015,
            1,
        ),
        (
            "SELECT * FROM family WHERE handle IN %s",
            [["F0001", "F0002"]],
            0.060,
            2,
        ),  # Slow query
        ("DELETE FROM person WHERE handle = %s", ["I0003"], 0.025, 1),
        ("BEGIN", [], 0.001, None),
        ("COMMIT", [], 0.005, None),
    ]

    for sql, params, duration, rows in queries:
        profiler.record_query(sql, params, duration, rows)
        time.sleep(0.01)  # Small delay to separate timestamps

    # Get statistics
    stats = profiler.get_statistics()
    print(f"\nTotal queries: {stats['total_queries']}")
    print(f"Query breakdown:")
    for op, data in stats["by_operation"].items():
        print(f"  {op}: {data['count']} queries, avg {data['avg_time']:.3f}s")

    print(f"\nSlowest queries:")
    for i, query in enumerate(stats["slowest_queries"][:3]):
        print(f"  {i+1}. {query['duration']:.3f}s - {query['sql'][:50]}...")

    return profiler


def test_transaction_tracker():
    """Test TransactionTracker functionality."""
    print("\n=== Testing TransactionTracker ===")
    tracker = TransactionTracker()

    # Simulate a successful transaction
    txn1_id = "txn_001"
    tracker.begin_transaction(txn1_id, "Add new person")
    tracker.add_operation(txn1_id, "INSERT", "person", "I0001")
    tracker.add_operation(txn1_id, "INSERT", "event", "E0001")
    sp1 = tracker.create_savepoint(txn1_id)
    print(f"Created savepoint: {sp1}")
    tracker.add_operation(txn1_id, "UPDATE", "family", "F0001")
    time.sleep(0.05)  # Simulate work
    txn1 = tracker.commit_transaction(txn1_id)
    print(
        f"Transaction {txn1_id} committed in {txn1['duration']:.3f}s with {len(txn1['operations'])} operations"
    )

    # Simulate a rolled back transaction
    txn2_id = "txn_002"
    tracker.begin_transaction(txn2_id, "Failed update")
    tracker.add_operation(txn2_id, "UPDATE", "person", "I0002")
    time.sleep(0.02)
    txn2 = tracker.rollback_transaction(txn2_id)
    print(f"Transaction {txn2_id} rolled back after {txn2['duration']:.3f}s")

    print(f"\nTransaction history: {len(tracker.transaction_history)} transactions")
    return tracker


def test_connection_monitor():
    """Test ConnectionMonitor functionality."""
    print("\n=== Testing ConnectionMonitor ===")
    monitor = ConnectionMonitor()

    # Simulate connection events
    events = [
        ("connect", {"host": "localhost", "database": "gramps_test"}),
        ("pool_created", {"min_size": 2, "max_size": 10}),
        ("query_start", {"query_id": "q001"}),
        ("query_complete", {"query_id": "q001", "duration": 0.025}),
        ("connection_error", {"error": "timeout", "retry": 1}),
        ("reconnect", {"attempt": 1, "success": True}),
    ]

    for event_type, details in events:
        monitor.record_connection_event(event_type, details)
        time.sleep(0.01)

    # Update pool stats
    monitor.update_pool_stats(
        {"current_size": 5, "available": 3, "waiting": 0, "usage_percent": 40.0}
    )

    health = monitor.get_connection_health()
    print(f"Connection health:")
    print(f"  Recent errors: {health['recent_errors']}")
    print(f"  Total events: {health['total_events']}")
    print(f"  Pool usage: {health['pool_stats'].get('usage_percent', 0):.1f}%")

    return monitor


def test_debug_context():
    """Test DebugContext comprehensive tracking."""
    print("\n=== Testing DebugContext ===")
    debug_ctx = DebugContext(logger)

    # Simulate a complex operation
    with debug_ctx.operation("import_gedcom", file="test.ged", records=1000) as op_id:
        print(f"Operation ID: {op_id}")

        # Log some queries
        debug_ctx.log_query(
            "SELECT COUNT(*) FROM person", duration=0.005, rows_affected=1
        )
        debug_ctx.log_query(
            "INSERT INTO person VALUES %s",
            params=["data"],
            duration=0.025,
            rows_affected=1,
        )

        # Nested operation
        with debug_ctx.operation("process_families", count=50):
            debug_ctx.log_query(
                "SELECT * FROM family WHERE handle = %s",
                params=["F0001"],
                duration=0.065,
                rows_affected=1,
            )  # Slow query
            time.sleep(0.1)

    # Generate debug report
    report = debug_ctx.get_debug_report()
    print(f"\nDebug report generated:")
    print(f"  Current operation: {report['current_operation']}")
    print(f"  Query count: {report['query_statistics']['total_queries']}")
    print(f"  Active transactions: {len(report['active_transactions'])}")

    # Save report to file
    report_path = debug_ctx.dump_debug_report("/tmp/gramps_debug_test.json")
    print(f"  Report saved to: {report_path}")

    return debug_ctx


def test_sql_formatter():
    """Test SQL query formatting."""
    print("\n=== Testing SQL Formatter ===")

    test_cases = [
        ("SELECT * FROM person WHERE handle = %s", ["I0001"]),
        (
            "INSERT INTO family (handle, json_data) VALUES (%s, %s)",
            ["F0001", '{"father": "I0001"}'],
        ),
        (
            "UPDATE person SET surname = %s, given_name = %s WHERE handle = %s",
            ["Smith", "John", "I0001"],
        ),
        ("SELECT " + "x" * 300, None),  # Long query
    ]

    for sql, params in test_cases:
        formatted = format_sql_query(sql, params)
        print(f"  {formatted}")


def test_timed_method_decorator():
    """Test the timed_method decorator."""
    print("\n=== Testing timed_method decorator ===")

    class TestClass:
        def __init__(self):
            self._debug_context = DebugContext(logger)

        @timed_method
        def slow_operation(self):
            """Simulate a slow operation."""
            time.sleep(0.1)
            return "completed"

        @timed_method
        def fast_operation(self):
            """Simulate a fast operation."""
            return "done"

    obj = TestClass()
    result1 = obj.slow_operation()
    result2 = obj.fast_operation()
    print(f"  Results: {result1}, {result2}")


def main():
    """Run all debug module tests."""
    print("Testing Gramps PostgreSQL Enhanced Debug Module")
    print("=" * 50)

    # Run tests
    profiler = test_query_profiler()
    tracker = test_transaction_tracker()
    monitor = test_connection_monitor()
    debug_ctx = test_debug_context()
    test_sql_formatter()
    test_timed_method_decorator()

    print("\n" + "=" * 50)
    print("All debug module tests completed!")

    # Check if debug report was created
    if os.path.exists("/tmp/gramps_debug_test.json"):
        print("\nDebug report contents:")
        with open("/tmp/gramps_debug_test.json", "r") as f:
            report = json.load(f)
            print(f"  Timestamp: {report['timestamp']}")
            print(f"  Total queries: {report['query_statistics']['total_queries']}")
            if report["query_statistics"]["slowest_queries"]:
                slowest = report["query_statistics"]["slowest_queries"][0]
                print(f"  Slowest query: {slowest['duration']:.3f}s")


if __name__ == "__main__":
    main()
