#!/bin/bash

# Fix collation version mismatch for all PostgreSQL databases
# Run this on the PostgreSQL server as postgres user

echo "Starting collation version refresh for all databases..."

# Get list of all databases (excluding templates)
databases=$(psql -tc "SELECT datname FROM pg_database WHERE datname NOT IN ('template0', 'template1', 'postgres');")

# Counter for progress
count=0
total=$(echo "$databases" | wc -w)

# Fix collation for each database
for db in $databases; do
    count=$((count + 1))
    echo "[$count/$total] Fixing collation for database: $db"
    
    # Run the ALTER COLLATION command
    psql -d "$db" -c "ALTER COLLATION pg_catalog.\"en_US\" REFRESH VERSION;" 2>&1 | grep -E "(ALTER COLLATION|NOTICE|ERROR)"
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Success"
    else
        echo "  ✗ Failed"
    fi
done

echo "Collation refresh complete!"

# Check for other glibc-related issues
echo ""
echo "Checking for other collations that might need updating..."
psql -c "SELECT DISTINCT collname, collversion FROM pg_collation WHERE collversion IS NOT NULL AND collname != 'en_US' ORDER BY collname LIMIT 10;"