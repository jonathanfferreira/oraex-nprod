#!/bin/bash
# =============================================================================
# Script: deploy_oracle_software.sh
# Descrição: Instala o binário do Oracle Database 19c (Silent Mode)
# Autor: Antigravity/Oraex
# =============================================================================

set -e

LOG_FILE="/home/vagrant/deploy_software.log"
ORACLE_HOME="/u01/app/oracle/product/19.0.0/dbhome_1"
ZIP_FILE="/vagrant/installers/LINUX.X64_193000_db_home.zip"
RSP_FILE="/vagrant/scripts/db_install.rsp"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "Iniciando instalação do Oracle Database 19c..."

# 1. Validações
if [ ! -f "$ZIP_FILE" ]; then
    log "ERRO: Arquivo $ZIP_FILE não encontrado!"
    log "Por favor, baixe o Oracle 19c (Linux x64) e coloque na pasta do projeto."
    exit 1
fi

if [ ! -f "$RSP_FILE" ]; then
    log "ERRO: Arquivo de resposta $RSP_FILE não encontrado."
    exit 1
fi

# 2. Preparação (Executar como user oracle)
log "2. Descompactando binários no ORACLE_HOME..."
if [ -d "$ORACLE_HOME" ]; then
    # Verifica se já está instalado
    if [ -f "$ORACLE_HOME/bin/sqlplus" ]; then
        log "Oracle Home parece já estar instalado. Pulando descompactação."
    else
        log "Diretório existe mas parece vazio/incompleto. Limpando..."
        sudo rm -rf $ORACLE_HOME/*
        sudo -u oracle unzip -qo $ZIP_FILE -d $ORACLE_HOME
    fi
else
    log "Criando diretório $ORACLE_HOME..."
    sudo mkdir -p $ORACLE_HOME
    sudo chown -R oracle:oinstall /u01
    sudo -u oracle unzip -qo $ZIP_FILE -d $ORACLE_HOME
fi

# 3. Instalação
log "3. Executando runInstaller (Silent Mode)..."
# Ajuste de permissão para o inventário
sudo mkdir -p /u01/app/oraInventory
sudo chown oracle:oinstall /u01/app/oraInventory

sudo -u oracle bash -c "export ORACLE_HOME=$ORACLE_HOME; \
    export CV_ASSUME_DISTID=OEL7.6; \
    $ORACLE_HOME/runInstaller -silent \
    -responseFile $RSP_FILE \
    -ignorePrereq \
    -waitForCompletion"

# 4. Root Scripts
log "4. Executando scripts de root..."
if [ -f /u01/app/oraInventory/orainstRoot.sh ]; then
    sudo /u01/app/oraInventory/orainstRoot.sh
fi
if [ -f $ORACLE_HOME/root.sh ]; then
    sudo $ORACLE_HOME/root.sh
fi

# 5. [RECOVERY PLAN] Verificação e Auto-Repair
log "5. Verificando integridade do binário oracle..."
ORACLE_BIN="$ORACLE_HOME/bin/oracle"

if [ -f "$ORACLE_BIN" ]; then
    BIN_SIZE=$(stat -c%s "$ORACLE_BIN")
    # Se menor que 10MB (geralmente é > 400MB)
    if [ "$BIN_SIZE" -lt 10000000 ]; then
        log "⚠️ ALERTA: Binário oracle corrompido ou incompleto (Size: $BIN_SIZE bytes)."
        log "Tentando Auto-Repair (Relink All)..."
        
        # Tenta relink
        sudo -u oracle bash -c "export ORACLE_HOME=$ORACLE_HOME; \
            export PATH=\$ORACLE_HOME/bin:\$PATH; \
            $ORACLE_HOME/bin/relink all"
        
        # Validar de novo
        BIN_SIZE_NEW=$(stat -c%s "$ORACLE_BIN")
        log "Novo tamanho após relink: $BIN_SIZE_NEW bytes"
        
        if [ "$BIN_SIZE_NEW" -lt 10000000 ]; then
            log "❌ ERRO CRÍTICO: Falha no Auto-Repair. O binário continua inválido."
            log "Verifique os logs de install em $ORACLE_HOME/install/."
            exit 1
        fi
    else
        log "✅ Integridade OK (Size: $BIN_SIZE bytes)."
    fi
else
    log "❌ ERRO: Binário $ORACLE_BIN não encontrado!"
    exit 1
fi

log "✅ Instalação do Software Concluída!"
