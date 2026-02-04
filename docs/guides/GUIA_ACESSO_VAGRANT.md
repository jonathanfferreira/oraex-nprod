# 🔐 Guia de Acesso - VMs Vagrant

## 🚀 Acesso Rápido (Recomendado)

### Via Vagrant (Mais Fácil)

```powershell
vagrant ssh oracle-rac-node1
```

**Login automático!** Não precisa de senha. ✅

---

## 🔑 Credenciais

### Usuário Padrão

**Usuário:** `vagrant`  
**Senha:** `vagrant` (se pedir, mas geralmente não precisa)

**Acesso:**
- ✅ Via `vagrant ssh` (automático, sem senha)
- ✅ Via SSH direto: `ssh vagrant@192.168.56.11`
- ✅ Via VirtualBox Console

### Usuário Oracle (Criado Automaticamente)

**Usuário:** `oracle`  
**Senha:** Não definida (use `sudo su - oracle`)

**Para usar:**
```bash
# Dentro da VM
sudo su - oracle

# Verificar
whoami
# Deve mostrar: oracle
```

---

## 📍 IPs das VMs

| VM | IP | Porta SSH |
|----|----|-----------|
| oracle-rac-node1 | 192.168.56.11 | 22 (ou 2222 via Vagrant) |
| oracle-rac-node2 | 192.168.56.12 | 22 (ou 2222 via Vagrant) |
| mongodb-node | 192.168.56.20 | 22 |
| test-node | 192.168.56.30 | 22 |

---

## 🎯 Formas de Acesso

### 1. Via Vagrant (Recomendado) ✅

```powershell
# Acessar
vagrant ssh oracle-rac-node1

# Sair
exit
```

**Vantagens:**
- ✅ Login automático
- ✅ Sem senha
- ✅ Configuração automática de chaves SSH

### 2. Via SSH Direto

```powershell
# Do seu PC
ssh vagrant@192.168.56.11
# Senha: vagrant (se pedir)
```

### 3. Via VirtualBox Console

1. Abrir VirtualBox
2. Selecionar "ORAEX-RAC-Node1"
3. Clicar em "Iniciar"
4. Login: `vagrant`
5. Senha: `vagrant`

---

## 👤 Usuários Disponíveis

### vagrant
- **Grupos:** vagrant (sudo habilitado)
- **Home:** /home/vagrant
- **Uso:** Acesso geral, administração

### oracle
- **Grupos:** oinstall, dba
- **Home:** /home/oracle
- **Uso:** Instalação e operação Oracle
- **Acesso:** `sudo su - oracle`

---

## 🔐 Configurar Senhas (Opcional)

Se quiser definir senhas:

```bash
# Dentro da VM
sudo passwd vagrant
# Digite nova senha

sudo passwd oracle
# Digite nova senha
```

---

## ✅ Verificação Rápida

```powershell
# Acessar VM
vagrant ssh oracle-rac-node1

# Dentro da VM, verificar:
whoami          # Deve mostrar: vagrant
id oracle       # Verificar usuário oracle
ls -la /u01     # Verificar diretórios Oracle
```

---

## 📝 Resumo

**Para acessar:** `vagrant ssh oracle-rac-node1`  
**Login:** Automático (usuário vagrant)  
**Senha:** Não precisa (usa chave SSH)

**Pronto!** 🚀
