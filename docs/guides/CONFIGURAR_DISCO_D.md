# 💾 Configurar Tudo no Disco D

**Importante:** Configurar Vagrant e VirtualBox para usar disco D ao invés de C.

---

## 🎯 Passo 1: Configurar Vagrant (Boxes e Dados)

### Opção A: Variável de Ambiente (Recomendado)

```powershell
# Definir variável de ambiente permanentemente
[System.Environment]::SetEnvironmentVariable("VAGRANT_HOME", "D:\vagrant", "User")

# Verificar
echo $env:VAGRANT_HOME
```

**Reiniciar PowerShell** para aplicar.

### Opção B: Configurar no Vagrantfile

O Vagrantfile já está configurado para usar disco D (ver abaixo).

---

## 🎯 Passo 2: Configurar VirtualBox (VMs)

### 1. Abrir VirtualBox

### 2. Ir em: **Arquivo → Preferências → Geral**

### 3. Alterar "Pasta de Máquinas Padrão":
- **De:** `C:\Users\SeuUsuario\VirtualBox VMs`
- **Para:** `D:\VirtualBox VMs`

### 4. Salvar

**OU via linha de comando:**

```powershell
# Definir diretório padrão do VirtualBox
VBoxManage setproperty machinefolder "D:\VirtualBox VMs"
```

---

## 🎯 Passo 3: Verificar Configuração

```powershell
# Verificar Vagrant
echo $env:VAGRANT_HOME

# Verificar VirtualBox
VBoxManage list systemproperties | findstr "Default"
```

---

## ✅ Pronto!

Agora quando executar `vagrant up`, tudo será criado no disco D:
- ✅ Boxes: `D:\vagrant\boxes`
- ✅ VMs: `D:\VirtualBox VMs`
- ✅ Dados: `D:\vagrant\data`

---

## 📝 Nota

Se já tiver VMs criadas no disco C, você pode:
1. Mover manualmente para D
2. Ou destruir e recriar (mais simples)

```powershell
# Destruir VMs antigas (se houver)
vagrant destroy -f

# Recriar no disco D
vagrant up
```
