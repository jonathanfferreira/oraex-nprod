#!/bin/bash
export ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_1
export PATH=$ORACLE_HOME/bin:$PATH

dbca -silent -createDatabase \
    -templateName General_Purpose.dbc \
    -gdbname orcl \
    -sid orcl \
    -responseFile NO_VALUE \
    -characterSet AL32UTF8 \
    -sysPassword "Oracle123!" \
    -systemPassword "Oracle123!" \
    -createAsContainerDatabase true \
    -pdbName orclpdb \
    -databaseType MULTIPURPOSE \
    -memoryPercentage 40 \
    -emConfiguration NONE \
    -storageType FS \
    -datafileDestination /u02/oracle/oradata \
    -recoveryAreaDestination /u02/oracle/fast_recovery_area
