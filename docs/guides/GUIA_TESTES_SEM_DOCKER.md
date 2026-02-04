# 🧪 Guia de Testes SEM Docker

**Não consegue instalar Docker? Sem problemas! Você ainda pode testar muita coisa.**

---

## ✅ O Que Você PODE Testar Sem Docker

### 1. **Validação de Código**
- ✅ Sintaxe Python
- ✅ Sintaxe Ansible (playbooks, roles)
- ✅ Sintaxe Terraform (validação)
- ✅ Estrutura do projeto
- ✅ Imports e dependências

### 2. **Testes Unitários**
- ✅ Testes Python com mocks
- ✅ Validação de lógica
- ✅ Testes de funções isoladas

### 3. **Validação de Configuração**
- ✅ Arquivos de configuração
- ✅ Templates Ansible
- ✅ Variáveis Terraform

---

## 🚀 Quick Start

### Windows (PowerShell)

```powershell
# Executar testes sem Docker
.\tests\local\run_tests_no_docker.bat

# Ou diretamente
python tests/local/test_without_docker.py
```

### Linux/Mac

```bash
# Dar permissão de execução
chmod +x tests/local/run_tests_no_docker.sh

# Executar
./tests/local/run_tests_no_docker.sh
```

---

## 📋 Testes Disponíveis

### 1. Teste Completo (Recomendado)

```bash
python tests/local/test_without_docker.py
```

**O que testa:**
- ✅ Estrutura do projeto
- ✅ Imports Python
- ✅ Sintaxe de scripts
- ✅ Sintaxe Ansible
- ✅ Sintaxe Terraform
- ✅ Arquivos de configuração

### 2. Testes Unitários Python

```bash
# Instalar pytest (se não tiver)
pip install pytest

# Executar testes
python -m pytest tests/ -v
```

### 3. Validação Ansible Individual

```bash
# Verificar sintaxe de um playbook
ansible-playbook --syntax-check infra/ansible/playbooks/deploy_all.yml

# Verificar sintaxe de uma role
ansible-playbook --syntax-check infra/ansible/roles/oracle-install/tasks/main.yml
```

### 4. Validação Terraform Individual

```bash
# Validar módulo
cd infra/terraform/modules/oracle-rac
terraform init -backend=false
terraform validate
```

---

## 🔧 Alternativas ao Docker

### Opção 1: Vagrant (VMs Completas)

**Vantagens:**
- ✅ Não precisa de Docker
- ✅ Ambiente mais realista
- ✅ Testa instalação completa

**Desvantagens:**
- ⚠️ Mais pesado (precisa VirtualBox)
- ⚠️ Mais lento para iniciar

**Como usar:**
```bash
# Instalar Vagrant + VirtualBox
# https://www.vagrantup.com/downloads
# https://www.virtualbox.org/wiki/Downloads

# Iniciar VMs
vagrant up

# Provisionar
vagrant provision
```

### Opção 2: Testes com Mocks

**Vantagens:**
- ✅ Rápido
- ✅ Não precisa de infraestrutura
- ✅ Testa lógica do código

**Exemplo:**
```python
# tests/test_healthcheck_mock.py já existe!
python -m pytest tests/test_healthcheck_mock.py -v
```

### Opção 3: Conexão Remota (Se Tiver Acesso)

Se você tiver acesso a um servidor Oracle/MongoDB remoto:

```bash
# Testar conexão remota
python automacao/diagnosticos/oracle_healthcheck.py \
  --dsn servidor-remoto:1521/orcl \
  --user system \
  --password senha
```

---

## 📊 O Que Cada Teste Valida

| Teste | O Que Valida | Precisa Docker? |
|-------|-------------|-----------------|
| `test_without_docker.py` | Código, sintaxe, estrutura | ❌ Não |
| `test_ansible_syntax.py` | Sintaxe Ansible | ❌ Não |
| `test_terraform_plan.py` | Validação Terraform | ❌ Não |
| `test_oracle_connection.py` | Conexão Oracle | ✅ Sim |
| `test_mongodb_connection.py` | Conexão MongoDB | ✅ Sim |
| `pytest tests/` | Testes unitários | ❌ Não |

---

## 🎯 Fluxo Recomendado (Sem Docker)

### 1. Validação Inicial

```bash
# Teste completo sem Docker
python tests/local/test_without_docker.py
```

### 2. Testes Unitários

```bash
# Instalar pytest
pip install pytest pytest-mock

# Executar testes
python -m pytest tests/ -v
```

### 3. Validação Individual

```bash
# Ansible
ansible-playbook --syntax-check infra/ansible/playbooks/deploy_all.yml

# Terraform
cd infra/terraform/modules/oracle-rac
terraform init -backend=false
terraform validate
```

### 4. Testes com Mocks

```bash
# Testes que usam mocks (não precisam de DB real)
python -m pytest tests/test_healthcheck_mock.py -v
python -m pytest tests/test_mongo_integration.py -v
```

---

## 🆘 Troubleshooting

### Python não encontrado

```bash
# Verificar instalação
python --version

# Se não tiver, instalar:
# https://www.python.org/downloads/
```

### Ansible não encontrado

```bash
# Instalar Ansible
pip install ansible

# Verificar
ansible-playbook --version
```

### Terraform não encontrado

```bash
# Baixar Terraform:
# https://www.terraform.io/downloads

# Adicionar ao PATH
```

---

## 💡 Dicas

1. **Foque no que pode testar:** Validação de código é muito importante!
2. **Use mocks:** Testes com mocks são rápidos e eficazes
3. **Valide sintaxe:** Erros de sintaxe são fáceis de pegar localmente
4. **Teste lógica:** Testes unitários não precisam de infraestrutura

---

## 📝 Checklist de Testes (Sem Docker)

- [ ] Estrutura do projeto OK
- [ ] Imports Python funcionam
- [ ] Sintaxe Ansible válida
- [ ] Sintaxe Terraform válida
- [ ] Testes unitários passam
- [ ] Scripts Python compilam sem erro
- [ ] Arquivos de configuração existem

**Se todos passarem, você está pronto para ir para o ambiente Getnet!** 🚀

---

**Dúvidas?** Consulte `docs/TROUBLESHOOTING_DOCKER.md` para diagnosticar problemas com Docker.
