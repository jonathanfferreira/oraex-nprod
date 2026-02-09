# ==============================================================================
# Script: Configurar Vagrant e VirtualBox para Disco D
# ==============================================================================
# Configura tudo para usar disco D ao invés de C
# ==============================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CONFIGURANDO VAGRANT E VIRTUALBOX PARA DISCO D" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está executando como Administrador (não necessário, mas ajuda)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "[OK] Executando como Administrador" -ForegroundColor Green
} else {
    Write-Host "[INFO] Executando como usuario normal (OK para configuracao)" -ForegroundColor Yellow
}
Write-Host ""

# 1. Verificar se disco D existe
Write-Host "[1/4] Verificando disco D..." -ForegroundColor Yellow
if (Test-Path "D:\") {
    Write-Host "[OK] Disco D encontrado" -ForegroundColor Green
    
    # Verificar espaço disponível
    $drive = Get-PSDrive D
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    Write-Host "      Espaco livre: $freeSpaceGB GB" -ForegroundColor Gray
    
    if ($freeSpaceGB -lt 20) {
        Write-Host "[AVISO] Pouco espaco no disco D! Recomendado pelo menos 20GB" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERRO] Disco D nao encontrado!" -ForegroundColor Red
    Write-Host "       Este script requer disco D disponivel" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

# 2. Criar diretórios necessários
Write-Host "[2/4] Criando diretorios no disco D..." -ForegroundColor Yellow
$directories = @(
    "D:\vagrant",
    "D:\vagrant\boxes",
    "D:\vagrant\data",
    "D:\VirtualBox VMs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   [OK] Criado: $dir" -ForegroundColor Green
    } else {
        Write-Host "   [OK] Ja existe: $dir" -ForegroundColor Gray
    }
}
Write-Host ""

# 3. Configurar Variável de Ambiente VAGRANT_HOME
Write-Host "[3/4] Configurando VAGRANT_HOME..." -ForegroundColor Yellow
try {
    [System.Environment]::SetEnvironmentVariable("VAGRANT_HOME", "D:\vagrant", "User")
    $env:VAGRANT_HOME = "D:\vagrant"
    Write-Host "[OK] VAGRANT_HOME configurado: D:\vagrant" -ForegroundColor Green
    Write-Host "     (Reinicie PowerShell para aplicar permanentemente)" -ForegroundColor Gray
} catch {
    Write-Host "[ERRO] Falha ao configurar VAGRANT_HOME: $_" -ForegroundColor Red
}
Write-Host ""

# 4. Configurar VirtualBox
Write-Host "[4/4] Configurando VirtualBox..." -ForegroundColor Yellow
try {
    # Verificar se VBoxManage está disponível
    $vboxPath = Get-Command VBoxManage -ErrorAction SilentlyContinue
    if ($vboxPath) {
        # Definir diretório padrão de VMs
        $result = & VBoxManage setproperty machinefolder "D:\VirtualBox VMs" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] VirtualBox configurado: D:\VirtualBox VMs" -ForegroundColor Green
        } else {
            Write-Host "[AVISO] Nao foi possivel configurar via linha de comando" -ForegroundColor Yellow
            Write-Host "        Configure manualmente:" -ForegroundColor Yellow
            Write-Host "        1. Abra VirtualBox" -ForegroundColor Cyan
            Write-Host "        2. Arquivo -> Preferencias -> Geral" -ForegroundColor Cyan
            Write-Host "        3. Altere 'Pasta de Maquinas Padrao' para: D:\VirtualBox VMs" -ForegroundColor Cyan
        }
    } else {
        Write-Host "[AVISO] VBoxManage nao encontrado no PATH" -ForegroundColor Yellow
        Write-Host "        Configure manualmente no VirtualBox:" -ForegroundColor Yellow
        Write-Host "        1. Abra VirtualBox" -ForegroundColor Cyan
        Write-Host "        2. Arquivo -> Preferencias -> Geral" -ForegroundColor Cyan
        Write-Host "        3. Altere 'Pasta de Maquinas Padrao' para: D:\VirtualBox VMs" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[AVISO] Erro ao configurar VirtualBox: $_" -ForegroundColor Yellow
    Write-Host "        Configure manualmente no VirtualBox" -ForegroundColor Yellow
}
Write-Host ""

# Resumo
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "RESUMO DA CONFIGURACAO" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Vagrant:" -ForegroundColor Yellow
Write-Host "  VAGRANT_HOME: $env:VAGRANT_HOME" -ForegroundColor Gray
Write-Host "  Boxes: D:\vagrant\boxes" -ForegroundColor Gray
Write-Host "  Data: D:\vagrant\data" -ForegroundColor Gray
Write-Host ""

Write-Host "VirtualBox:" -ForegroundColor Yellow
Write-Host "  VMs: D:\VirtualBox VMs" -ForegroundColor Gray
Write-Host ""

Write-Host "[IMPORTANTE]" -ForegroundColor Yellow
Write-Host "1. REINICIE O POWERSHELL para aplicar VAGRANT_HOME permanentemente" -ForegroundColor Cyan
Write-Host "2. Configure VirtualBox manualmente se necessario" -ForegroundColor Cyan
Write-Host "3. Apos configurar, execute: vagrant up" -ForegroundColor Cyan
Write-Host ""

Write-Host "Para verificar:" -ForegroundColor Yellow
Write-Host "  vagrant box list" -ForegroundColor Cyan
Write-Host "  (Boxes serao salvos em D:\vagrant\boxes)" -ForegroundColor Gray
Write-Host ""

pause
