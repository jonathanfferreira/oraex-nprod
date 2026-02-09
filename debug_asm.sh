#!/bin/bash
echo "=== ASM DEBUG START ==="
LOG_FILE=$(ls -t /u01/app/grid/cfgtoollogs/asmca/asmca-*.log | head -n 1)
echo "Latest Log: $LOG_FILE"
echo "--- ORA Errors ---"
grep "ORA-" $LOG_FILE || echo "No ORA- errors found in grep."
echo "--- Last 20 Lines ---"
tail -n 20 $LOG_FILE
echo "--- Resource Status ---"
/u01/app/19.0.0/grid/bin/crsctl stat res -t
echo "=== ASM DEBUG END ==="
