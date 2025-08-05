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
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Unit tests for PostgreSQL Enhanced connection handling.
"""

# -------------------------------------------------------------------------
#
# Standard python modules
#
# -------------------------------------------------------------------------
import unittest
from unittest.mock import Mock, patch, MagicMock
import os

# -------------------------------------------------------------------------
#
# PostgreSQL Enhanced modules
#
# -------------------------------------------------------------------------
from ..connection import PostgreSQLConnection


# -------------------------------------------------------------------------
#
# TestPostgreSQLConnection
#
# -------------------------------------------------------------------------
class TestPostgreSQLConnection(unittest.TestCase):
    """Test PostgreSQL connection handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_psycopg = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        
    @patch('psycopg.connect')
    def test_parse_url_connection_string(self, mock_connect):
        """Test parsing PostgreSQL URL format."""
        mock_connect.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__ = Mock(
            return_value=self.mock_cursor)
        self.mock_connection.cursor.return_value.__exit__ = Mock(
            return_value=None)
        
        # Test URL format
        conn = PostgreSQLConnection(
            "postgresql://testuser:testpass@localhost:5432/testdb",
            None, None)
        
        mock_connect.assert_called_once_with(
            "postgresql://testuser:testpass@localhost:5432/testdb")
        
    @patch('psycopg.connect')
    def test_parse_traditional_connection_string(self, mock_connect):
        """Test parsing traditional host:port:dbname format."""
        mock_connect.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__ = Mock(
            return_value=self.mock_cursor)
        self.mock_connection.cursor.return_value.__exit__ = Mock(
            return_value=None)
        
        # Test traditional format
        conn = PostgreSQLConnection(
            "localhost:5432:testdb:public",
            "testuser", "testpass")
        
        expected = "host=localhost port=5432 dbname=testdb user=testuser password=testpass"
        mock_connect.assert_called_once_with(expected)
        
    @patch('psycopg.connect')
    def test_parse_simple_dbname(self, mock_connect):
        """Test parsing simple database name."""
        mock_connect.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__ = Mock(
            return_value=self.mock_cursor)
        self.mock_connection.cursor.return_value.__exit__ = Mock(
            return_value=None)
        
        # Test simple dbname
        conn = PostgreSQLConnection("testdb", "testuser", None)
        
        expected = "dbname=testdb user=testuser"
        mock_connect.assert_called_once_with(expected)
        
    def test_query_translation_placeholders(self):
        """Test SQLite ? placeholder translation."""
        conn = PostgreSQLConnection.__new__(PostgreSQLConnection)
        
        # Test placeholder conversion
        sqlite_query = "SELECT * FROM person WHERE handle = ? AND gramps_id = ?"
        pg_query = conn._translate_query(sqlite_query)
        self.assertEqual(pg_query, 
                        "SELECT * FROM person WHERE handle = %s AND gramps_id = %s")
        
    def test_query_translation_regexp(self):
        """Test REGEXP operator translation."""
        conn = PostgreSQLConnection.__new__(PostgreSQLConnection)
        
        # Test REGEXP conversion
        sqlite_query = "SELECT * FROM person WHERE name REGEXP ?"
        pg_query = conn._translate_query(sqlite_query)
        self.assertEqual(pg_query, "SELECT * FROM person WHERE name ~ %s")
        
    def test_query_translation_limit(self):
        """Test LIMIT clause translation."""
        conn = PostgreSQLConnection.__new__(PostgreSQLConnection)
        
        # Test LIMIT offset, count conversion
        sqlite_query = "SELECT * FROM person LIMIT 10, 20"
        pg_query = conn._translate_query(sqlite_query)
        self.assertEqual(pg_query, "SELECT * FROM person LIMIT 20 OFFSET 10")
        
        # Test LIMIT -1 conversion
        sqlite_query = "SELECT * FROM person LIMIT -1"
        pg_query = conn._translate_query(sqlite_query)
        self.assertEqual(pg_query, "SELECT * FROM person LIMIT ALL")
        
    def test_query_translation_blob(self):
        """Test BLOB to BYTEA translation."""
        conn = PostgreSQLConnection.__new__(PostgreSQLConnection)
        
        sqlite_query = "CREATE TABLE test (data BLOB)"
        pg_query = conn._translate_query(sqlite_query)
        self.assertEqual(pg_query, "CREATE TABLE test (data BYTEA)")
        
    @patch.dict(os.environ, {'PGHOST': 'envhost', 'PGPORT': '5433'})
    def test_environment_variables(self):
        """Test PostgreSQL environment variable support."""
        conn = PostgreSQLConnection.__new__(PostgreSQLConnection)
        
        # This would need proper mocking of the full initialization
        # For now just test the method exists
        self.assertTrue(hasattr(conn, '_add_environment_variables'))


# -------------------------------------------------------------------------
#
# TestConnectionPooling
#
# -------------------------------------------------------------------------
class TestConnectionPooling(unittest.TestCase):
    """Test connection pooling functionality."""
    
    @patch('psycopg_pool.ConnectionPool')
    @patch('psycopg.connect')
    def test_pool_creation(self, mock_connect, mock_pool_class):
        """Test connection pool creation."""
        mock_connect.return_value = MagicMock()
        
        # Test pool creation with pool_size option
        # This would require full URL parsing implementation
        # For now just verify the connection class handles options
        conn = PostgreSQLConnection.__new__(PostgreSQLConnection)
        self.assertTrue(hasattr(conn, '_create_pool'))


if __name__ == '__main__':
    unittest.main()