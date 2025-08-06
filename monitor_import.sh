#\!/bin/bash
# Monitor script for GEDCOM import
while true; do
    echo "=== $(date +%H:%M:%S) ==="
    echo "PostgreSQL connections:"
    PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -t -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'gramps_monolithic' AND state \!= 'idle';" 2>/dev/null
    
    echo "Record counts:"
    for table in person family event place source citation media repository note tag; do
        count=$(PGPASSWORD='GenealogyData2025' psql -h 192.168.10.90 -U genealogy_user -d gramps_monolithic -t -c "SELECT COUNT(*) FROM tree_*_$table;" 2>/dev/null | head -1)
        printf "  %-12s %s\n" "$table:" "$count"
    done
    
    echo "Log size:"
    ls -lh ~/gramps_debug_logs/gramps_full_debug_*.log 2>/dev/null | tail -1 | awk '{print "  "$5}'
    
    sleep 30
done
