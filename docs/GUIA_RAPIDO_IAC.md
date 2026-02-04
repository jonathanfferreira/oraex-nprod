# Guia Rápido: Transformação para 100% IaC

**Para:** Equipe DBRE Getnet  
**Objetivo:** Começar a usar IaC imediatamente

---

## 🎯 Visão Geral

Este projeto agora suporta **100% Infrastructure as Code**:

1. **Terraform** → Cria recursos (VMs, redes, storage)
2. **Ansible** → Configura recursos (Oracle, MongoDB, automações)
3. **Python (ORAEX)** → Operações diárias (monitoramento, backup)

---

## 🚀 Quick Start (5 minutos)

### Passo 1: Configurar Backend Terraform

```bash
# Criar bucket S3 para state (uma vez)
aws s3 mb s3://getnet-terraform-state
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Passo 2: Configurar Variáveis

```bash
cd infra/terraform/environments/production
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars com valores reais
```

### Passo 3: Inicializar e Aplicar

```bash
# Inicializar
terraform init

# Ver o que será criado (dry-run)
terraform plan

# Aplicar (criar recursos)
terraform apply
```

### Passo 4: Configurar com Ansible

```bash
cd ../../ansible
ansible-playbook -i inventory/terraform-inventory/ playbooks/integrate-terraform.yml
```

---

## 📋 Workflow Completo

### Desenvolvimento

```bash
# 1. Criar branch
git checkout -b feature/new-oracle-cluster

# 2. Modificar Terraform
vim environments/development/main.tf

# 3. Validar
terraform fmt
terraform validate

# 4. Testar em Dev
cd environments/development
terraform apply

# 5. Commit
git commit -m "Add new Oracle cluster module"
```

### Deploy em Produção

```bash
# 1. Review do código (Pull Request)
# 2. Aprovar PR
# 3. Merge para main
# 4. CI/CD executa:
terraform plan -out=tfplan
terraform apply tfplan
ansible-playbook playbooks/integrate-terraform.yml
```

---

## 🔧 Comandos Úteis

### Terraform

```bash
# Listar workspaces
terraform workspace list

# Trocar ambiente
terraform workspace select production

# Ver outputs
terraform output

# Destruir recursos (cuidado!)
terraform destroy

# Formatar código
terraform fmt -recursive

# Validar sintaxe
terraform validate
```

### Ansible

```bash
# Verificar sintaxe
ansible-playbook --syntax-check playbooks/deploy_all.yml

# Dry-run (não executa, só mostra)
ansible-playbook --check playbooks/deploy_all.yml

# Executar com verbose
ansible-playbook -vvv playbooks/deploy_all.yml

# Executar apenas uma role
ansible-playbook playbooks/deploy_all.yml --tags monitoring
```

---

## 🛡️ Boas Práticas

### 1. Sempre usar `terraform plan` antes de `apply`

```bash
terraform plan -out=tfplan
# Revisar o plan
terraform show tfplan
# Aplicar apenas se estiver correto
terraform apply tfplan
```

### 2. Versionar tudo no Git

```bash
git add .
git commit -m "Add Oracle RAC module"
git push
```

### 3. Nunca commitar secrets

```bash
# ✅ Correto
variable "password" {
  sensitive = true
}

# ❌ Errado
password = "minhasenha123"
```

### 4. Usar módulos reutilizáveis

```hcl
# ✅ Correto - Usar módulo
module "oracle_rac" {
  source = "../../modules/oracle-rac"
  # ...
}

# ❌ Errado - Duplicar código
resource "vsphere_virtual_machine" "node1" { ... }
resource "vsphere_virtual_machine" "node2" { ... }
```

---

## 📊 Monitoramento

Após provisionar, verificar saúde:

```bash
# Healthcheck
python automacao/diagnosticos/oracle_healthcheck.py --json

# Ver métricas Prometheus
curl http://localhost:9090/metrics

# Dashboard
cd dashboard
python -m uvicorn api.main:app --reload
# Abrir http://localhost:8000
```

---

## 🆘 Troubleshooting

### Erro: "Backend configuration changed"

```bash
terraform init -reconfigure
```

### Erro: "State locked"

```bash
# Verificar se outro processo está rodando
# Se não, forçar unlock (cuidado!)
terraform force-unlock <LOCK_ID>
```

### Erro: "Provider not found"

```bash
terraform init -upgrade
```

---

## 📚 Próximos Passos

1. **Ler documentação completa**: `docs/ESTRATEGIA_100_PERCENT_IAC.md`
2. **Aplicar conceitos DBRE**: `docs/DBRE_CONCEITOS_APLICADOS.md`
3. **Criar primeiro módulo**: Começar com Oracle RAC
4. **Configurar CI/CD**: GitHub Actions ou GitLab CI

---

## 💡 Dicas

- **Comece pequeno**: Um módulo por vez
- **Teste em Dev primeiro**: Sempre validar antes de Prod
- **Documente decisões**: Por que escolheu essa configuração?
- **Automatize tudo**: Se fez 2x, automatize

---

**Dúvidas?** Consultar documentação completa ou contatar equipe DBRE.
