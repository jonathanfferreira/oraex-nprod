#!/bin/bash
export ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_1
export PATH=$ORACLE_HOME/bin:$PATH
export ORACLE_SID=orcl

echo "--- CHECKING PMON ---"
ps -ef | grep pmon

echo "--- CHECKING LISTENER ---"
lsnrctl status

echo "--- CHECKING SQLPLUS ---"
sqlplus -S / as sysdba <<EOF
set heading off feedback off
select 'INSTANCE: ' || instance_name || ' | STATUS: ' || status from v\$instance;
exit;
EOF
