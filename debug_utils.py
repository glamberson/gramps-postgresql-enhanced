#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025       Greg Lamberson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

"""
Enhanced debugging utilities for PostgreSQL Enhanced addon.

Provides comprehensive logging, profiling, and diagnostic capabilities
for database operations.
"""

import os
import time
import json
import logging
import functools
import traceback
from datetime import datetime
from collections import defaultdict, deque
from contextlib import contextmanager


# Performance tracking
class QueryProfiler:
    """
    Track and analyze SQL query performance.

    Maintains detailed statistics about all SQL queries executed,
    including timing, categorization, and slow query detection.
    """

    def __init__(self):
        """
        Initialize the query profiler.

        Sets up query tracking with configurable slow query threshold
        from GRAMPS_POSTGRESQL_SLOW_QUERY environment variable.
        """
        self.queries = defaultdict(list)
        self.slow_query_threshold = float(
            os.environ.get("GRAMPS_POSTGRESQL_SLOW_QUERY", "0.1")
        )
        self.query_history = deque(maxlen=1000)
        self.start_time = time.time()

    def record_query(self, sql, params, duration, rows_affected=None):
        """
        Record a query execution.

        :param sql: SQL query string
        :type sql: str
        :param params: Query parameters
        :type params: tuple or list or None
        :param duration: Query execution time in seconds
        :type duration: float
        :param rows_affected: Number of rows affected (optional)
        :type rows_affected: int or None
        :returns: Query information dictionary
        :rtype: dict
        """
        query_info = {
            "sql": sql,
            "params": params,
            "duration": duration,
            "rows_affected": rows_affected,
            "timestamp": datetime.now().isoformat(),
            "stack": traceback.extract_stack()[-4:-2],  # Calling context
        }

        # Categorize query
        operation = self._categorize_query(sql)
        self.queries[operation].append(query_info)
        self.query_history.append(query_info)

        # Check for slow queries
        if duration > self.slow_query_threshold:
            LOG.warning("Slow query (%.3fs): %s...", duration, sql[:100])

        return query_info

    def _categorize_query(self, sql):
        """
        Categorize SQL query by operation type.

        :param sql: SQL query string
        :type sql: str
        :returns: Operation category (SELECT, INSERT, UPDATE, etc.)
        :rtype: str
        """
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT"):
            return "SELECT"
        if sql_upper.startswith("INSERT"):
            return "INSERT"
        if sql_upper.startswith("UPDATE"):
            return "UPDATE"
        if sql_upper.startswith("DELETE"):
            return "DELETE"
        if sql_upper.startswith("CREATE"):
            return "CREATE"
        if "BEGIN" in sql_upper or "COMMIT" in sql_upper or "ROLLBACK" in sql_upper:
            return "TRANSACTION"
        return "OTHER"

    def get_statistics(self):
        """
        Get query performance statistics.

        :returns: Dictionary with comprehensive query statistics
        :rtype: dict
        """
        stats = {
            "total_queries": sum(len(queries) for queries in self.queries.values()),
            "uptime_seconds": time.time() - self.start_time,
            "by_operation": {},
        }

        for operation, queries in self.queries.items():
            if queries:
                durations = [q["duration"] for q in queries]
                stats["by_operation"][operation] = {
                    "count": len(queries),
                    "total_time": sum(durations),
                    "avg_time": sum(durations) / len(durations),
                    "min_time": min(durations),
                    "max_time": max(durations),
                }

        # Find slowest queries
        all_queries = []
        for queries in self.queries.values():
            all_queries.extend(queries)

        stats["slowest_queries"] = sorted(
            all_queries, key=lambda q: q["duration"], reverse=True
        )[:10]

        return stats

    def reset(self):
        """
        Reset profiler statistics.

        Clears all query history and resets the start time.
        """
        self.queries.clear()
        self.query_history.clear()
        self.start_time = time.time()


