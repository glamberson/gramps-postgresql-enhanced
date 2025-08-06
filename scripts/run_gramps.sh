#!/bin/bash
# Script to run Gramps properly

# First, exit any virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment..."
    deactivate 2>/dev/null || true
fi

# Try different methods to run Gramps

# Method 1: System-installed Gramps
if command -v gramps &> /dev/null; then
    echo "Running system-installed Gramps..."
    /usr/bin/gramps "$@"
    exit $?
fi

# Method 2: Run from source (if available)
GRAMPS_SOURCE="/home/greg/genealogy-ai/gramps-project-gramps-e960164"
if [ -d "$GRAMPS_SOURCE" ]; then
    echo "Running Gramps from source..."
    cd "$GRAMPS_SOURCE"
    GRAMPS_RESOURCES="$GRAMPS_SOURCE" python3 -m gramps "$@"
    exit $?
fi

# Method 3: Try with explicit resource path
echo "Trying with explicit resource path..."
GRAMPS_RESOURCES=/usr/share/gramps gramps "$@"