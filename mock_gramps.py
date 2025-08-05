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

"""Mock Gramps modules for testing without full Gramps installation."""

import sys
from unittest.mock import MagicMock, Mock

# Add real Gramps to path if available
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Try to import real Gramps modules first
try:
    # Import real DBAPI and other critical modules
    from gramps.plugins.db.dbapi.dbapi import DBAPI as RealDBAPI
    from gramps.gen.db.exceptions import DbConnectionError as RealDbConnectionError
    from gramps.gen.lib.serialize import JSONSerializer as RealJSONSerializer
    # Import real Gramps lib classes
    from gramps.gen.lib import Person as RealPerson
    from gramps.gen.lib import Family as RealFamily
    from gramps.gen.lib import Event as RealEvent
    from gramps.gen.lib import Place as RealPlace
    from gramps.gen.lib import Source as RealSource
    from gramps.gen.lib import Name as RealName
    from gramps.gen.lib import Surname as RealSurname
    from gramps.gen.db import DbTxn as RealDbTxn
    # Try to import DbGenericUndo
    try:
        from gramps.gen.db.generic import DbGenericUndo as RealDbGenericUndo
    except ImportError:
        RealDbGenericUndo = None
    REAL_GRAMPS_AVAILABLE = True
except ImportError:
    REAL_GRAMPS_AVAILABLE = False
    RealDBAPI = None
    RealDbConnectionError = Exception
    RealJSONSerializer = None
    RealPerson = None
    RealFamily = None
    RealEvent = None
    RealPlace = None
    RealSource = None
    RealName = None
    RealSurname = None
    RealDbTxn = None
    RealDbGenericUndo = None

# Only mock modules that aren't critical for database operations
if not REAL_GRAMPS_AVAILABLE:
    # Create mock modules only if real Gramps is not available
    sys.modules["gramps"] = MagicMock()
    sys.modules["gramps.gen"] = MagicMock()
    sys.modules["gramps.gen.const"] = MagicMock()
    sys.modules["gramps.gen.db"] = MagicMock()
    sys.modules["gramps.gen.db.dbconst"] = MagicMock()
    sys.modules["gramps.gen.db.exceptions"] = MagicMock()
    sys.modules["gramps.gen.lib"] = MagicMock()
    sys.modules["gramps.gen.lib.serialize"] = MagicMock()
    sys.modules["gramps.gen.db.generic"] = MagicMock()
else:
    # Only mock the parts we need to mock
    if "gramps.gen.const" not in sys.modules:
        sys.modules["gramps.gen.const"] = MagicMock()
    if "gramps.gen.db.generic" not in sys.modules:
        sys.modules["gramps.gen.db.generic"] = MagicMock()


# -------------------------------------------------------------------------
#
# MockDBAPI - No longer needed, we'll use the real DBAPI
#
# -------------------------------------------------------------------------

# We'll just skip creating MockDBAPI and not replace DBAPI
"""
class MockDBAPI:
    def __init__(self):
        # Initialize base class if it's the real DBAPI
        if REAL_DBAPI_AVAILABLE:
            super().__init__()
        
        # Set up mock attributes
        self.undolog = None
        self.readonly = False
        self.transaction = None
        self._txn_begin = MagicMock()
        self._txn_commit = MagicMock()
        self.execute = MagicMock()
        self.fetchone = MagicMock()
        self.fetchall = MagicMock()
        self.close = MagicMock()

        # Add methods that tests might call
        self.get_person_handles = MagicMock(return_value=[])
        self.get_family_handles = MagicMock(return_value=[])
        self.get_event_handles = MagicMock(return_value=[])
        self.get_place_handles = MagicMock(return_value=[])
        self.get_source_handles = MagicMock(return_value=[])
        self.get_citation_handles = MagicMock(return_value=[])
        self.get_repository_handles = MagicMock(return_value=[])
        self.get_media_handles = MagicMock(return_value=[])
        self.get_note_handles = MagicMock(return_value=[])
        self.get_tag_handles = MagicMock(return_value=[])

        # Don't override add_ methods - let them be inherited from DBAPI

        self.commit_person = MagicMock()
        self.commit_family = MagicMock()
        self.commit_event = MagicMock()
        self.commit_place = MagicMock()
        self.commit_source = MagicMock()

        self.get_person_from_handle = MagicMock()
        self.get_family_from_handle = MagicMock()
        self.get_event_from_handle = MagicMock()
        self.get_place_from_handle = MagicMock()
        self.get_source_from_handle = MagicMock()

        self.get_number_of_people = MagicMock(return_value=0)
        self.get_number_of_families = MagicMock(return_value=0)
        self.get_number_of_events = MagicMock(return_value=0)
        self.get_number_of_places = MagicMock(return_value=0)
        self.get_number_of_sources = MagicMock(return_value=0)

        # Add iterator methods
        self.iter_person_handles = MagicMock(return_value=iter([]))
        self.iter_family_handles = MagicMock(return_value=iter([]))
        self.iter_event_handles = MagicMock(return_value=iter([]))
        self.iter_place_handles = MagicMock(return_value=iter([]))
        self.iter_source_handles = MagicMock(return_value=iter([]))

        self.iter_people = MagicMock(return_value=iter([]))
        self.iter_families = MagicMock(return_value=iter([]))
        self.iter_events = MagicMock(return_value=iter([]))
        self.iter_places = MagicMock(return_value=iter([]))
        self.iter_sources = MagicMock(return_value=iter([]))
        
    def transaction_begin(self, transaction):
        # Begin a transaction.
        self.transaction = transaction
        if hasattr(self, 'dbapi') and hasattr(self.dbapi, 'begin'):
            self.dbapi.begin()
        return transaction
    
    def transaction_commit(self, transaction):
        # Commit a transaction.
        if hasattr(self, 'dbapi') and hasattr(self.dbapi, 'commit'):
            self.dbapi.commit()
        self.transaction = None
    
    def transaction_abort(self, transaction):
        # Abort a transaction.
        if hasattr(self, 'dbapi') and hasattr(self.dbapi, 'rollback'):
            self.dbapi.rollback()
        self.transaction = None
"""

