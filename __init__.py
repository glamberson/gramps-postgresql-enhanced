#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025 Greg Lamberson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

"""PostgreSQL Enhanced Database Backend for Gramps"""

# Make PostgreSQLEnhanced class available at package level
from .postgresqlenhanced import PostgreSQLEnhanced

__all__ = ['PostgreSQLEnhanced']

__version__ = '1.0.0'
__author__ = 'Greg Lamberson'