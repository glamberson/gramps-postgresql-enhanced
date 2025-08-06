#!/bin/bash

# Script to register an existing PostgreSQL tree with Gramps
# Usage: ./register_existing_tree.sh <tree_id> <tree_name>

TREE_ID="${1}"
TREE_NAME="${2}"

if [ -z "${TREE_ID}" ] || [ -z "${TREE_NAME}" ]; then
    echo "Usage: $0 <tree_id> <tree_name>"
    echo "Example: $0 68932301 'Ancestry Import 86k'"
    echo ""
    echo "Available unregistered trees in database:"
    export PGPASSWORD='GenealogyData2025'
    psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -t -c "
        SELECT DISTINCT substring(tablename from 'tree_([^_]+)') as tree_id 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'tree_%'
        AND substring(tablename from 'tree_([^_]+)') NOT IN (
            SELECT basename(path) 
            FROM (SELECT unnest(string_to_array('$(ls -d ~/.local/share/gramps/grampsdb/*/ 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ')', ' ')) as basename) as paths
        )
        ORDER BY tree_id;"
    exit 1
fi

GRAMPS_DB_DIR="${HOME}/.local/share/gramps/grampsdb"
TREE_DIR="${GRAMPS_DB_DIR}/${TREE_ID}"

# Check if already registered
if [ -d "${TREE_DIR}" ]; then
    echo "Tree ${TREE_ID} is already registered as '$(cat ${TREE_DIR}/name.txt 2>/dev/null)'"
    exit 1
fi

# Create tree directory
echo "Registering tree ${TREE_ID} as '${TREE_NAME}'..."
mkdir -p "${TREE_DIR}"

# Register as PostgreSQL Enhanced
echo "postgresqlenhanced" > "${TREE_DIR}/database.txt"

# Set the name
echo "${TREE_NAME}" > "${TREE_DIR}/name.txt"

echo "Success! Tree ${TREE_ID} registered as '${TREE_NAME}'"
echo "The tree will appear in Gramps Family Tree Manager after restart."

# Show tree statistics
echo ""
echo "Tree statistics:"
export PGPASSWORD='GenealogyData2025'
psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -c "
    SELECT 
        'Persons' as type, COUNT(*) as count 
    FROM tree_${TREE_ID}_person
    UNION ALL
    SELECT 'Families', COUNT(*) FROM tree_${TREE_ID}_family
    UNION ALL  
    SELECT 'Events', COUNT(*) FROM tree_${TREE_ID}_event
    UNION ALL
    SELECT 'Places', COUNT(*) FROM tree_${TREE_ID}_place
    UNION ALL
    SELECT 'Sources', COUNT(*) FROM tree_${TREE_ID}_source
    UNION ALL
    SELECT 'Citations', COUNT(*) FROM tree_${TREE_ID}_citation;"