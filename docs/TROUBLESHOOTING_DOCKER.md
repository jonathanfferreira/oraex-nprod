# 🔧 Troubleshooting Docker - Windows

## Problemas Comuns e Soluções

### 1. Erro: "WSL 2 installation is incomplete"

**Causa:** WSL2 não está instalado ou configurado corretamente.

**Solução:**
```powershell
# 1. Verificar se WSL está instalado
wsl --status

# 2. Instalar WSL2
wsl --install

# 3. Definir WSL2 como padrão
wsl --set-default-version 2

# 4. Reiniciar computador
```

### 2. Erro: "Hardware assisted virtualization and data execution protection must be enabled"

**Causa:** Virtualização desabilitada no BIOS.

**Solução:**
1. Reiniciar e entrar no BIOS (F2, F10, Del - depende do fabricante)
2. Habilitar:
   - **Intel VT-x** ou **AMD-V**
   - **Virtualization Technology**
3. Salvar e reiniciar

### 2.1. Erro 193: "%1 is not a valid Win32 application" (WSL2)

**Causa:** Virtual Machine Platform não consegue ser habilitada.

**Soluções:**
1. **Habilitar virtualização no BIOS** (mais comum - ver Solução 1 acima)
2. **Reparar Windows:**
   ```powershell
   sfc /scannow
   DISM /Online /Cleanup-Image /RestoreHealth
   ```
3. **Habilitar manualmente:**
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All
   ```

**Ver:** `docs/SOLUCAO_ERRO_WSL_193.md` para guia completo.

### 3. Erro: "Hyper-V is not available"

**Causa:** Hyper-V não está habilitado ou conflitando.

**Solução:**
```powershell
# Verificar se Hyper-V está habilitado
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All

# Habilitar Hyper-V (se necessário)
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All

# Reiniciar
```

### 4. Erro: "Docker Desktop requires Windows 10/11 Pro or Enterprise"

**Causa:** Versão do Windows incompatível.

**Solução:**
- Docker Desktop requer Windows 10/11 **Pro, Enterprise ou Education**
- Windows Home não suporta Hyper-V nativamente
- **Alternativa:** Usar Docker Toolbox (mais antigo) ou WSL2

### 5. Erro: "Access Denied" ou problemas de permissão

**Causa:** Permissões insuficientes.

**Solução:**
```powershell
# Executar PowerShell como Administrador
# Adicionar usuário ao grupo Docker (se aplicável)
net localgroup docker-users "seu_usuario" /add
```

### 6. Antivírus bloqueando

**Causa:** Antivírus bloqueando virtualização.

**Solução:**
- Adicionar Docker à lista de exceções do antivírus
- Desabilitar temporariamente para testar

---

## ✅ Verificação Rápida

Execute este script para diagnosticar:

```powershell
# Verificar WSL
Write-Host "WSL Status:"
wsl --status

# Verificar virtualização
Write-Host "`nVirtualization:"
Get-ComputerInfo | Select-Object -Property HyperV*

# Verificar Windows Edition
Write-Host "`nWindows Edition:"
(Get-CimInstance Win32_OperatingSystem).Caption

# Verificar se Docker está instalado
Write-Host "`nDocker:"
docker --version 2>&1
```

---

## 🚫 Alternativas (Se Docker Não Funcionar)

### Opção 1: Usar Vagrant (Recomendado)
- Não precisa de Docker
- Cria VMs completas
- Mais pesado, mas mais realista

### Opção 2: Testes Sem Containers
- Testes de sintaxe (Ansible, Terraform)
- Testes unitários Python (com mocks)
- Validação de código

### Opção 3: Docker Toolbox (Legado)
- Funciona em Windows Home
- Usa VirtualBox ao invés de Hyper-V
- Versão mais antiga do Docker

---

## 📞 Próximos Passos

1. **Execute o script de verificação acima**
2. **Identifique o erro específico**
3. **Siga a solução correspondente**
4. **Se não funcionar, use as alternativas sem Docker**
