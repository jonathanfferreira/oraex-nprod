# ⚡ Início Rápido - Vagrant

**Tudo pronto? Vamos começar em 3 passos!**

---

## 🚀 Passo 1: Iniciar VMs

Execute este comando:

```powershell
vagrant up oracle-rac-node1 oracle-rac-node2
```

**O que acontece:**
- ⏱️ Primeira vez: 15-20 minutos (baixa imagens)
- ⏱️ Próximas vezes: 2-3 minutos

**Você verá:**
```
Bringing machine 'oracle-rac-node1' up with 'virtualbox' provider...
==> oracle-rac-node1: Importing base box 'generic/rhel8'...
...
==> oracle-rac-node1: Machine booted and ready!
```

**Aguarde até ver "Machine booted and ready!"**

---

## 🚀 Passo 2: Acessar VM

```powershell
vagrant ssh oracle-rac-node1
```

**Login automático!** Não precisa de senha. O Vagrant usa chave SSH.

**Credenciais (se precisar acessar manualmente):**
- **Usuário:** `vagrant`
- **Senha:** `vagrant` (padrão)
- **IP:** 192.168.56.11

**Pronto! Você está dentro da VM!** 🎉

---

## 🚀 Passo 3: Verificar

Dentro da VM, execute:

```bash
# Verificar sistema
cat /etc/os-release

# Verificar usuário oracle
id oracle

# Verificar diretórios
ls -la /u01/app/oracle

# Sair
exit
```

---

## 📋 Comandos Essenciais

```powershell
# Ver status
vagrant status

# Acessar VM
vagrant ssh oracle-rac-node1

# Parar VMs (mas manter)
vagrant halt

# Reiniciar
vagrant reload

# Deletar tudo
vagrant destroy
```

---

## 🎯 Próximos Passos

1. **Testar automações Python** dentro da VM
2. **Instalar Oracle** (quando estiver pronto)
3. **Configurar RAC** (se necessário)

---

## 🆘 Problemas?

### VM não inicia
```powershell
vagrant up --debug oracle-rac-node1
```

### Box não encontrado
```powershell
vagrant box add generic/rhel8
```

### Ver logs
```powershell
vagrant up --debug
```

---

## 💡 Dica

**Código do projeto está em `/vagrant` dentro da VM!**

```bash
# Dentro da VM
cd /vagrant
ls -la
```

---

**Pronto? Execute:**

```powershell
vagrant up oracle-rac-node1 oracle-rac-node2
```

**E aguarde!** ⏱️
