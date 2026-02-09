#!/bin/bash
# ==============================================================================
# Script: deploy_rac_prerequisites.sh
# Description: Configura pré-requisitos para Oracle RAC 19c em RHEL/CentOS 8
# Author: ORAEX Automation
# ==============================================================================

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Iniciando configuração de pré-requisitos Oracle RAC..."

# 1. Configurar Repositórios
log "1. Configurando repositórios (Nativo Oracle Linux)..."
# Em Oracle Linux, os repositórios já vêm configurados. 
# Apenas garantimos que o Add-ons (para dependências extras) esteja habilitado se existir.
dnf config-manager --set-enabled ol8_addons || true

log "Repositórios prontos."

# 2. Instalar Pacote de Pré-instalação Oracle 19c
log "2. Instalando oracle-database-preinstall-19c..."
dnf install -y oracle-database-preinstall-19c

# 3. Instalar Pacotes Adicionais
log "3. Instalando pacotes adicionais..."
dnf install -y xorg-x11-xauth xterm ksh libaio-devel policycoreutils-python-utils smartmontools
# [RECOVERY PLAN] Build Tools obrigatórios para relink do Oracle no RHEL 8
dnf install -y make binutils gcc glibc-devel libnsl

# 4. Criar Grupos Oracle (se não existirem)
log "4. Criando grupos..."
groupadd -g 54321 oinstall || true
groupadd -g 54322 dba || true
groupadd -g 54323 oper || true
groupadd -g 54324 backupdba || true
groupadd -g 54325 dgdba || true
groupadd -g 54326 kmdba || true
groupadd -g 54327 asmdba || true
groupadd -g 54328 asmoper || true
groupadd -g 54329 asmadmin || true
groupadd -g 54330 racdba || true

# 5. Criar Usuários (Grid e Oracle)
log "5. Criando usuários..."

# Usuário Oracle (RDBMS)
id oracle >/dev/null 2>&1 || useradd -u 54321 -g oinstall -G dba,oper,backupdba,dgdba,kmdba,racdba,asmdba oracle
# Definir senha padrão (oracle)
echo "oracle:oracle" | chpasswd

# Usuário Grid (Infrastructure)
id grid >/dev/null 2>&1 || useradd -u 54322 -g oinstall -G asmadmin,asmdba,asmoper,dba grid
# Definir senha padrão (oracle)
echo "grid:oracle" | chpasswd

# 6. Criar Diretórios
log "6. Criando diretórios..."
mkdir -p /u01
mkdir -p /u02
mkdir -p /u01/app/grid
mkdir -p /u01/app/oracle
chown -R grid:oinstall /u01
chown -R oracle:oinstall /u01/app/oracle
chown -R grid:oinstall /u02
chmod -R 775 /u01
chmod -R 775 /u02

# 7. Desabilitar Firewall
log "7. Desabilitando Firewalld..."
systemctl stop firewalld
systemctl disable firewalld

# 8. Configurar SELinux para Permissive
log "8. Configurando SELinux para Permissive..."
setenforce 0 || true
sed -i 's/^SELINUX=.*/SELINUX=permissive/g' /etc/selinux/config

log "✅ Configuração concluída com sucesso!"
