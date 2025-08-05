"""Mock Gramps modules for testing without full Gramps installation."""

import sys
from unittest.mock import MagicMock, Mock

# Create mock modules
sys.modules["gramps"] = MagicMock()
sys.modules["gramps.gen"] = MagicMock()
sys.modules["gramps.gen.const"] = MagicMock()
sys.modules["gramps.gen.db"] = MagicMock()
sys.modules["gramps.gen.db.dbconst"] = MagicMock()
sys.modules["gramps.gen.db.exceptions"] = MagicMock()
sys.modules["gramps.gen.lib"] = MagicMock()
sys.modules["gramps.gen.lib.serialize"] = MagicMock()
sys.modules["gramps.plugins"] = MagicMock()
sys.modules["gramps.plugins.db"] = MagicMock()
sys.modules["gramps.plugins.db.dbapi"] = MagicMock()
sys.modules["gramps.plugins.db.dbapi.dbapi"] = MagicMock()
sys.modules["gramps.gen.db.generic"] = MagicMock()


# Mock specific classes and functions
class MockDBAPI:
    def __init__(self):
        self.undolog = None
        self.readonly = False
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

        self.add_person = MagicMock()
        self.add_family = MagicMock()
        self.add_event = MagicMock()
        self.add_place = MagicMock()
        self.add_source = MagicMock()

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

        # Add get by gramps_id methods
        self.get_person_from_gramps_id = MagicMock()
        self.get_family_from_gramps_id = MagicMock()
        self.get_event_from_gramps_id = MagicMock()
        self.get_place_from_gramps_id = MagicMock()
        self.get_source_from_gramps_id = MagicMock()


sys.modules["gramps.plugins.db.dbapi.dbapi"].DBAPI = MockDBAPI


class MockDbConnectionError(Exception):
    pass


sys.modules["gramps.gen.db.exceptions"].DbConnectionError = MockDbConnectionError


class MockJSONSerializer:
    def object_to_data(self, obj):
        return {}


sys.modules["gramps.gen.lib.serialize"].JSONSerializer = MockJSONSerializer


class MockDbGenericUndo:
    def __init__(self, db, log):
        pass

    def open(self):
        pass


sys.modules["gramps.gen.db.generic"].DbGenericUndo = MockDbGenericUndo


# Mock locale
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


# Add gender constants
class PersonGender:
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2
    OTHER = 3


# Mock Gramps data classes with full functionality
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


class MockName:
    def __init__(self):
        self.first_name = ""
        self.surname_list = []

    def set_first_name(self, name):
        self.first_name = name

    def add_surname(self, surname):
        self.surname_list.append(surname)


class MockSurname:
    def __init__(self):
        self.surname = ""

    def set_surname(self, surname):
        self.surname = surname


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


class MockEvent:
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


class MockDbTxn:
    def __init__(self, msg, db):
        self.msg = msg
        self.db = db

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


sys.modules["gramps.gen.lib"].Person = MockPerson
sys.modules["gramps.gen.lib"].Name = MockName
sys.modules["gramps.gen.lib"].Surname = MockSurname
sys.modules["gramps.gen.lib"].Family = MockFamily
sys.modules["gramps.gen.lib"].Event = MockEvent
sys.modules["gramps.gen.lib"].Place = MockPlace
sys.modules["gramps.gen.lib"].Source = MockSource
sys.modules["gramps.gen.db"].DbTxn = MockDbTxn


# Add more mock classes that tests might need
class MockCitation:
    def __init__(self):
        self.handle = None
        self.gramps_id = None


class MockRepository:
    def __init__(self):
        self.handle = None
        self.gramps_id = None

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id


class MockMedia:
    def __init__(self):
        self.handle = None
        self.gramps_id = None

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id


class MockNote:
    def __init__(self):
        self.handle = None
        self.gramps_id = None

    def set_handle(self, handle):
        self.handle = handle

    def set_gramps_id(self, gramps_id):
        self.gramps_id = gramps_id


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


# Add event types
class MockEventType:
    BIRTH = 1
    DEATH = 2
    MARRIAGE = 3

    def __init__(self, value=None):
        self.value = value


# Add child reference
class MockChildRef:
    def __init__(self):
        self.ref = None


sys.modules["gramps.gen.lib"].Citation = MockCitation
sys.modules["gramps.gen.lib"].Repository = MockRepository
sys.modules["gramps.gen.lib"].Media = MockMedia
sys.modules["gramps.gen.lib"].Note = MockNote
sys.modules["gramps.gen.lib"].Tag = MockTag
sys.modules["gramps.gen.lib"].EventType = MockEventType
sys.modules["gramps.gen.lib"].ChildRef = MockChildRef