class TransactionTracker:
    """
    Track transaction lifecycle and nesting.

    Monitors transaction operations, timing, and savepoint usage
    for debugging and performance analysis.
    """

    def __init__(self):
        """
        Initialize transaction tracker.
        """
        self.active_transactions = {}
        self.transaction_history = deque(maxlen=100)
        self.savepoint_counter = 0

    def begin_transaction(self, txn_id, name=None):
        """
        Record transaction start.

        :param txn_id: Unique transaction identifier
        :type txn_id: str
        :param name: Optional transaction name
        :type name: str or None
        """
        self.active_transactions[txn_id] = {
            "id": txn_id,
            "name": name,
            "start_time": time.time(),
            "savepoints": [],
            "operations": [],
        }
        LOG.debug("Transaction started: %s (%s)", txn_id, name)

    def add_operation(self, txn_id, operation, obj_type, handle):
        """
        Add operation to transaction.

        :param txn_id: Transaction identifier
        :type txn_id: str
        :param operation: Operation type (add, commit, remove)
        :type operation: str
        :param obj_type: Type of object
        :type obj_type: str
        :param handle: Object handle
        :type handle: str
        """
        if txn_id in self.active_transactions:
            self.active_transactions[txn_id]["operations"].append(
                {
                    "operation": operation,
                    "obj_type": obj_type,
                    "handle": handle,
                    "time": time.time(),
                }
            )

    def commit_transaction(self, txn_id):
        """
        Record transaction commit.

        :param txn_id: Transaction identifier
        :type txn_id: str
        :returns: Transaction info dictionary
        :rtype: dict or None
        """
        if txn_id in self.active_transactions:
            txn = self.active_transactions.pop(txn_id)
            txn["end_time"] = time.time()
            txn["duration"] = txn["end_time"] - txn["start_time"]
            txn["status"] = "committed"
            self.transaction_history.append(txn)
            LOG.debug("Transaction committed: %s (%.3fs)", txn_id, txn["duration"])
            return txn
        return None

    def rollback_transaction(self, txn_id):
        """
        Record transaction rollback.

        :param txn_id: Transaction identifier
        :type txn_id: str
        :returns: Transaction info dictionary
        :rtype: dict or None
        """
        if txn_id in self.active_transactions:
            txn = self.active_transactions.pop(txn_id)
            txn["end_time"] = time.time()
            txn["duration"] = txn["end_time"] - txn["start_time"]
            txn["status"] = "rolled_back"
            self.transaction_history.append(txn)
            LOG.warning("Transaction rolled back: %s", txn_id)
            return txn
        return None

    def create_savepoint(self, txn_id):
        """
        Create a savepoint within transaction.

        :param txn_id: Transaction identifier
        :type txn_id: str
        :returns: Savepoint name
        :rtype: str
        """
        self.savepoint_counter += 1
        sp_name = "sp_%d" % self.savepoint_counter
        if txn_id in self.active_transactions:
            self.active_transactions[txn_id]["savepoints"].append(
                {"name": sp_name, "created": time.time()}
            )
        return sp_name


