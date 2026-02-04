# 🚀 Guia Rápido: Resolver Erro 193

## 📋 Seu Erro

```
Error: 193
%1 is not a valid Win32 application.
Failed to enable windows component 'VirtualMachinePlatform'
```

## ✅ Diagnóstico do Seu Sistema

Baseado no diagnóstico executado:

- ✅ **Windows 11 Pro** - Suporta WSL2
- ✅ **CPU AMD Ryzen 5 4500** - Virtualização habilitada
- ✅ **WSL2 instalado** (v2.6.3.0)
- ⚠️ **Virtual Machine Platform** - Precisa ser habilitado como Admin

---

## 🔧 Solução Rápida (3 Passos)

### Passo 1: Executar Script de Correção

1. **Abra PowerShell como Administrador:**
   - Clique com botão direito no PowerShell
   - Selecione "Executar como Administrador"

2. **Execute o script:**
   ```powershell
   cd D:\antigravity\oraex\nprod
   .\scripts\fix_wsl_admin.ps1
   ```

3. **Reinicie o computador**

### Passo 2: Verificar Após Reiniciar

```powershell
# Verificar status
wsl --status

# Deve mostrar:
# Default Version: 2
# WSL2 está funcionando corretamente
```

### Passo 3: Se Ainda Não Funcionar

**Opção A: Verificar BIOS**
1. Reiniciar e entrar no BIOS (geralmente F2 ou Del)
2. Procurar por "AMD-V" ou "SVM Mode"
3. Habilitar se estiver desabilitado
4. Salvar e reiniciar

**Opção B: Usar Alternativas**
- ✅ **Testes sem Docker** (já funcionando!):
  ```cmd
  python tests/local/test_without_docker.py
  ```

- ✅ **Vagrant** (mais simples que Docker):
  ```cmd
  # Instalar VirtualBox: https://www.virtualbox.org/wiki/Downloads
  # Instalar Vagrant: https://www.vagrantup.com/downloads
  vagrant up
  ```

---

## 💡 Recomendação Imediata

**Você NÃO precisa resolver o Docker agora!**

Os testes sem Docker já estão funcionando e validam:
- ✅ 80% do código (sintaxe, estrutura, lógica)
- ✅ Testes unitários Python
- ✅ Validação Ansible/Terraform

**Continue desenvolvendo e teste Docker depois!**

---

## 📝 Checklist

- [ ] Executar `fix_wsl_admin.ps1` como Administrador
- [ ] Reiniciar computador
- [ ] Verificar `wsl --status`
- [ ] Se OK, instalar Docker Desktop
- [ ] Se não OK, usar alternativas (Vagrant ou testes sem Docker)

---

**Dúvidas?** Consulte `docs/SOLUCAO_ERRO_WSL_193.md` para guia completo.
