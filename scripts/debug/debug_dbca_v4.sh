#!/bin/bash
export ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_1
export PATH=$ORACLE_HOME/bin:$PATH
export CV_ASSUME_DISTID=OL7
unset ORACLE_SID

echo ">>> DEBUG V4: New SID"
dbca -silent -createDatabase \
    -templateName General_Purpose.dbc \
    -gdbname orclnew \
    -sid orclnew \
    -sysPassword "Oracle_12345" \
    -systemPassword "Oracle_12345" \
    -databaseType MULTIPURPOSE \
    -memoryPercentage 30 \
    -emConfiguration NONE \
    -storageType FS \
    -datafileDestination /u02/oracle/oradata
