# 🚀 Comece Aqui - Vagrant

**Vagrant instalado? VirtualBox instalado? Vamos começar!**

---

## ✅ Verificação Rápida

Execute para verificar se está tudo OK:

```powershell
vagrant --version
vagrant status
```

**Se ambos funcionarem, continue!**

---

## 🎯 Início Rápido (3 Comandos)

### 1. Iniciar VMs Oracle RAC

```powershell
vagrant up oracle-rac-node1 oracle-rac-node2
```

**⏱️ Primeira vez:** 15-20 minutos (baixa imagens e cria VMs)  
**⏱️ Próximas vezes:** 2-3 minutos (VMs já criadas)

### 2. Aguardar Conclusão

Você verá mensagens como:
```
==> oracle-rac-node1: Machine booted and ready!
==> oracle-rac-node1: Running provisioner: shell...
```

**Aguarde até ver "Machine booted and ready!"**

### 3. Acessar VM

```powershell
vagrant ssh oracle-rac-node1
```

**Pronto! Você está dentro da VM!** 🎉

---

## 📋 O Que Fazer Dentro da VM

### Verificar Sistema

```bash
# Verificar OS
cat /etc/os-release

# Verificar usuário oracle
id oracle

# Verificar diretórios
ls -la /u01/app/oracle
ls -la /u02/oracle

# Verificar rede
ip addr show
ping -c 3 8.8.8.8
```

### Sair da VM

```bash
exit
```

---

## 🛠️ Comandos Úteis

### Ver Status

```powershell
vagrant status
```

### Parar VMs (mas manter criadas)

```powershell
vagrant halt
```

### Reiniciar VMs

```powershell
vagrant reload
```

### Provisionar Novamente (executar Ansible)

```powershell
vagrant provision oracle-rac-node1
```

### Destruir VMs (deletar tudo)

```powershell
vagrant destroy
```

---

## 🎯 Próximos Passos

### 1. Testar Automações Python

```powershell
# Acessar VM
vagrant ssh oracle-rac-node1

# Dentro da VM, testar scripts
cd /vagrant  # Código do projeto está aqui
python3 automacao/diagnosticos/oracle_healthcheck.py --help
```

### 2. Instalar Oracle (Quando Estiver Pronto)

```bash
# Dentro da VM
sudo yum install oracle-database-preinstall-19c
# ... seguir instalação Oracle ...
```

### 3. Testar Ansible

```powershell
# Do seu PC
cd infra/ansible
ansible-playbook -i inventory/vagrant.ini playbooks/provision-cluster.yml
```

---

## 🆘 Problemas Comuns

### VM não inicia

```powershell
# Ver logs detalhados
vagrant up --debug oracle-rac-node1

# Verificar VirtualBox
# Abrir VirtualBox e ver se VM aparece
```

### Erro: "Box not found"

```powershell
# Adicionar box manualmente
vagrant box add generic/rhel8
```

### Rede não funciona

```powershell
# Verificar configuração
vagrant ssh oracle-rac-node1
ip addr show
```

### VM muito lenta

- Verificar se tem RAM suficiente (cada VM usa 4GB)
- Fechar outros programas
- Reduzir memória no Vagrantfile (se necessário)

---

## 💡 Dicas

1. **Primeira vez é mais lenta** - Vagrant baixa imagens (~1GB)
2. **Use `vagrant halt`** ao invés de `destroy` (mantém VMs)
3. **Código do projeto está em `/vagrant`** dentro da VM
4. **VMs usam ~4GB RAM cada** - verifique se tem RAM suficiente

---

## 🚀 Script Helper

Use o script helper para facilitar:

```powershell
.\scripts\vagrant-quick-start.ps1
```

**Menu interativo com opções:**
- Iniciar VMs
- Ver status
- Acessar VMs
- Parar/destruir VMs

---

## 📝 Checklist

- [ ] Vagrant instalado ✅
- [ ] VirtualBox instalado ✅
- [ ] Executar `vagrant up oracle-rac-node1 oracle-rac-node2`
- [ ] Aguardar criação completa
- [ ] Acessar com `vagrant ssh oracle-rac-node1`
- [ ] Testar sistema dentro da VM
- [ ] Pronto para desenvolver! 🎉

---

**Pronto para começar? Execute:**

```powershell
vagrant up oracle-rac-node1 oracle-rac-node2
```

**E aguarde a criação!** ⏱️
