-- Fix collation version mismatch for all databases
-- This script generates and executes ALTER COLLATION commands for each database

\echo 'Starting collation refresh for all databases...'

-- Create a temporary script to fix each database
\o /tmp/fix_collations_temp.sql

SELECT 
    'echo ''Fixing database: ' || datname || ''';' || E'\n' ||
    '\c ' || datname || E'\n' ||
    'ALTER COLLATION pg_catalog."en_US" REFRESH VERSION;' || E'\n'
FROM pg_database 
WHERE datname NOT IN ('template0', 'template1')
ORDER BY datname;

\o

-- Execute the generated script
\echo 'Executing collation fixes...'
\i /tmp/fix_collations_temp.sql

\echo 'Collation refresh complete!'