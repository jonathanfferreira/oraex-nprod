# Testes Locais - ORAEX

Guia para executar testes localmente sem precisar do ambiente Getnet.

## 🚀 Setup Rápido

### Opção 1: Docker Compose (Recomendado)

```bash
# 1. Configurar ambiente
./tests/local/test_local_setup.sh

# 2. Executar todos os testes
./tests/local/run_all_local_tests.sh
```

### Opção 2: Vagrant (VMs Completas)

```bash
# 1. Instalar Vagrant e VirtualBox
# https://www.vagrantup.com/downloads
# https://www.virtualbox.org/wiki/Downloads

# 2. Iniciar VMs
vagrant up

# 3. Provisionar com Ansible
vagrant provision

# 4. Acessar VMs
vagrant ssh oracle-rac-node1
```

## 📋 Testes Disponíveis

### 1. Testes de Sintaxe

```bash
# Ansible
python3 tests/local/test_ansible_syntax.py

# Terraform
python3 tests/local/test_terraform_plan.py
```

### 2. Testes de Conexão

```bash
# Oracle
python3 tests/local/test_oracle_connection.py

# MongoDB
python3 tests/local/test_mongodb_connection.py
```

### 3. Testes Unitários Python

```bash
python -m pytest tests/ -v
```

## 🐳 Containers Docker

### Iniciar Ambiente

```bash
docker-compose -f docker-compose.test.yml up -d
```

### Verificar Status

```bash
docker-compose -f docker-compose.test.yml ps
```

### Logs

```bash
docker-compose -f docker-compose.test.yml logs -f oracle-test
```

### Parar Ambiente

```bash
docker-compose -f docker-compose.test.yml down
```

## 🔧 Credenciais de Teste

### Oracle
- **Host:** localhost:1521
- **SID:** XE
- **User:** system
- **Password:** Oracle123!

### MongoDB
- **Host:** localhost:27017
- **User:** admin
- **Password:** admin123

### PostgreSQL
- **Host:** localhost:5432
- **User:** postgres
- **Password:** postgres123
- **Database:** testdb

## 📊 Serviços Disponíveis

- **Oracle XE:** http://localhost:5500/em (EM Express)
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)

## 🧪 Executar Suite Completa

```bash
./tests/local/run_all_local_tests.sh
```

## 📝 Notas

- **Terraform:** Testes validam sintaxe, mas não criam recursos reais (sem provider vSphere)
- **Ansible:** Testes validam sintaxe e estrutura, mas precisam de VMs para execução completa
- **Python:** Testes unitários usam mocks e não precisam de infraestrutura real

## 🆘 Troubleshooting

### Docker não inicia

```bash
# Verificar se Docker está rodando
docker ps

# Reiniciar containers
docker-compose -f docker-compose.test.yml restart
```

### Porta já em uso

```bash
# Verificar portas
netstat -tulpn | grep -E '1521|27017|5432'

# Parar serviços conflitantes ou alterar portas no docker-compose.test.yml
```

### Erro de conexão Oracle

```bash
# Verificar logs
docker-compose -f docker-compose.test.yml logs oracle-test

# Reiniciar container
docker-compose -f docker-compose.test.yml restart oracle-test
```
