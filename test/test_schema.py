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
Unit tests for PostgreSQL Enhanced schema management.
"""

# -------------------------------------------------------------------------
#
# Standard python modules
#
# -------------------------------------------------------------------------
import unittest
from unittest.mock import Mock, patch, MagicMock, call

# -------------------------------------------------------------------------
#
# PostgreSQL Enhanced modules
#
# -------------------------------------------------------------------------
from ..schema import PostgreSQLSchema, SCHEMA_VERSION, OBJECT_TYPES


class TestPostgreSQLSchema(unittest.TestCase):
    """Test PostgreSQL schema management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = MagicMock()
        self.schema = PostgreSQLSchema(self.mock_connection, use_jsonb=True)
        
    def test_init_with_jsonb_enabled(self):
        """Test schema initialization with JSONB enabled."""
        schema = PostgreSQLSchema(self.mock_connection, use_jsonb=True)
        self.assertTrue(schema.use_jsonb)
        
    def test_init_with_jsonb_disabled(self):
        """Test schema initialization with JSONB disabled."""
        schema = PostgreSQLSchema(self.mock_connection, use_jsonb=False)
        self.assertFalse(schema.use_jsonb)
        
    def test_check_and_init_schema_new_database(self):
        """Test schema creation for new database."""
        # Mock table doesn't exist
        self.mock_connection.table_exists.return_value = False
        
        # Mock _create_schema method
        self.schema._create_schema = Mock()
        
        # Run check
        self.schema.check_and_init_schema()
        
        # Verify metadata table check
        self.mock_connection.table_exists.assert_called_once_with('metadata')
        
        # Verify schema creation called
        self.schema._create_schema.assert_called_once()
        
    def test_check_and_init_schema_existing_database(self):
        """Test schema check for existing database."""
        # Mock table exists
        self.mock_connection.table_exists.return_value = True
        
        # Mock version check
        self.schema._get_schema_version = Mock(return_value=SCHEMA_VERSION)
        
        # Run check
        self.schema.check_and_init_schema()
        
        # Verify version check called
        self.schema._get_schema_version.assert_called_once()
        
    def test_create_schema_with_jsonb(self):
        """Test full schema creation with JSONB enabled."""
        self.schema.use_jsonb = True
        self.mock_connection.fetchone.return_value = [0]  # Extension not found
        
        # Run schema creation
        self.schema._create_schema()
        
        # Check metadata table created with JSONB
        metadata_call = [c for c in self.mock_connection.execute.call_args_list
                        if 'CREATE TABLE IF NOT EXISTS metadata' in str(c)][0]
        self.assertIn('json_value JSONB', str(metadata_call))
        
        # Check object tables created
        for obj_type in OBJECT_TYPES:
            table_calls = [c for c in self.mock_connection.execute.call_args_list
                          if f'CREATE TABLE IF NOT EXISTS {obj_type}' in str(c)]
            self.assertEqual(len(table_calls), 1)
            
            # Check JSONB column exists
            self.assertIn('json_data JSONB', str(table_calls[0]))
            self.assertIn('gramps_id VARCHAR(50) GENERATED', str(table_calls[0]))
            
        # Check commit called
        self.mock_connection.commit.assert_called_once()
        
    def test_create_schema_without_jsonb(self):
        """Test schema creation with JSONB disabled."""
        self.schema.use_jsonb = False
        
        # Run schema creation
        self.schema._create_schema()
        
        # Check metadata table created without JSONB
        metadata_call = [c for c in self.mock_connection.execute.call_args_list
                        if 'CREATE TABLE IF NOT EXISTS metadata' in str(c)][0]
        self.assertNotIn('json_value', str(metadata_call))
        
        # Check object tables created without JSONB
        for obj_type in OBJECT_TYPES:
            table_calls = [c for c in self.mock_connection.execute.call_args_list
                          if f'CREATE TABLE IF NOT EXISTS {obj_type}' in str(c)]
            self.assertEqual(len(table_calls), 1)
            self.assertNotIn('json_data', str(table_calls[0]))
            
    def test_create_object_specific_indexes(self):
        """Test creation of object-specific indexes."""
        # Test person indexes
        self.schema._create_object_specific_indexes('person')
        
        # Check name index created
        name_index_calls = [c for c in self.mock_connection.execute.call_args_list
                           if 'idx_person_names' in str(c)]
        self.assertEqual(len(name_index_calls), 1)
        
        # Test event indexes
        self.mock_connection.reset_mock()
        self.schema._create_object_specific_indexes('event')
        
        # Check event type/date index created
        event_index_calls = [c for c in self.mock_connection.execute.call_args_list
                            if 'idx_event_type_date' in str(c)]
        self.assertEqual(len(event_index_calls), 1)
        
    def test_check_extension_available(self):
        """Test PostgreSQL extension availability check."""
        # Mock extension exists
        self.mock_connection.fetchone.return_value = [1]
        
        result = self.schema._check_extension_available('pg_trgm')
        
        self.assertTrue(result)
        self.mock_connection.execute.assert_called_with(
            'SELECT COUNT(*) FROM pg_available_extensions WHERE name = %s',
            ['pg_trgm']
        )
        
    def test_get_schema_version(self):
        """Test retrieving schema version."""
        import pickle
        
        # Mock version in database
        version_data = pickle.dumps(1)
        self.mock_connection.fetchone.return_value = [version_data]
        
        version = self.schema._get_schema_version()
        
        self.assertEqual(version, 1)
        
    def test_get_schema_version_not_found(self):
        """Test retrieving schema version when not set."""
        self.mock_connection.fetchone.return_value = None
        
        version = self.schema._get_schema_version()
        
        self.assertEqual(version, 0)
        
    def test_set_schema_version_with_jsonb(self):
        """Test setting schema version with JSONB enabled."""
        self.schema.use_jsonb = True
        
        self.schema._set_schema_version(2)
        
        # Check INSERT with JSONB
        insert_calls = [c for c in self.mock_connection.execute.call_args_list
                       if 'INSERT INTO metadata' in str(c)]
        self.assertEqual(len(insert_calls), 1)
        self.assertIn('json_value', str(insert_calls[0]))
        
    def test_enhanced_features_creation(self):
        """Test creation of enhanced PostgreSQL features."""
        # Mock extension available
        self.schema._check_extension_available = Mock(return_value=True)
        
        self.schema._create_enhanced_features()
        
        # Check custom functions created
        function_calls = [c for c in self.mock_connection.execute.call_args_list
                         if 'CREATE OR REPLACE FUNCTION' in str(c)]
        self.assertGreater(len(function_calls), 0)
        
        # Check get_person_name function
        person_name_calls = [c for c in function_calls 
                            if 'get_person_name' in str(c)]
        self.assertEqual(len(person_name_calls), 1)
        
        # Check get_family_members function
        family_members_calls = [c for c in function_calls
                               if 'get_family_members' in str(c)]
        self.assertEqual(len(family_members_calls), 1)


class TestSchemaUpgrade(unittest.TestCase):
    """Test schema upgrade functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = MagicMock()
        self.schema = PostgreSQLSchema(self.mock_connection, use_jsonb=True)
        
    def test_upgrade_schema_noop(self):
        """Test upgrade when already at current version."""
        self.schema._set_schema_version = Mock()
        
        self.schema._upgrade_schema(SCHEMA_VERSION)
        
        # Should only update version
        self.schema._set_schema_version.assert_called_once_with(SCHEMA_VERSION)
        self.mock_connection.commit.assert_called_once()
        
    def test_get_schema_info(self):
        """Test retrieving schema information."""
        # Mock database queries
        self.schema._get_schema_version = Mock(return_value=1)
        self.mock_connection.fetchall.return_value = [
            ('person', '1.2 MB', 5),
            ('family', '500 KB', 4),
        ]
        
        info = self.schema.get_schema_info()
        
        self.assertEqual(info['version'], 1)
        self.assertTrue(info['use_jsonb'])
        self.assertIn('person', info['tables'])
        self.assertEqual(info['tables']['person']['size'], '1.2 MB')
        self.assertEqual(info['tables']['person']['columns'], 5)


if __name__ == '__main__':
    unittest.main()