# Don't replace DBAPI - we'll use the real one
# sys.modules["gramps.plugins.db.dbapi.dbapi"].DBAPI = MockDBAPI


# -------------------------------------------------------------------------
#
# MockDbConnectionError
#
# -------------------------------------------------------------------------
if REAL_GRAMPS_AVAILABLE:
    # Use the real DbConnectionError
    MockDbConnectionError = RealDbConnectionError
else:
    class MockDbConnectionError(Exception):
        pass
    sys.modules["gramps.gen.db.exceptions"].DbConnectionError = MockDbConnectionError


# -------------------------------------------------------------------------
#
# MockJSONSerializer
#
# -------------------------------------------------------------------------
if REAL_GRAMPS_AVAILABLE:
    # Use the real JSONSerializer
    MockJSONSerializer = RealJSONSerializer
else:
    class MockJSONSerializer:
        def object_to_data(self, obj):
            return {}
    sys.modules["gramps.gen.lib.serialize"].JSONSerializer = MockJSONSerializer


# -------------------------------------------------------------------------
#
# MockDbGenericUndo
#
# -------------------------------------------------------------------------
if REAL_GRAMPS_AVAILABLE and RealDbGenericUndo:
    # Use the real DbGenericUndo
    MockDbGenericUndo = RealDbGenericUndo
else:
    class MockDbGenericUndo:
        def __init__(self, db, log):
            self.db = db
            self.log = log
            self.undo_data = []
            
        def open(self):
            pass
            
        def append(self, data):
            """Append undo data."""
            self.undo_data.append(data)
            
        def undo(self):
            """Undo last operation."""
            if self.undo_data:
                return self.undo_data.pop()
            return None
            
        def redo(self):
            """Redo operation."""
            pass
            
        def clear(self):
            """Clear undo data."""
            self.undo_data = []

if not REAL_GRAMPS_AVAILABLE or not RealDbGenericUndo:
    sys.modules["gramps.gen.db.generic"].DbGenericUndo = MockDbGenericUndo


# -------------------------------------------------------------------------
#
# MockLocale
#
# -------------------------------------------------------------------------
if REAL_GRAMPS_AVAILABLE:
    try:
        from gramps.gen.const import GRAMPS_LOCALE
    except ImportError:
        # Create a mock locale if not available
        class MockLocale:
            def get_addon_translator(self, file):
                return self

            def gettext(self, text):
                return text

            def get_collation(self):
                """Return a collation string for testing."""
                return "en_US.UTF-8"

            translation = property(lambda self: self)
        
        sys.modules["gramps.gen.const"].GRAMPS_LOCALE = MockLocale()
else:
    class MockLocale:
        def get_addon_translator(self, file):
            return self

        def gettext(self, text):
            return text

        def get_collation(self):
            """Return a collation string for testing."""
            return "en_US.UTF-8"

        translation = property(lambda self: self)

    sys.modules["gramps.gen.const"].GRAMPS_LOCALE = MockLocale()

# Mock the _ function
import builtins

builtins._ = lambda x: x


