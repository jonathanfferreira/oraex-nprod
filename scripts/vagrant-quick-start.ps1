# ==============================================================================
# Script: Quick Start Vagrant
# ==============================================================================
# Verifica instalação e inicia VMs Oracle RAC
# ==============================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VAGRANT QUICK START - ORAEX" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Vagrant
Write-Host "[1/4] Verificando Vagrant..." -ForegroundColor Yellow
try {
    $vagrantVersion = vagrant --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Vagrant encontrado: $vagrantVersion" -ForegroundColor Green
    } else {
        Write-Host "[ERRO] Vagrant nao encontrado!" -ForegroundColor Red
        Write-Host "       Instale: https://www.vagrantup.com/downloads" -ForegroundColor Yellow
        pause
        exit 1
    }
} catch {
    Write-Host "[ERRO] Vagrant nao encontrado!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# 2. Verificar VirtualBox (opcional - Vagrant encontra automaticamente)
Write-Host "[2/4] Verificando VirtualBox..." -ForegroundColor Yellow
try {
    $vboxVersion = vboxmanage --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] VirtualBox encontrado: $vboxVersion" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] VirtualBox nao esta no PATH" -ForegroundColor Yellow
        Write-Host "        Mas Vagrant vai encontra-lo automaticamente se estiver instalado" -ForegroundColor Gray
    }
} catch {
    Write-Host "[AVISO] VirtualBox nao esta no PATH" -ForegroundColor Yellow
    Write-Host "        Mas Vagrant vai encontra-lo automaticamente se estiver instalado" -ForegroundColor Gray
}
Write-Host ""

# 3. Verificar Vagrantfile
Write-Host "[3/4] Verificando Vagrantfile..." -ForegroundColor Yellow
if (Test-Path "Vagrantfile") {
    Write-Host "[OK] Vagrantfile encontrado" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Vagrantfile nao encontrado!" -ForegroundColor Red
    Write-Host "       Execute este script do diretorio raiz do projeto" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

# 4. Perguntar o que fazer
Write-Host "[4/4] O que deseja fazer?" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Iniciar VMs Oracle RAC (oracle-rac-node1 e oracle-rac-node2)" -ForegroundColor Cyan
Write-Host "2. Iniciar todas as VMs" -ForegroundColor Cyan
Write-Host "3. Ver status das VMs" -ForegroundColor Cyan
Write-Host "4. Acessar oracle-rac-node1 via SSH" -ForegroundColor Cyan
Write-Host "5. Parar todas as VMs" -ForegroundColor Cyan
Write-Host "6. Destruir todas as VMs (deletar)" -ForegroundColor Red
Write-Host "0. Sair" -ForegroundColor Gray
Write-Host ""

$opcao = Read-Host "Escolha uma opcao (0-6)"

switch ($opcao) {
    "1" {
        Write-Host ""
        Write-Host "Iniciando VMs Oracle RAC..." -ForegroundColor Yellow
        Write-Host "Isso pode levar 15-20 minutos na primeira vez..." -ForegroundColor Gray
        Write-Host ""
        vagrant up oracle-rac-node1 oracle-rac-node2
    }
    "2" {
        Write-Host ""
        Write-Host "Iniciando todas as VMs..." -ForegroundColor Yellow
        Write-Host "Isso pode levar 20-30 minutos na primeira vez..." -ForegroundColor Gray
        Write-Host ""
        vagrant up
    }
    "3" {
        Write-Host ""
        vagrant status
    }
    "4" {
        Write-Host ""
        Write-Host "Acessando oracle-rac-node1..." -ForegroundColor Yellow
        Write-Host "Digite 'exit' para sair da VM" -ForegroundColor Gray
        Write-Host ""
        vagrant ssh oracle-rac-node1
    }
    "5" {
        Write-Host ""
        Write-Host "Parando todas as VMs..." -ForegroundColor Yellow
        vagrant halt
    }
    "6" {
        Write-Host ""
        Write-Host "[ATENCAO] Isso vai DELETAR todas as VMs!" -ForegroundColor Red
        $confirm = Read-Host "Tem certeza? (sim/nao)"
        if ($confirm -eq "sim") {
            vagrant destroy -f
        } else {
            Write-Host "Cancelado." -ForegroundColor Yellow
        }
    }
    "0" {
        Write-Host "Saindo..." -ForegroundColor Gray
        exit 0
    }
    default {
        Write-Host "Opcao invalida!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Para mais informacoes, consulte: GUIA_VAGRANT_PASSO_A_PASSO.md" -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

pause
