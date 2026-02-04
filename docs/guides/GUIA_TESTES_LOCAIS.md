# 🧪 Guia de Testes Locais - ORAEX

**Teste tudo localmente antes de ir para o ambiente Getnet!**

---

## 🚀 Quick Start (5 minutos)

### ⚠️ Não Consegue Instalar Docker?

**Sem problemas!** Você ainda pode testar muita coisa:
- ✅ Validação de código e sintaxe
- ✅ Testes unitários Python
- ✅ Validação Ansible/Terraform

**Ver:** [GUIA_TESTES_SEM_DOCKER.md](GUIA_TESTES_SEM_DOCKER.md)

### 1. Setup Inicial (Com Docker)

```bash
# Windows (PowerShell)
.\tests\local\test_local_setup.sh

# Linux/Mac
chmod +x tests/local/*.sh
./tests/local/test_local_setup.sh
```

### 1. Setup Inicial (Sem Docker)

```bash
# Windows
.\tests\local\run_tests_no_docker.bat

# Linux/Mac
./tests/local/run_tests_no_docker.sh
```

### 2. Executar Todos os Testes

```bash
# Windows (PowerShell)
.\tests\local\run_all_local_tests.sh

# Linux/Mac
./tests/local/run_all_local_tests.sh
```

---

## 📦 O Que Foi Criado

### 1. **Docker Compose** (`docker-compose.test.yml`)
- ✅ Oracle XE (porta 1521)
- ✅ MongoDB (porta 27017)
- ✅ PostgreSQL (porta 5432)
- ✅ Prometheus (porta 9090)
- ✅ Grafana (porta 3000)

### 2. **Vagrant** (`Vagrantfile`)
- ✅ 2 VMs Oracle RAC (simuladas)
- ✅ 1 VM MongoDB
- ✅ 1 VM de testes

### 3. **Scripts de Teste**
- ✅ `test_local_setup.sh` - Configura ambiente
- ✅ `test_oracle_connection.py` - Testa Oracle
- ✅ `test_mongodb_connection.py` - Testa MongoDB
- ✅ `test_terraform_plan.py` - Valida Terraform (sem criar recursos)
- ✅ `test_ansible_syntax.py` - Valida sintaxe Ansible
- ✅ `run_all_local_tests.sh` - Suite completa

---

## 🎯 Como Usar

### Opção 1: Docker (Mais Rápido)

```bash
# 1. Iniciar containers
docker-compose -f docker-compose.test.yml up -d

# 2. Testar conexão Oracle
python tests/local/test_oracle_connection.py

# 3. Testar conexão MongoDB
python tests/local/test_mongodb_connection.py

# 4. Ver logs
docker-compose -f docker-compose.test.yml logs -f

# 5. Parar
docker-compose -f docker-compose.test.yml down
```

### Opção 2: Vagrant (VMs Completas)

```bash
# 1. Instalar Vagrant + VirtualBox
# https://www.vagrantup.com/downloads

# 2. Iniciar VMs
vagrant up

# 3. Acessar VM
vagrant ssh oracle-rac-node1

# 4. Parar VMs
vagrant halt
```

### Opção 3: Testes Individuais

```bash
# Validar sintaxe Ansible
python tests/local/test_ansible_syntax.py

# Validar Terraform (sem criar recursos)
python tests/local/test_terraform_plan.py

# Testar automações Python
python -m pytest tests/ -v
```

---

## 🔑 Credenciais de Teste

| Serviço | Host | Usuário | Senha |
|---------|------|---------|-------|
| Oracle | localhost:1521 | system | Oracle123! |
| MongoDB | localhost:27017 | admin | admin123 |
| PostgreSQL | localhost:5432 | postgres | postgres123 |
| Grafana | localhost:3000 | admin | admin |

---

## 📊 O Que Você Pode Testar

### ✅ Pode Testar Localmente:
- ✅ Sintaxe Ansible (playbooks, roles)
- ✅ Validação Terraform (plan, validate)
- ✅ Conexões com bancos (Oracle, MongoDB, PostgreSQL)
- ✅ Automações Python (com mocks)
- ✅ Scripts de monitoramento
- ✅ SLO tracker
- ✅ Runbooks (com mocks)

### ❌ Não Pode Testar Localmente (precisa ambiente real):
- ❌ Criação real de VMs (Terraform apply)
- ❌ Instalação Oracle completa (precisa instalador)
- ❌ Configuração RAC completa (precisa múltiplas VMs)
- ❌ Integração com vSphere real

---

## 🛠️ Troubleshooting

### Docker não inicia

```bash
# Verificar Docker
docker ps

# Reiniciar
docker-compose -f docker-compose.test.yml restart
```

### Porta já em uso

Edite `docker-compose.test.yml` e altere as portas:
```yaml
ports:
  - "1522:1521"  # Mude 1521 para 1522
```

### Oracle não conecta

```bash
# Ver logs
docker-compose -f docker-compose.test.yml logs oracle-test

# Aguardar inicialização (pode levar 2-3 minutos)
docker-compose -f docker-compose.test.yml logs -f oracle-test
```

---

## 📝 Exemplos de Uso

### Testar Healthcheck Local

```bash
# 1. Iniciar Oracle
docker-compose -f docker-compose.test.yml up -d oracle-test

# 2. Aguardar inicialização
sleep 60

# 3. Executar healthcheck
python automacao/diagnosticos/oracle_healthcheck.py \
  --dsn localhost:1521/XE \
  --user system \
  --password Oracle123! \
  --json
```

### Testar SLO Tracker

```bash
python automacao/monitoramento/slo_tracker.py \
  --dsn localhost:1521/XE \
  --user system \
  --password Oracle123! \
  --json
```

### Testar MongoDB Healthcheck

```bash
python automacao/mongodb/diagnosticos/check_health.py \
  --host localhost:27017 \
  --user admin \
  --password admin123 \
  --json
```

---

## 🎓 Próximos Passos

1. **Execute os testes locais** para validar código
2. **Ajuste conforme necessário** baseado nos resultados
3. **Documente problemas encontrados**
4. **Quando estiver tudo OK localmente**, aí sim vai para ambiente Getnet!

---

**Dúvidas?** Consulte `tests/local/README.md` para mais detalhes.