# -------------------------------------------------------------------------
#
# PersonGender
#
# -------------------------------------------------------------------------
class PersonGender:
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2
    OTHER = 3


# -------------------------------------------------------------------------
#
# MockPerson
#
# -------------------------------------------------------------------------
class MockPerson:
    # Gender constants
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2
    OTHER = 3

    def __init__(self):
        self.handle = None
        self.gramps_id = None
        self.primary_name = MockName()
        self.gender = 0  # Unknown

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id

    def get_handle(self):
        return self.handle

    def get_primary_name(self):
        return self.primary_name

    def set_primary_name(self, name):
        self.primary_name = name

    def set_gender(self, gender):
        self.gender = gender

    def get_gender(self):
        return self.gender
    def add_url(self, url):
        """Add URL to person."""
        pass
    
    def add_event_ref(self, event_ref):
        """Add event reference."""
        pass



# -------------------------------------------------------------------------
#
# MockName
#
# -------------------------------------------------------------------------
class MockName:
    def __init__(self):
        self.first_name = ""
        self.surname_list = []

    def set_first_name(self, name):
        self.first_name = name

    def add_surname(self, surname):
        self.surname_list.append(surname)
    def get_first_name(self):
        return self.first_name
    
    def get_surname_list(self):
        return self.surname_list



# -------------------------------------------------------------------------
#
# MockSurname
#
# -------------------------------------------------------------------------
class MockSurname:
    def __init__(self):
        self.surname = ""

    def set_surname(self, surname):
        self.surname = surname
    def get_surname(self):
        return self.surname



# -------------------------------------------------------------------------
#
# MockFamily
#
# -------------------------------------------------------------------------
class MockFamily:
    def __init__(self):
        self.handle = None
        self.gramps_id = None
        self.father_handle = None
        self.mother_handle = None
        self.child_ref_list = []

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id

    def set_father_handle(self, handle):
        self.father_handle = handle

    def set_mother_handle(self, handle):
        self.mother_handle = handle

    def add_child_ref(self, ref):
        self.child_ref_list.append(ref)
    def get_handle(self):
        return self.handle
    
    def get_father_handle(self):
        return self.father_handle
    
    def get_mother_handle(self):
        return self.mother_handle
    
    def get_child_ref_list(self):
        return self.child_ref_list
    
    def add_event_ref(self, event_ref):
        pass



# -------------------------------------------------------------------------
#
# MockEvent
#
# -------------------------------------------------------------------------
class MockEvent:
    # Event type constants
    BIRTH = 1
    DEATH = 2
    MARRIAGE = 3
    
    def __init__(self):
        self.handle = None
        self.gramps_id = None
        self.type = None
        self.date = None
        self.description = ""

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id

    def set_type(self, event_type):
        self.type = event_type

    def set_date_object(self, date):
        self.date = date

    def set_description(self, desc):
        self.description = desc

    def get_description(self):
        return self.description
    def get_handle(self):
        return self.handle
    
    def set_place_handle(self, handle):
        self.place_handle = handle
    
    def get_place_handle(self):
        return getattr(self, 'place_handle', None)



# -------------------------------------------------------------------------
#
# MockPlace
#
# -------------------------------------------------------------------------
class MockPlace:
    def __init__(self):
        self.handle = None
        self.gramps_id = None
        self.title = ""
        self.code = ""

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id

    def set_title(self, title):
        self.title = title

    def set_code(self, code):
        self.code = code

    def get_code(self):
        return self.code
    def set_name(self, name):
        self.name = name



# -------------------------------------------------------------------------
#
# MockSource
#
# -------------------------------------------------------------------------
class MockSource:
    def __init__(self):
        self.handle = None
        self.gramps_id = None
        self.title = ""
        self.author = ""

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id

    def set_title(self, title):
        self.title = title

    def set_author(self, author):
        self.author = author

    def get_author(self):
        return self.author
    def set_publication_info(self, info):
        self.pubinfo = info



# -------------------------------------------------------------------------
#
# MockDbTxn
#
# -------------------------------------------------------------------------
from collections import defaultdict

