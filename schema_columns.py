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
PostgreSQL Enhanced Schema Column Definitions

This module defines all the columns expected by Gramps DBAPI
for each table type, with their JSONB extraction paths.
"""

# Required columns for each table type based on DBAPI expectations
REQUIRED_COLUMNS = {
    'person': {
        'given_name': "json_data->'names'->0->'first_name'",
        'surname': "json_data->'names'->0->'surname'->>'surname'",
        'gramps_id': "json_data->>'gramps_id'"
    },
    'family': {
        'gramps_id': "json_data->>'gramps_id'"
    },
    'event': {
        'gramps_id': "json_data->>'gramps_id'"
    },
    'place': {
        'enclosed_by': "json_data->>'enclosed_by'",
        'gramps_id': "json_data->>'gramps_id'"
    },
    'source': {
        'gramps_id': "json_data->>'gramps_id'"
    },
    'citation': {
        'gramps_id': "json_data->>'gramps_id'"
    },
    'repository': {
        'gramps_id': "json_data->>'gramps_id'"
    },
    'media': {
        'gramps_id': "json_data->>'gramps_id'"
    },
    'note': {
        'gramps_id': "json_data->>'gramps_id'"
    },
    'tag': {
        'name': "json_data->>'name'",
        'gramps_id': "json_data->>'gramps_id'"  # Not in original but good to have
    }
}

# Indexes required by DBAPI
REQUIRED_INDEXES = {
    'person': ['gramps_id', 'surname'],
    'family': ['gramps_id'],
    'event': ['gramps_id'],
    'place': ['gramps_id', 'enclosed_by'],
    'source': ['gramps_id'],
    'citation': ['gramps_id'],
    'repository': ['gramps_id'],
    'media': ['gramps_id'],
    'note': ['gramps_id'],
    'tag': ['name']
}