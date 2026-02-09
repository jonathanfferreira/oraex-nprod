#!/bin/bash
# =============================================================================
# Script: setup_oracle_profiles.sh
# Descrição: Configura os profiles .bash_profile e .db_profile_orcl (Padrão Getnet)
# =============================================================================

ORACLE_HOME="/u01/app/oracle/product/19.0.0/dbhome_1"
ORACLE_SID="orcl"
PROFILE_PATH="/home/oracle/.db_profile_orcl"

echo "Configurando Profile para $ORACLE_SID em $PROFILE_PATH..."

cat > $PROFILE_PATH <<EOF
# Profile Oracle - Padrão Getnet/Oraex
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=$ORACLE_HOME
export ORACLE_SID=$ORACLE_SID
export PATH=\$ORACLE_HOME/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin
export LD_LIBRARY_PATH=\$ORACLE_HOME/lib:/lib:/usr/lib
export CLASSPATH=\$ORACLE_HOME/jlib:\$ORACLE_HOME/rdbms/jlib
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8

alias sql='sqlplus / as sysdba'
alias dbs='cd \$ORACLE_HOME/dbs'
alias oh='cd \$ORACLE_HOME'
alias tns='cd \$ORACLE_HOME/network/admin'

echo "Oracle Environment set to: \$ORACLE_SID"
EOF

chown oracle:oinstall $PROFILE_PATH
chmod 755 $PROFILE_PATH

# Adicionar chamada no .bash_profile
if ! grep -q ".db_profile_orcl" /home/oracle/.bash_profile; then
    echo ". $PROFILE_PATH" >> /home/oracle/.bash_profile
    echo "Atualizado .bash_profile do usuário oracle."
fi

echo "Profile configurado com sucesso!"
