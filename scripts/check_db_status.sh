#!/bin/bash
source /home/oracle/.db_profile_orcl
sqlplus -s / as sysdba <<EOF
set head off
select 'DATABASE_STATUS: ' || status from v\$instance;
EOF
