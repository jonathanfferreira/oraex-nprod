# ==============================================================================
# Script: Corrigir WSL2 - Executar como Administrador
# ==============================================================================
# Este script deve ser executado como Administrador
# ==============================================================================

# Verificar se está executando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERRO] Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Como executar:" -ForegroundColor Yellow
    Write-Host "1. Clique com botao direito no PowerShell" -ForegroundColor Yellow
    Write-Host "2. Selecione 'Executar como Administrador'" -ForegroundColor Yellow
    Write-Host "3. Execute: .\scripts\fix_wsl_admin.ps1" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CORRIGINDO WSL2 E VIRTUAL MACHINE PLATFORM" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Reparar Windows primeiro
Write-Host "[1/5] Verificando integridade do Windows..." -ForegroundColor Yellow
Write-Host "      Isso pode levar alguns minutos..." -ForegroundColor Gray
sfc /scannow
Write-Host ""

Write-Host "[2/5] Reparando componentes do Windows..." -ForegroundColor Yellow
DISM /Online /Cleanup-Image /RestoreHealth
Write-Host ""

# 2. Habilitar WSL
Write-Host "[3/5] Habilitando WSL..." -ForegroundColor Yellow
try {
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -All -NoRestart
    Write-Host "[OK] WSL habilitado" -ForegroundColor Green
} catch {
    Write-Host "[AVISO] Erro ao habilitar WSL: $_" -ForegroundColor Yellow
}
Write-Host ""

# 3. Habilitar Virtual Machine Platform
Write-Host "[4/5] Habilitando Virtual Machine Platform..." -ForegroundColor Yellow
Write-Host "      Este e o passo que estava falhando..." -ForegroundColor Gray
try {
    Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart
    Write-Host "[OK] Virtual Machine Platform habilitado!" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Falha ao habilitar Virtual Machine Platform" -ForegroundColor Red
    Write-Host "       Erro: $_" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Possiveis causas:" -ForegroundColor Yellow
    Write-Host "1. Virtualizacao nao habilitada no BIOS" -ForegroundColor Yellow
    Write-Host "2. Conflito com Hyper-V ou outras tecnologias" -ForegroundColor Yellow
    Write-Host "3. Arquivos do Windows corrompidos" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tente:" -ForegroundColor Yellow
    Write-Host "1. Reiniciar e verificar BIOS (habilitar AMD-V)" -ForegroundColor Cyan
    Write-Host "2. Desabilitar Hyper-V temporariamente" -ForegroundColor Cyan
    Write-Host "3. Usar alternativas (Vagrant ou testes sem Docker)" -ForegroundColor Cyan
}
Write-Host ""

# 4. Definir WSL2 como padrão
Write-Host "[5/5] Configurando WSL2 como padrao..." -ForegroundColor Yellow
try {
    wsl --set-default-version 2
    Write-Host "[OK] WSL2 configurado como padrao" -ForegroundColor Green
} catch {
    Write-Host "[AVISO] Nao foi possivel configurar WSL2: $_" -ForegroundColor Yellow
}
Write-Host ""

# Resumo
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "RESUMO" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[IMPORTANTE] REINICIE O COMPUTADOR para aplicar as mudancas!" -ForegroundColor Yellow
Write-Host ""

Write-Host "Apos reiniciar:" -ForegroundColor Yellow
Write-Host "1. Execute: wsl --status" -ForegroundColor Cyan
Write-Host "2. Se estiver OK, instale Docker Desktop" -ForegroundColor Cyan
Write-Host "3. Ou use: python tests/local/test_without_docker.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "Se ainda nao funcionar apos reiniciar:" -ForegroundColor Yellow
Write-Host "- Verifique BIOS (habilitar AMD-V)" -ForegroundColor Cyan
Write-Host "- Use Vagrant como alternativa" -ForegroundColor Cyan
Write-Host "- Continue com testes sem Docker (ja funcionando!)" -ForegroundColor Cyan
Write-Host ""

pause
