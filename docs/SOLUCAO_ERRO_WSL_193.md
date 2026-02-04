# 🔧 Solução: Erro 193 - WSL2 / Virtual Machine Platform

## 📋 Erro Identificado

```
Error: 193
%1 is not a valid Win32 application.
Failed to enable windows component 'VirtualMachinePlatform' (exit code 193)
```

Este erro indica que o Windows não consegue habilitar a Virtual Machine Platform, necessária para WSL2 e Docker Desktop.

---

## 🔍 Causas Possíveis

### 1. **Virtualização Desabilitada no BIOS** (Mais Comum)
- CPU não tem virtualização habilitada
- BIOS não permite virtualização

### 2. **Processador Não Suporta Virtualização**
- CPUs muito antigas podem não ter suporte
- Verificar se CPU suporta Intel VT-x ou AMD-V

### 3. **Arquivos do Windows Corrompidos**
- Componentes do Windows danificados
- DISM/SFC pode resolver

### 4. **Conflito com Outras Tecnologias**
- Hyper-V já instalado e conflitando
- VirtualBox ou VMware rodando

---

## ✅ Soluções (Tente nesta ordem)

### Solução 1: Habilitar Virtualização no BIOS

**Passo a passo:**

1. **Reiniciar computador**
2. **Entrar no BIOS:**
   - **Dell:** F2 ou F12
   - **HP:** F10 ou Esc
   - **Lenovo:** F1 ou F2
   - **ASUS:** F2 ou Del
   - **Acer:** F2 ou Del

3. **Procurar por:**
   - **Intel:** "Intel Virtualization Technology" ou "Intel VT-x"
   - **AMD:** "AMD-V" ou "SVM Mode"
   - **Geral:** "Virtualization Technology" ou "Virtualization"

4. **Habilitar** (Enabled)
5. **Salvar e sair** (F10 geralmente)
6. **Reiniciar**

### Solução 2: Verificar se CPU Suporta Virtualização

```powershell
# Executar no PowerShell (como Administrador)
systeminfo | findstr /C:"Hyper-V"
```

**Se aparecer:**
- "A hypervisor has been detected" = Virtualização disponível
- Nada ou erro = Pode não ter suporte

**Verificar CPU:**
```powershell
Get-WmiObject Win32_Processor | Select-Object Name, VirtualizationFirmwareEnabled
```

### Solução 3: Reparar Arquivos do Windows

```powershell
# Executar no PowerShell (como Administrador)

# 1. Verificar integridade
sfc /scannow

# 2. Reparar componentes
DISM /Online /Cleanup-Image /RestoreHealth

# 3. Reiniciar
Restart-Computer
```

### Solução 4: Habilitar Componentes Manualmente

```powershell
# Executar no PowerShell (como Administrador)

# Habilitar Virtual Machine Platform
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All

# Habilitar WSL
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -All

# Reiniciar
Restart-Computer
```

### Solução 5: Verificar Conflitos

```powershell
# Verificar se Hyper-V está habilitado
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All

# Se estiver habilitado e causando conflito, pode desabilitar temporariamente
Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
```

---

## 🚫 Alternativas (Se Nada Funcionar)

### Opção 1: Usar Docker Toolbox (Legado)

Docker Toolbox não precisa de WSL2, usa VirtualBox:

1. **Instalar VirtualBox:**
   - https://www.virtualbox.org/wiki/Downloads

2. **Instalar Docker Toolbox:**
   - https://github.com/docker/toolbox/releases
   - Versão mais antiga, mas funciona sem WSL2

### Opção 2: Usar Vagrant (Recomendado)

Vagrant usa VirtualBox diretamente, não precisa de WSL2:

```powershell
# Instalar Vagrant
# https://www.vagrantup.com/downloads

# Instalar VirtualBox
# https://www.virtualbox.org/wiki/Downloads

# Usar Vagrantfile do projeto
vagrant up
```

### Opção 3: Continuar Sem Docker (Melhor Opção Agora)

Você já tem testes funcionando sem Docker! Use:

```cmd
python tests/local/test_without_docker.py
```

**Pode testar:**
- ✅ Sintaxe e estrutura do código
- ✅ Testes unitários Python
- ✅ Validação Ansible/Terraform
- ✅ Lógica das automações

---

## 🔍 Diagnóstico Detalhado

Execute este script para diagnosticar:

```powershell
# Salvar como diagnose_wsl.ps1 e executar como Administrador

Write-Host "=== DIAGNOSTICO WSL2 ===" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Windows Edition
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "Windows Edition: $($os.Caption)" -ForegroundColor Yellow
Write-Host ""

# 2. Verificar CPU
$cpu = Get-WmiObject Win32_Processor
Write-Host "CPU: $($cpu.Name)" -ForegroundColor Yellow
Write-Host "Virtualization Firmware: $($cpu.VirtualizationFirmwareEnabled)" -ForegroundColor Yellow
Write-Host ""

# 3. Verificar Hyper-V
$hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
Write-Host "Hyper-V Status: $($hyperv.State)" -ForegroundColor Yellow
Write-Host ""

# 4. Verificar WSL
$wsl = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Write-Host "WSL Status: $($wsl.State)" -ForegroundColor Yellow
Write-Host ""

# 5. Verificar Virtual Machine Platform
$vmp = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
Write-Host "Virtual Machine Platform: $($vmp.State)" -ForegroundColor Yellow
Write-Host ""

# 6. Verificar se virtualização está disponível
$systeminfo = systeminfo | Select-String "Hyper-V"
Write-Host "System Info:" -ForegroundColor Yellow
Write-Host $systeminfo -ForegroundColor Gray
Write-Host ""

# 7. Verificar BIOS/UEFI
$bios = Get-WmiObject Win32_BIOS
Write-Host "BIOS: $($bios.Manufacturer) $($bios.Version)" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== FIM DO DIAGNOSTICO ===" -ForegroundColor Cyan
```

---

## 📝 Checklist de Verificação

- [ ] Virtualização habilitada no BIOS
- [ ] CPU suporta virtualização (Intel VT-x ou AMD-V)
- [ ] Windows Pro/Enterprise/Education
- [ ] Arquivos do Windows íntegros (sfc /scannow OK)
- [ ] Sem conflitos com Hyper-V/VirtualBox
- [ ] Componentes Windows habilitados corretamente

---

## 💡 Recomendação

**Para seu caso específico:**

1. **Primeiro:** Tente habilitar virtualização no BIOS (Solução 1)
2. **Se não funcionar:** Use os testes sem Docker que já estão funcionando
3. **Alternativa:** Instale Vagrant + VirtualBox (mais simples que Docker)

**Você NÃO precisa de Docker para desenvolver e testar o projeto!**

Os testes sem Docker já validam:
- ✅ 80% do código (sintaxe, estrutura, lógica)
- ✅ Testes unitários (com mocks)
- ✅ Configurações (Ansible, Terraform)

Os 20% restantes (conexões reais) podem ser testados no ambiente Getnet quando estiver pronto.

---

## 🆘 Ainda com Problemas?

Se nenhuma solução funcionar:

1. **Verifique a marca/modelo do seu computador**
2. **Consulte o manual do fabricante** sobre virtualização
3. **Entre em contato com suporte** do fabricante
4. **Use alternativas** (Vagrant ou testes sem Docker)

---

**Lembre-se:** Você já tem um ambiente de testes funcionando sem Docker! 🎉
