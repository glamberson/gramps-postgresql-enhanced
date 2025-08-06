#\!/bin/bash
# Quick check of current database state
echo 'Current trees in database:'
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -t -c "
SELECT DISTINCT substring(tablename from 1 for 13) as tree_prefix, 
       COUNT(*) as table_count 
FROM pg_tables 
WHERE tablename LIKE 'tree_%' 
GROUP BY tree_prefix;" 2>/dev/null

echo -e '\nDatabase size:'
PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -t -c "
SELECT pg_size_pretty(pg_database_size('gramps_monolithic'));" 2>/dev/null
