#!/bin/bash
export ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_1
export PATH=$ORACLE_HOME/bin:$PATH

echo ">>> Checking oracle binary size before relink:"
ls -l $ORACLE_HOME/bin/oracle

echo ">>> Running relink all..."
$ORACLE_HOME/bin/relink all

echo ">>> Checking oracle binary size after relink:"
ls -l $ORACLE_HOME/bin/oracle
