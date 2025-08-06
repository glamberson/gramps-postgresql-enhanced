#!/usr/bin/env python3
"""
Test runner with comprehensive logging and debugging for PostgreSQL Enhanced
"""

import os
import sys
import logging

# Configure gramps logging BEFORE importing gramps modules
logging.getLogger("gramps.gen.utils.grampslocale").setLevel(logging.WARNING)

import argparse
from datetime import datetime


# Set up logging
def setup_logging(debug=False, log_file=None):
    """Configure comprehensive logging"""

    # Create logs directory
    log_dir = os.path.join(os.path.dirname(__file__), "test_logs")
    os.makedirs(log_dir, exist_ok=True)

    # Generate log filename with timestamp
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")

    # Configure root logger
    log_level = logging.DEBUG if debug else logging.INFO

    # File handler with detailed formatting
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(file_formatter)

    # Console handler with simpler formatting
    console_formatter = logging.Formatter("%(levelname)-8s %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers_config = {
        "gramps": logging.INFO,
        "gramps.gen.utils.grampslocale": logging.WARNING,  # Suppress DEBUG messages
        "postgresqlenhanced": logging.DEBUG,
        "psycopg": logging.INFO,
        "test": logging.DEBUG,
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    # Log startup info
    logging.info(f"=" * 80)
    logging.info(f"PostgreSQL Enhanced Test Suite")
    logging.info(f"Started: {datetime.now()}")
    logging.info(f"Log file: {log_file}")
    logging.info(f"Debug mode: {debug}")
    logging.info(f"Python: {sys.version}")
    logging.info(f"=" * 80)

    return log_file


def run_specific_test(test_name):
    """Run a specific test by name"""
    from test_postgresql_enhanced import PostgreSQLEnhancedTester

    tester = PostgreSQLEnhancedTester()

    # Map test names to methods
    test_methods = {
        "person_crud": tester.test_person_crud,
        "family_crud": tester.test_family_crud,
        "event_crud": tester.test_event_crud,
        "place_crud": tester.test_place_crud,
        "source_citation_crud": tester.test_source_citation_crud,
        "repository_crud": tester.test_repository_crud,
        "media_crud": tester.test_media_crud,
        "note_crud": tester.test_note_crud,
        "tag_crud": tester.test_tag_crud,
        "secondary_columns_person": tester.test_secondary_columns_person,
        "secondary_columns_all": tester.test_secondary_columns_all_types,
        "search": tester.test_search_operations,
        "filter": tester.test_filter_operations,
        "relationships": tester.test_family_relationships,
        "references": tester.test_person_references,
        "bulk": tester.test_bulk_operations,
        "concurrent": tester.test_concurrent_access,
        "edge_cases": tester.test_edge_cases,
        "error_handling": tester.test_error_handling,
    }

    if test_name not in test_methods:
        logging.error(f"Unknown test: {test_name}")
        logging.info(f"Available tests: {', '.join(test_methods.keys())}")
        return False

    try:
        logging.info(f"Running specific test: {test_name}")
        tester.setup()
        test_methods[test_name]()
        tester.teardown()
        return tester.results.failed == 0
    except Exception as e:
        logging.exception(f"Test {test_name} failed with exception")
        return False


def run_all_tests():
    """Run the complete test suite"""
    from test_postgresql_enhanced import PostgreSQLEnhancedTester

    tester = PostgreSQLEnhancedTester()
    tester.run_all_tests()
    return tester.results.failed == 0


def run_sql_verification():
    """Run direct SQL verification tests"""
    import psycopg

    logging.info("Running SQL verification tests...")

    try:
        # Test connection
        conn = psycopg.connect(
            "postgresql://genealogy_user:GenealogyData2025@192.168.10.90:5432/postgres"
        )

        with conn.cursor() as cur:
            # List recent test databases
            cur.execute(
                """
                SELECT datname, pg_database_size(datname) as size
                FROM pg_database 
                WHERE datname LIKE 'test_gramps_%' OR datname LIKE '6890%'
                ORDER BY datname DESC
                LIMIT 10
            """
            )

            logging.info("Recent databases:")
            for row in cur.fetchall():
                logging.info(f"  {row[0]}: {row[1]:,} bytes")

        conn.close()
        return True

    except Exception as e:
        logging.exception("SQL verification failed")
        return False


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run PostgreSQL Enhanced tests")
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    parser.add_argument("--log-file", "-l", type=str, help="Log file path")
    parser.add_argument("--test", "-t", type=str, help="Run specific test")
    parser.add_argument(
        "--sql-verify", action="store_true", help="Run SQL verification only"
    )
    parser.add_argument(
        "--keep-db", action="store_true", help="Keep test database after tests"
    )

    args = parser.parse_args()

    # Set up logging
    log_file = setup_logging(debug=args.debug, log_file=args.log_file)

    # Set environment for tests
    if args.keep_db:
        os.environ["KEEP_TEST_DB"] = "1"

    try:
        if args.sql_verify:
            success = run_sql_verification()
        elif args.test:
            success = run_specific_test(args.test)
        else:
            success = run_all_tests()

        if success:
            logging.info("✅ All tests passed!")
        else:
            logging.error("❌ Some tests failed!")

        logging.info(f"Full test log: {log_file}")

        return 0 if success else 1

    except KeyboardInterrupt:
        logging.warning("Tests interrupted by user")
        return 2
    except Exception as e:
        logging.exception("Unexpected error during tests")
        return 3


if __name__ == "__main__":
    sys.exit(main())
