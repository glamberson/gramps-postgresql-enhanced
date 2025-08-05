#!/usr/bin/env python3
"""
Type Validator for PostgreSQL Enhanced
Validates data types WITHOUT modifying them.
Accepts valid variations (e.g., SQLite booleans) but rejects invalid data.

NO FALLBACK POLICY: Invalid data is REJECTED with clear errors.
"""

import logging

log = logging.getLogger(".PostgreSQLEnhanced.TypeValidator")

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

def validate_boolean(value, field_name="field"):
    """
    Validate a boolean value.
    Accepts: True, False, 1, 0, None (as NULL)
    Rejects: Everything else with clear error
    """
    if value is None:
        return None  # NULL is valid for nullable boolean fields
    
    if isinstance(value, bool):
        return value  # Already a boolean
    
    if isinstance(value, int) and value in (0, 1):
        return bool(value)  # SQLite-style boolean (0=False, 1=True)
    
    # Everything else is INVALID
    raise ValidationError(
        f"Invalid boolean value for {field_name}: {repr(value)} "
        f"(type: {type(value).__name__}). "
        f"Expected: boolean, 0, 1, or None"
    )

def validate_integer(value, field_name="field", min_val=None, max_val=None):
    """
    Validate an integer value.
    Accepts: integers, None (as NULL)
    Rejects: Everything else with clear error
    """
    if value is None:
        return None  # NULL is valid for nullable integer fields
    
    if isinstance(value, bool):
        # Reject booleans as integers (Python quirk: bool is subclass of int)
        raise ValidationError(
            f"Invalid integer value for {field_name}: boolean {value}. "
            f"Expected: integer or None"
        )
    
    if isinstance(value, int):
        if min_val is not None and value < min_val:
            raise ValidationError(
                f"Integer value for {field_name} too small: {value} < {min_val}"
            )
        if max_val is not None and value > max_val:
            raise ValidationError(
                f"Integer value for {field_name} too large: {value} > {max_val}"
            )
        return value
    
    # Everything else is INVALID
    raise ValidationError(
        f"Invalid integer value for {field_name}: {repr(value)} "
        f"(type: {type(value).__name__}). "
        f"Expected: integer or None"
    )

def validate_string(value, field_name="field", max_length=None, allow_empty=True):
    """
    Validate a string value.
    Accepts: strings, None (as NULL)
    Rejects: Everything else with clear error
    """
    if value is None:
        return None  # NULL is valid for nullable string fields
    
    if isinstance(value, str):
        if not allow_empty and len(value) == 0:
            raise ValidationError(
                f"Empty string not allowed for {field_name}"
            )
        if max_length and len(value) > max_length:
            raise ValidationError(
                f"String too long for {field_name}: {len(value)} > {max_length}"
            )
        # Check for null bytes (PostgreSQL doesn't like them)
        if '\x00' in value:
            raise ValidationError(
                f"Null bytes not allowed in {field_name}"
            )
        return value
    
    # Everything else is INVALID
    raise ValidationError(
        f"Invalid string value for {field_name}: {repr(value)} "
        f"(type: {type(value).__name__}). "
        f"Expected: string or None"
    )

