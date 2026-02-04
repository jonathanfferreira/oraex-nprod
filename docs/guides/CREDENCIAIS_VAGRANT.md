# 🔐 Credenciais Vagrant - Como Acessar as VMs

## 📋 Credenciais Padrão

### Acesso via Vagrant (Recomendado)

```powershell
# Acessar VM (login automático)
vagrant ssh oracle-rac-node1
```

**Não precisa de senha!** O Vagrant usa chave SSH automaticamente.

---

## 🔑 Credenciais Manuais (Se Precisar)

### Via SSH Direto

**Usuário:** `vagrant`  
**Senha:** `vagrant` (padrão, mas pode não funcionar - melhor usar chave SSH)

**IPs das VMs:**
- `oracle-rac-node1`: 192.168.56.11
- `oracle-rac-node2`: 192.168.56.12
- `mongodb-node`: 192.168.56.20
- `test-node`: 192.168.56.30

**Porta SSH:** 22 (ou 2222 via port forwarding do Vagrant)

### Exemplo de Conexão SSH Manual

```powershell
# Usando PuTTY ou SSH
ssh vagrant@192.168.56.11
# Senha: vagrant (se pedir)
```

**Mas é mais fácil usar `vagrant ssh`!**

---

## 🚀 Formas de Acesso

### Opção 1: Via Vagrant (Mais Fácil) ✅

```powershell
# Acessar VM
vagrant ssh oracle-rac-node1

# Sair
exit
```

### Opção 2: Via SSH Direto

```powershell
# Do seu PC
ssh vagrant@192.168.56.11
# Ou
ssh -p 2222 vagrant@127.0.0.1
```

### Opção 3: Via VirtualBox Console

1. Abrir VirtualBox
2. Selecionar VM "ORAEX-RAC-Node1"
3. Clicar em "Iniciar"
4. Login: `vagrant` / Senha: `vagrant`

---

## 👤 Usuários Criados nas VMs

### Usuário Padrão
- **vagrant** - Usuário padrão do Vagrant (sudo habilitado)

### Usuário Oracle (Criado pelos Scripts)
- **oracle** - Usuário para Oracle Database
- **Grupos:** oinstall, dba
- **Home:** /home/oracle
- **Senha:** Não definida (use `sudo su - oracle`)

### Trocar para Usuário Oracle

```bash
# Dentro da VM
sudo su - oracle

# Verificar
whoami
# Deve mostrar: oracle

# Sair
exit
```

---

## 🔐 Configurar Senha (Opcional)

Se quiser definir senha para os usuários:

```bash
# Dentro da VM
sudo passwd vagrant
# Digite nova senha

sudo passwd oracle
# Digite nova senha
```

---

## 📝 Resumo Rápido

| Método | Comando | Login |
|--------|---------|-------|
| **Vagrant SSH** | `vagrant ssh oracle-rac-node1` | Automático (sem senha) |
| **SSH Direto** | `ssh vagrant@192.168.56.11` | vagrant / vagrant |
| **VirtualBox** | Console da VM | vagrant / vagrant |

---

## ✅ Recomendação

**Use sempre `vagrant ssh`** - é mais fácil e seguro!

```powershell
vagrant ssh oracle-rac-node1
```

**Pronto! Você está dentro da VM!** 🎉
