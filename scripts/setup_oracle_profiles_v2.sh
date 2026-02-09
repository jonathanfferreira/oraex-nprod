#!/bin/bash
# =============================================================================
# Script: setup_oracle_profiles_v2.sh
# Descrição: Configura os profiles .bash_profile e .db_profile_orcl (Padrão Getnet)
# =============================================================================

ORACLE_HOME_VAL="/u01/app/oracle/product/19.0.0/dbhome_1"
ORACLE_SID_VAL="orcl"
PROFILE_PATH="/home/oracle/.db_profile_orcl"

echo "Configurando Profile para $ORACLE_SID_VAL em $PROFILE_PATH..."

# Usando <<'EOF' para evitar expansão de variáveis no corpo do arquivo
cat > $PROFILE_PATH <<'EOF'
# Profile Oracle - Padrão Getnet/Oraex
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_1
export ORACLE_SID=orcl
export PATH=$ORACLE_HOME/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export CLASSPATH=$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8

alias sql='sqlplus / as sysdba'
alias dbs='cd $ORACLE_HOME/dbs'
alias oh='cd $ORACLE_HOME'
alias tns='cd $ORACLE_HOME/network/admin'

echo "Oracle Environment set to: $ORACLE_SID"
EOF

chown oracle:oinstall $PROFILE_PATH
chmod 755 $PROFILE_PATH

# Adicionar chamada no .bash_profile se não existir
BASH_PROFILE="/home/oracle/.bash_profile"
if [ -f "$BASH_PROFILE" ]; then
    if ! grep -q ".db_profile_orcl" "$BASH_PROFILE"; then
        echo "" >> "$BASH_PROFILE"
        echo ". /home/oracle/.db_profile_orcl" >> "$BASH_PROFILE"
        echo "Atualizado .bash_profile do usuário oracle."
    fi
else
    # Se não existir, criar um simples
    cat > "$BASH_PROFILE" <<'EOF'
# .bash_profile
[ -f ~/.bashrc ] && . ~/.bashrc
. /home/oracle/.db_profile_orcl
EOF
    chown oracle:oinstall "$BASH_PROFILE"
    chmod 755 "$BASH_PROFILE"
fi

echo "Profile configurado com sucesso!"
ls -la /home/oracle/.db_profile_orcl /home/oracle/.bash_profile
