#!/bin/bash
# =============================================================================
# Script: create_database.sh
# Descrição: Cria o banco de dados Oracle via DBCA (Silent Mode)
# Autor: Antigravity/Oraex
# =============================================================================

set -e

LOG_FILE="/home/vagrant/create_database.log"
ORACLE_HOME="/u01/app/oracle/product/19.0.0/dbhome_1"
RSP_FILE="/vagrant/scripts/dbca_create.rsp"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "Iniciando criação do Banco de Dados..."

# 1. Validações
if [ ! -f "$RSP_FILE" ]; then
    log "ERRO: Arquivo de resposta $RSP_FILE não encontrado."
    exit 1
fi

# 2. Execução (DBCA)
log "Executando DBCA (Silent Mode)..."
# Usando o template General Purpose padrão do 19c se o customizado não existir
TEMPLATE_NAME="General_Purpose.dbc"

sudo -u oracle bash -c "export ORACLE_HOME=$ORACLE_HOME; \
    export PATH=\$ORACLE_HOME/bin:\$PATH; \
    dbca -silent -createDatabase \
    -responseFile $RSP_FILE"

log "✅ Criação do Banco de Dados Concluída!"