class ConnectionMonitor:
    """
    Monitor database connections and pool status.

    Tracks connection events, errors, and pool health metrics
    for operational monitoring.
    """

    def __init__(self):
        """
        Initialize connection monitor.
        """
        self.connection_events = deque(maxlen=500)
        self.pool_stats = {}

    def record_connection_event(self, event_type, details=None):
        """
        Record a connection event.

        :param event_type: Type of event (connect, disconnect, error)
        :type event_type: str
        :param details: Additional event details
        :type details: dict or None
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self.connection_events.append(event)
        LOG.debug("Connection event: %s", event_type)

    def update_pool_stats(self, pool_info):
        """
        Update connection pool statistics.

        :param pool_info: Pool statistics dictionary
        :type pool_info: dict
        """
        self.pool_stats = {"updated": datetime.now().isoformat(), **pool_info}

    def get_connection_health(self):
        """
        Get connection health metrics.

        :returns: Health metrics including errors and pool stats
        :rtype: dict
        """
        recent_events = list(self.connection_events)[-50:]
        error_count = sum(1 for e in recent_events if "error" in e["type"].lower())

        return {
            "recent_errors": error_count,
            "total_events": len(self.connection_events),
            "pool_stats": self.pool_stats,
            "last_event": (
                self.connection_events[-1] if self.connection_events else None
            ),
        }


class DebugContext:
    """Enhanced debug context manager for detailed operation tracking."""

    def __init__(self, logger):
        self.logger = logger
        self.query_profiler = QueryProfiler()
        self.transaction_tracker = TransactionTracker()
        self.connection_monitor = ConnectionMonitor()
        self.operation_stack = []

    @contextmanager
    def operation(self, name, **kwargs):
        """Context manager for tracking operations."""
        op_id = f"{name}_{time.time()}"
        start_time = time.time()

        self.operation_stack.append(
            {"id": op_id, "name": name, "start_time": start_time, "context": kwargs}
        )

        self.logger.debug(f"Operation started: {name}", extra=kwargs)

        try:
            yield op_id
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Operation failed: {name} ({duration:.3f}s)",
                exc_info=True,
                extra={"operation_id": op_id, "duration": duration},
            )
            raise
        else:
            duration = time.time() - start_time
            self.logger.debug(
                f"Operation completed: {name} ({duration:.3f}s)",
                extra={"operation_id": op_id, "duration": duration},
            )
        finally:
            self.operation_stack.pop()

    def log_query(self, sql, params=None, duration=None, rows_affected=None):
        """Log SQL query with profiling."""
        if duration is None:
            # If duration not provided, this is a pre-execution log
            self.logger.debug(f"SQL: {sql}", extra={"params": params})
        else:
            # Post-execution log with metrics
            query_info = self.query_profiler.record_query(
                sql, params, duration, rows_affected
            )
            self.logger.debug(
                f"SQL executed ({duration:.3f}s): {sql[:100]}...",
                extra={
                    "duration": duration,
                    "rows_affected": rows_affected,
                    "params": params,
                },
            )

    def get_debug_report(self):
        """Generate comprehensive debug report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "query_statistics": self.query_profiler.get_statistics(),
            "transaction_history": list(self.transaction_tracker.transaction_history),
            "active_transactions": dict(self.transaction_tracker.active_transactions),
            "connection_health": self.connection_monitor.get_connection_health(),
            "current_operation": (
                self.operation_stack[-1] if self.operation_stack else None
            ),
        }

    def dump_debug_report(self, filepath=None):
        """Dump debug report to file."""
        if filepath is None:
            filepath = os.path.expanduser("~/.gramps/postgresql_debug_report.json")

        report = self.get_debug_report()
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Debug report written to: {filepath}")
        return filepath


# Create global logger
LOG = logging.getLogger(".PostgreSQLEnhanced.Debug")


# Decorator for method timing
def timed_method(method):
    """Decorator to time method execution."""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, "_debug_context") and self._debug_context:
            with self._debug_context.operation(
                f"{self.__class__.__name__}.{method.__name__}"
            ):
                return method(self, *args, **kwargs)
        else:
            return method(self, *args, **kwargs)

    return wrapper


# SQL query formatter for logging
def format_sql_query(sql, params=None, max_length=200):
    """Format SQL query for logging with parameter substitution."""
    if params:
        try:
            # Attempt to show query with parameters inline
            formatted = sql
            if isinstance(params, (list, tuple)):
                for i, param in enumerate(params):
                    # Simple parameter substitution for logging
                    if isinstance(param, str):
                        formatted = formatted.replace("%s", f"'{param}'", 1)
                    else:
                        formatted = formatted.replace("%s", str(param), 1)

            if len(formatted) > max_length:
                formatted = formatted[:max_length] + "..."
            return formatted
        except:
            # Fallback to showing query and params separately
            pass

    if len(sql) > max_length:
        sql = sql[:max_length] + "..."

    if params:
        return f"{sql} [params: {params}]"
    return sql


# Connection pool monitor
class PoolMonitor:
    """Monitor psycopg connection pool statistics."""

    def __init__(self, pool):
        self.pool = pool
        self.sample_interval = 60  # seconds
        self.last_sample = None

    def get_stats(self):
        """Get current pool statistics."""
        try:
            stats = {
                "name": getattr(self.pool, "name", "default"),
                "min_size": getattr(self.pool, "min_size", None),
                "max_size": getattr(self.pool, "max_size", None),
                "current_size": getattr(self.pool, "_nconns", None),
                "available": getattr(self.pool, "_navailable", None),
                "waiting": getattr(self.pool, "_nwaiting", None),
            }

            # Calculate usage percentage
            if stats["current_size"] and stats["available"] is not None:
                stats["usage_percent"] = (
                    (stats["current_size"] - stats["available"])
                    / stats["current_size"]
                    * 100
                )

            return stats
        except Exception as e:
            LOG.warning(f"Failed to get pool stats: {e}")
            return {}

    def should_sample(self):
        """Check if we should take a new sample."""
        now = time.time()
        if self.last_sample is None or (now - self.last_sample) > self.sample_interval:
            self.last_sample = now
            return True
        return False
