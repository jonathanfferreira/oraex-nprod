# ==============================================================================
# Script: Diagnóstico WSL2 e Virtualização
# ==============================================================================
# Executa diagnóstico completo para identificar problemas com WSL2/Docker
# ==============================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "DIAGNOSTICO WSL2 E VIRTUALIZACAO" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está executando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[AVISO] Execute como Administrador para resultados completos" -ForegroundColor Yellow
    Write-Host ""
}

# 1. Informações do Windows
Write-Host "=== 1. INFORMACOES DO WINDOWS ===" -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "Edicao: $($os.Caption)" -ForegroundColor Gray
Write-Host "Versao: $($os.Version)" -ForegroundColor Gray
Write-Host "Arquitetura: $($os.OSArchitecture)" -ForegroundColor Gray

# Verificar se é Pro/Enterprise
if ($os.Caption -match "Home") {
    Write-Host "[AVISO] Windows Home pode ter limitacoes com WSL2" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Edicao suporta WSL2" -ForegroundColor Green
}
Write-Host ""

# 2. Informações da CPU
Write-Host "=== 2. INFORMACOES DA CPU ===" -ForegroundColor Yellow
$cpu = Get-WmiObject Win32_Processor
Write-Host "Processador: $($cpu.Name)" -ForegroundColor Gray
Write-Host "Virtualizacao Firmware: $($cpu.VirtualizationFirmwareEnabled)" -ForegroundColor Gray

if ($cpu.VirtualizationFirmwareEnabled) {
    Write-Host "[OK] CPU suporta virtualizacao" -ForegroundColor Green
} else {
    Write-Host "[ERRO] CPU nao tem virtualizacao habilitada no BIOS!" -ForegroundColor Red
    Write-Host "       Habilite Intel VT-x ou AMD-V no BIOS" -ForegroundColor Yellow
}
Write-Host ""

# 3. Verificar Hyper-V
Write-Host "=== 3. HYPER-V ===" -ForegroundColor Yellow
try {
    $hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction SilentlyContinue
    if ($hyperv) {
        Write-Host "Status: $($hyperv.State)" -ForegroundColor Gray
        if ($hyperv.State -eq "Enabled") {
            Write-Host "[OK] Hyper-V habilitado" -ForegroundColor Green
        } else {
            Write-Host "[INFO] Hyper-V nao habilitado (opcional para WSL2)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "[AVISO] Nao foi possivel verificar Hyper-V" -ForegroundColor Yellow
}
Write-Host ""

# 4. Verificar WSL
Write-Host "=== 4. WSL (Windows Subsystem for Linux) ===" -ForegroundColor Yellow
try {
    $wsl = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -ErrorAction SilentlyContinue
    if ($wsl) {
        Write-Host "Status: $($wsl.State)" -ForegroundColor Gray
        if ($wsl.State -eq "Enabled") {
            Write-Host "[OK] WSL habilitado" -ForegroundColor Green
        } else {
            Write-Host "[INFO] WSL nao habilitado" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "[AVISO] Nao foi possivel verificar WSL" -ForegroundColor Yellow
}

# Verificar versão do WSL
try {
    $wslVersion = wsl --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Versao WSL:" -ForegroundColor Gray
        Write-Host $wslVersion -ForegroundColor Gray
    } else {
        Write-Host "[INFO] WSL nao instalado ou com problemas" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[AVISO] Nao foi possivel verificar versao WSL" -ForegroundColor Yellow
}
Write-Host ""

# 5. Verificar Virtual Machine Platform
Write-Host "=== 5. VIRTUAL MACHINE PLATFORM ===" -ForegroundColor Yellow
try {
    $vmp = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -ErrorAction SilentlyContinue
    if ($vmp) {
        Write-Host "Status: $($vmp.State)" -ForegroundColor Gray
        if ($vmp.State -eq "Enabled") {
            Write-Host "[OK] Virtual Machine Platform habilitado" -ForegroundColor Green
        } else {
            Write-Host "[ERRO] Virtual Machine Platform NAO habilitado!" -ForegroundColor Red
            Write-Host "       Este e necessario para WSL2 e Docker Desktop" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[ERRO] Nao foi possivel verificar Virtual Machine Platform" -ForegroundColor Red
    Write-Host "       Erro: $_" -ForegroundColor Yellow
}
Write-Host ""

# 6. Verificar System Info
Write-Host "=== 6. SYSTEM INFO ===" -ForegroundColor Yellow
$systeminfo = systeminfo | Select-String "Hyper-V"
if ($systeminfo) {
    Write-Host $systeminfo -ForegroundColor Gray
    if ($systeminfo -match "A hypervisor has been detected") {
        Write-Host "[OK] Hypervisor detectado" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Nenhuma informacao de hypervisor encontrada" -ForegroundColor Gray
}
Write-Host ""

# 7. Verificar BIOS
Write-Host "=== 7. BIOS ===" -ForegroundColor Yellow
try {
    $bios = Get-WmiObject Win32_BIOS
    Write-Host "Fabricante: $($bios.Manufacturer)" -ForegroundColor Gray
    Write-Host "Versao: $($bios.Version)" -ForegroundColor Gray
    Write-Host "Data: $($bios.ReleaseDate)" -ForegroundColor Gray
} catch {
    Write-Host "[AVISO] Nao foi possivel obter informacoes do BIOS" -ForegroundColor Yellow
}
Write-Host ""

# 8. Verificar Docker (se instalado)
Write-Host "=== 8. DOCKER ===" -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker encontrado: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Docker nao instalado" -ForegroundColor Gray
    }
} catch {
    Write-Host "[INFO] Docker nao encontrado" -ForegroundColor Gray
}
Write-Host ""

# Resumo e Recomendações
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "RESUMO E RECOMENDACOES" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $cpu.VirtualizationFirmwareEnabled) {
    Write-Host "[ACAO NECESSARIA] Habilite virtualizacao no BIOS:" -ForegroundColor Red
    Write-Host "   1. Reinicie o computador" -ForegroundColor Yellow
    Write-Host "   2. Entre no BIOS (F2, F10, Del - depende do fabricante)" -ForegroundColor Yellow
    Write-Host "   3. Procure por 'Intel VT-x' ou 'AMD-V' ou 'Virtualization Technology'" -ForegroundColor Yellow
    Write-Host "   4. Habilite (Enabled)" -ForegroundColor Yellow
    Write-Host "   5. Salve e reinicie" -ForegroundColor Yellow
    Write-Host ""
}

try {
    $vmp = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -ErrorAction SilentlyContinue
    if ($vmp -and $vmp.State -ne "Enabled") {
        Write-Host "[ACAO NECESSARIA] Habilite Virtual Machine Platform:" -ForegroundColor Red
        Write-Host "   Execute como Administrador:" -ForegroundColor Yellow
        Write-Host "   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All" -ForegroundColor Cyan
        Write-Host ""
    }
} catch {
    Write-Host "[AVISO] Nao foi possivel verificar Virtual Machine Platform" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "[ALTERNATIVA] Se Docker nao funcionar, use:" -ForegroundColor Yellow
Write-Host "   - Testes sem Docker: python tests/local/test_without_docker.py" -ForegroundColor Cyan
Write-Host "   - Vagrant: vagrant up (precisa VirtualBox)" -ForegroundColor Cyan
Write-Host ""

Write-Host "Para mais detalhes, consulte: docs/SOLUCAO_ERRO_WSL_193.md" -ForegroundColor Gray
Write-Host ""
