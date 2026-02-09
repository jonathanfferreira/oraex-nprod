#!/bin/bash
export ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_1
export PATH=$ORACLE_HOME/bin:$PATH
export CV_ASSUME_DISTID=OL7

echo ">>> DEBUG V2: Checking Environment"
whoami
echo "DISTID: $CV_ASSUME_DISTID"
ls -ld /u02/oracle/oradata

echo ">>> DEBUG V2: Launching DBCA..."
dbca -silent -createDatabase \
    -templateName General_Purpose.dbc \
    -gdbname orcl \
    -sid orcl \
    -responseFile NO_VALUE \
    -characterSet AL32UTF8 \
    -sysPassword "Oracle_12345" \
    -systemPassword "Oracle_12345" \
    -pdbAdminPassword "Oracle_12345" \
    -createAsContainerDatabase true \
    -pdbName orclpdb \
    -databaseType MULTIPURPOSE \
    -memoryPercentage 30 \
    -emConfiguration NONE \
    -storageType FS \
    -datafileDestination /u02/oracle/oradata \
    -recoveryAreaDestination /u02/oracle/fast_recovery_area