class MockDbTxn(defaultdict):
    """Mock transaction that mimics the real DbTxn class."""
    
    def __init__(self, msg, db, batch=False):
        # Initialize as a defaultdict like the real DbTxn
        defaultdict.__init__(self, list)
        self.msg = msg
        self.db = db
        self.batch = batch
        self.first = None
        self.last = None
        
        # Call transaction_begin if available (matches real DbTxn)
        if hasattr(db, 'transaction_begin'):
            db.transaction_begin(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Match the real DbTxn behavior - call transaction_commit/abort on the db
        if exc_type is None:
            # No exception - commit the transaction
            if hasattr(self.db, 'transaction_commit'):
                self.db.transaction_commit(self)
            elif hasattr(self.db, 'dbapi') and hasattr(self.db.dbapi, 'commit'):
                # Fallback to direct commit
                self.db.dbapi.commit()
        else:
            # Exception occurred - abort transaction
            if hasattr(self.db, 'transaction_abort'):
                self.db.transaction_abort(self)
            elif hasattr(self.db, 'dbapi') and hasattr(self.db.dbapi, 'rollback'):
                # Fallback to direct rollback
                self.db.dbapi.rollback()
        # Don't suppress the exception
        return False
    
    def get_description(self):
        """Return the transaction description."""
        return self.msg
    
    def set_description(self, msg):
        """Set the transaction description."""
        self.msg = msg


# Use real classes if available, otherwise use mocks
if REAL_GRAMPS_AVAILABLE:
    # Real classes are already imported, make them available as our "Mock" versions
    Person = RealPerson
    Name = RealName
    Surname = RealSurname
    Family = RealFamily
    Event = RealEvent
    Place = RealPlace
    Source = RealSource
    DbTxn = RealDbTxn
else:
    # Use mock classes and register them
    Person = MockPerson
    Name = MockName
    Surname = MockSurname
    Family = MockFamily
    Event = MockEvent
    Place = MockPlace
    Source = MockSource
    DbTxn = MockDbTxn
    
    sys.modules["gramps.gen.lib"].Person = MockPerson
    sys.modules["gramps.gen.lib"].Name = MockName
    sys.modules["gramps.gen.lib"].Surname = MockSurname
    sys.modules["gramps.gen.lib"].Family = MockFamily
    sys.modules["gramps.gen.lib"].Event = MockEvent
    sys.modules["gramps.gen.lib"].Place = MockPlace
    sys.modules["gramps.gen.lib"].Source = MockSource
    sys.modules["gramps.gen.db"].DbTxn = MockDbTxn


# -------------------------------------------------------------------------
#
# MockCitation
#
# -------------------------------------------------------------------------
class MockCitation:
    def __init__(self):
        self.handle = None
        self.gramps_id = None


# -------------------------------------------------------------------------
#
# MockRepository
#
# -------------------------------------------------------------------------
class MockRepository:
    def __init__(self):
        self.handle = None
        self.gramps_id = None

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id
    def set_name(self, name):
        self.name = name



# -------------------------------------------------------------------------
#
# MockMedia
#
# -------------------------------------------------------------------------
class MockMedia:
    def __init__(self):
        self.handle = None
        self.gramps_id = None

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id
    def set_path(self, path):
        self.path = path



# -------------------------------------------------------------------------
#
# MockNote
#
# -------------------------------------------------------------------------
class MockNote:
    def __init__(self):
        self.handle = None
        self.gramps_id = None

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id
    def set_styledtext(self, text):
        self.text = text



# -------------------------------------------------------------------------
#
# MockTag
#
# -------------------------------------------------------------------------
class MockTag:
    def __init__(self):
        self.handle = None
        self.name = ""

    def set_handle(self, handle):
        self.handle = handle

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name
    def set_color(self, color):
        self.color = color



# -------------------------------------------------------------------------
#
# MockEventType
#
# -------------------------------------------------------------------------
class MockEventType:
    BIRTH = 1
    DEATH = 2
    MARRIAGE = 3

    def __init__(self, value=None):
        self.value = value


# -------------------------------------------------------------------------
#
# MockChildRef
#
# -------------------------------------------------------------------------
class MockChildRef:
    def __init__(self):
        self.ref = None
    def set_reference_handle(self, handle):
        self.ref = handle



if not REAL_GRAMPS_AVAILABLE:
    sys.modules["gramps.gen.lib"].Citation = MockCitation
    sys.modules["gramps.gen.lib"].Repository = MockRepository
    sys.modules["gramps.gen.lib"].Media = MockMedia
    sys.modules["gramps.gen.lib"].Note = MockNote
    sys.modules["gramps.gen.lib"].Tag = MockTag
    sys.modules["gramps.gen.lib"].EventType = MockEventType
    sys.modules["gramps.gen.lib"].ChildRef = MockChildRef

# Export classes for tests to use
__all__ = [
    'Person', 'Family', 'Event', 'Place', 'Source',
    'Name', 'Surname', 'DbTxn',
    'MockCitation', 'MockRepository', 'MockMedia',
    'MockNote', 'MockTag', 'MockEventType', 'MockChildRef'
]
