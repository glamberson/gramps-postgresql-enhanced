#!/bin/bash
# Complete Gramps Debug Launcher with ALL Debug Options
# This enables EVERY debug logger for comprehensive troubleshooting

# Create debug log directory
mkdir -p ~/gramps_debug_logs

# Get timestamp for unique log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE=~/gramps_debug_logs/gramps_full_debug_${TIMESTAMP}.log

echo "Starting Gramps with COMPLETE debug logging..."
echo "Log file: $LOGFILE"
echo "Press Ctrl+C to stop"
echo ""

# Start Gramps with ALL debug loggers
gramps \
  --debug=. \
  --debug=.GedcomImport \
  --debug=.libgedcom \
  --debug=.PostgreSQLEnhanced \
  --debug=.PostgreSQLEnhanced.TablePrefixWrapper \
  --debug=.PostgreSQLEnhanced.Schema \
  --debug=.PostgreSQLEnhanced.Migration \
  --debug=.PostgreSQLEnhanced.Queries \
  --debug=.PostgreSQLEnhanced.Debug \
  --debug=.PostgreSQLEnhanced.TypeValidator \
  --debug=.PostgreSQLEnhanced.TypeSanitizer \
  --debug=database \
  --debug=.clidbman \
  --debug=.grampscli \
  --debug=.odfbackend.py \
  --debug=.cite \
  --debug=.ImportProGen \
  --debug=maps.selectionlayer \
  --debug=maps.dummylayer \
  --debug=.RebuildRefMap \
  --debug=maps.datelayer \
  --debug=.libcairodoc \
  --debug=maps.messagelayer \
  --debug=.libmetadata \
  --debug=maps.placeselection \
  --debug=maps.libkml \
  --debug=.latexdoc \
  --debug=maps.markerlayer \
  --debug=.cairodoc \
  --debug=maps.lifeway \
  --debug=.GtkPrint \
  --debug=maps.geography \
  --debug=.rtfdoc \
  --debug=.htmldoc \
  --debug=.gui.editors.EditNote \
  --debug=.gui.personview \
  --debug=maps.osmgps \
  --debug=.ColumnOrder \
  --debug=.upgrade \
  --debug=.NarrativeWeb \
  --debug=.thumbnail \
  --debug=Gramps \
  2>&1 | tee "$LOGFILE"

echo ""
echo "Debug session ended. Log saved to: $LOGFILE"
echo ""
echo "Quick analysis commands:"
echo "  View errors:    grep -E 'ERROR|CRITICAL' $LOGFILE"
echo "  View warnings:  grep WARNING $LOGFILE"
echo "  View SQL:       grep -E 'Executing SQL|INSERT|UPDATE|DELETE' $LOGFILE"
echo "  View GEDCOM:    grep -i gedcom $LOGFILE"
echo "  View PostgreSQL: grep -i postgres $LOGFILE"