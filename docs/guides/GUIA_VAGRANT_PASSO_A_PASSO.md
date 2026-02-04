# 🚀 Guia Vagrant - Passo a Passo

## ✅ Pré-requisitos Verificados

- ✅ Vagrant instalado
- ✅ VirtualBox instalado
- ✅ Computador reiniciado

---

## 🎯 Passo 1: Verificar Instalação

```powershell
# Verificar Vagrant
vagrant --version

# Verificar VirtualBox
vboxmanage --version
```

**Se ambos funcionarem, continue!**

---

## 🎯 Passo 2: Iniciar VMs (Primeira Vez)

### Opção A: Iniciar Todas as VMs

```powershell
# No diretório do projeto
cd D:\antigravity\oraex\nprod

# Iniciar todas as VMs (pode levar 15-20 minutos na primeira vez)
vagrant up
```

**O que acontece:**
1. Vagrant baixa a imagem do SO (RHEL8/Ubuntu)
2. Cria as VMs no VirtualBox
3. Configura rede
4. Executa scripts de bootstrap

### Opção B: Iniciar Apenas VMs Oracle (Mais Rápido)

```powershell
# Iniciar apenas as 2 VMs Oracle RAC
vagrant up oracle-rac-node1 oracle-rac-node2
```

**Recomendado para começar!**

---

## 🎯 Passo 3: Aguardar Criação

**Na primeira vez, pode levar:**
- ⏱️ 10-15 minutos para baixar imagens
- ⏱️ 5-10 minutos para criar VMs
- ⏱️ Total: ~20-25 minutos

**Você verá:**
```
Bringing machine 'oracle-rac-node1' up with 'virtualbox' provider...
==> oracle-rac-node1: Importing base box 'generic/rhel8'...
==> oracle-rac-node1: Matching MAC address for NAT networking...
==> oracle-rac-node1: Setting the name of the VM...
==> oracle-rac-node1: Clearing any previously set network interfaces...
...
```

**Aguarde até ver:**
```
==> oracle-rac-node1: Machine booted and ready!
```

---

## 🎯 Passo 4: Verificar Status

```powershell
# Ver status de todas as VMs
vagrant status
```

**Deve mostrar:**
```
oracle-rac-node1    running (virtualbox)
oracle-rac-node2    running (virtualbox)
mongodb-node        not created
test-node           not created
```

---

## 🎯 Passo 5: Acessar uma VM

```powershell
# Acessar primeira VM Oracle
vagrant ssh oracle-rac-node1
```

**Você entrará na VM!** Agora pode:

```bash
# Verificar sistema
cat /etc/os-release

# Verificar usuário oracle (se foi criado)
id oracle

# Verificar diretórios
ls -la /u01/app/oracle

# Sair da VM
exit
```

---

## 🎯 Passo 6: Provisionar com Ansible (Opcional)

Depois que as VMs estiverem prontas, você pode provisionar com Ansible:

```powershell
# Sair da VM (se estiver dentro)
exit

# Provisionar com Ansible
vagrant provision oracle-rac-node1
```

**Ou manualmente:**

```powershell
# Gerar inventory do Vagrant
vagrant ssh-config > infra/ansible/inventory/vagrant-ssh-config

# Executar playbook Ansible
cd infra/ansible
ansible-playbook -i inventory/vagrant.ini playbooks/provision-cluster.yml
```

---

## 🎯 Passo 7: Testar Conexões

### Testar Oracle (quando instalado)

```powershell
# Acessar VM
vagrant ssh oracle-rac-node1

# Dentro da VM, testar (quando Oracle estiver instalado)
sqlplus / as sysdba
```

### Testar do Seu PC

As VMs estarão acessíveis em:
- `oracle-rac-node1`: 192.168.56.11
- `oracle-rac-node2`: 192.168.56.12
- `mongodb-node`: 192.168.56.20

---

## 🎯 Passo 8: Comandos Úteis

```powershell
# Ver status
vagrant status

# Parar VMs (mas manter criadas)
vagrant halt

# Reiniciar VMs
vagrant reload

# Destruir VMs (deletar tudo)
vagrant destroy

# Ver logs
vagrant up --debug

# Provisionar novamente
vagrant provision
```

---

## 🆘 Troubleshooting

### Erro: "Box not found"

```powershell
# Adicionar box manualmente
vagrant box add generic/rhel8
```

### Erro: "VT-x/AMD-V not available"

- Verificar se virtualização está habilitada no BIOS
- Verificar se Hyper-V está desabilitado (se não usar)

### VM não inicia

```powershell
# Ver logs detalhados
vagrant up --debug oracle-rac-node1

# Verificar VirtualBox
# Abrir VirtualBox e ver se VM aparece lá
```

### Rede não funciona

```powershell
# Verificar configuração de rede
vagrant ssh oracle-rac-node1
ip addr show
ping 8.8.8.8
```

---

## 📝 Próximos Passos

1. **Iniciar VMs:** `vagrant up oracle-rac-node1 oracle-rac-node2`
2. **Aguardar criação completa**
3. **Acessar:** `vagrant ssh oracle-rac-node1`
4. **Instalar Oracle** (quando estiver pronto)
5. **Testar automações** do projeto

---

## 💡 Dicas

- **Primeira vez é mais lenta** (baixa imagens)
- **Próximas vezes são rápidas** (VMs já criadas)
- **Use `vagrant halt`** ao invés de `destroy` (mantém VMs)
- **Verifique RAM disponível** (cada VM usa ~4GB)

---

**Pronto para começar? Execute `vagrant up oracle-rac-node1` e aguarde!** 🚀