def validate_float(value, field_name="field"):
    """
    Validate a float value.
    Accepts: floats, integers (converted to float), None (as NULL)
    Rejects: Everything else with clear error
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    
    # Everything else is INVALID
    raise ValidationError(
        f"Invalid float value for {field_name}: {repr(value)} "
        f"(type: {type(value).__name__}). "
        f"Expected: number or None"
    )

def validate_gramps_object(obj):
    """
    Validate a Gramps object's data fields.
    Returns the object unchanged if valid.
    Raises ValidationError if any field is invalid.
    """
    try:
        # Get the serialized data to check types
        data = obj.serialize()
        obj_type = obj.__class__.__name__.lower()
        
        # Validate common fields
        if len(data) > 17:
            # Field 17 is change_time - must be integer or None
            try:
                validate_integer(data[17], f"{obj_type}.change_time")
            except ValidationError as e:
                raise ValidationError(f"Object {obj_type}: {e}")
        
        # Object-specific validation
        if obj_type == 'person':
            # Gender must be integer (0=unknown, 1=male, 2=female)
            if len(data) > 2:
                try:
                    validate_integer(data[2], "person.gender", min_val=0, max_val=2)
                except ValidationError as e:
                    raise ValidationError(f"Person gender: {e}")
            
            # Privacy must be boolean
            if len(data) > 19:
                try:
                    validate_boolean(data[19], "person.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Person privacy: {e}")
        
        elif obj_type == 'family':
            # Privacy must be boolean
            if len(data) > 15:
                try:
                    validate_boolean(data[15], "family.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Family privacy: {e}")
        
        elif obj_type == 'event':
            # Privacy must be boolean
            if len(data) > 11:
                try:
                    validate_boolean(data[11], "event.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Event privacy: {e}")
        
        elif obj_type == 'place':
            # Privacy must be boolean
            if len(data) > 17:
                try:
                    validate_boolean(data[17], "place.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Place privacy: {e}")
        
        elif obj_type == 'source':
            # Privacy must be boolean
            if len(data) > 11:
                try:
                    validate_boolean(data[11], "source.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Source privacy: {e}")
        
        elif obj_type == 'citation':
            # Confidence must be integer (0-4)
            if len(data) > 5:
                try:
                    validate_integer(data[5], "citation.confidence", min_val=0, max_val=4)
                except ValidationError as e:
                    raise ValidationError(f"Citation confidence: {e}")
            
            # Privacy must be boolean
            if len(data) > 8:
                try:
                    validate_boolean(data[8], "citation.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Citation privacy: {e}")
        
        elif obj_type == 'repository':
            # Privacy must be boolean
            if len(data) > 9:
                try:
                    validate_boolean(data[9], "repository.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Repository privacy: {e}")
        
        elif obj_type == 'media':
            # Privacy must be boolean
            if len(data) > 10:
                try:
                    validate_boolean(data[10], "media.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Media privacy: {e}")
        
        elif obj_type == 'note':
            # Format must be integer (0=formatted, 1=plain)
            if len(data) > 5:
                try:
                    validate_integer(data[5], "note.format", min_val=0, max_val=1)
                except ValidationError as e:
                    raise ValidationError(f"Note format: {e}")
            
            # Privacy must be boolean
            if len(data) > 6:
                try:
                    validate_boolean(data[6], "note.privacy")
                except ValidationError as e:
                    raise ValidationError(f"Note privacy: {e}")
        
        elif obj_type == 'tag':
            # Priority must be integer
            if len(data) > 2:
                try:
                    validate_integer(data[2], "tag.priority")
                except ValidationError as e:
                    raise ValidationError(f"Tag priority: {e}")
        
        # Object is valid
        return obj
        
    except ValidationError:
        raise  # Re-raise validation errors
    except Exception as e:
        # Any other error during validation
        raise ValidationError(f"Validation failed for {obj.__class__.__name__}: {e}")

def validate_for_column(value, column_type, column_name="column"):
    """
    Validate a value for a specific PostgreSQL column type.
    Returns the value (possibly converted) if valid.
    Raises ValidationError if invalid.
    """
    column_type = column_type.upper()
    
    if 'BOOLEAN' in column_type or 'BOOL' in column_type:
        return validate_boolean(value, column_name)
    
    elif 'INTEGER' in column_type or 'INT' in column_type or 'SERIAL' in column_type:
        return validate_integer(value, column_name)
    
    elif 'FLOAT' in column_type or 'DOUBLE' in column_type or 'REAL' in column_type:
        return validate_float(value, column_name)
    
    elif 'TEXT' in column_type or 'VARCHAR' in column_type or 'CHAR' in column_type:
        # Extract max length if specified
        import re
        length_match = re.search(r'\((\d+)\)', column_type)
        max_length = int(length_match.group(1)) if length_match else None
        return validate_string(value, column_name, max_length)
    
    elif 'JSON' in column_type:
        # JSON/JSONB can accept various types, but must be JSON-serializable
        import json
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError) as e:
            raise ValidationError(
                f"Invalid JSON value for {column_name}: {repr(value)}. Error: {e}"
            )
    
    else:
        # Unknown column type - accept as-is (let PostgreSQL validate)
        return value