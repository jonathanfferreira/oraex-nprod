# Terraform - Infrastructure as Code

Estrutura modular para provisionamento de infraestrutura Oracle e MongoDB.

## 📁 Estrutura

```
terraform/
├── modules/              # Módulos reutilizáveis
│   └── oracle-rac/      # Módulo Oracle RAC completo
├── environments/         # Configurações por ambiente
│   ├── development/      # Dev
│   └── production/       # Prod
└── shared/               # Configuração compartilhada
    ├── backend.tf        # State remoto
    └── providers.tf     # Providers
```

## 🚀 Uso Rápido

### 1. Inicializar Backend

```bash
cd environments/production
terraform init -backend-config=backend.hcl
```

### 2. Planejar Mudanças

```bash
terraform plan -var-file=terraform.tfvars
```

### 3. Aplicar

```bash
terraform apply -var-file=terraform.tfvars
```

### 4. Integrar com Ansible

Após o Terraform criar recursos, o Ansible configura:

```bash
cd ../../ansible
ansible-playbook -i inventory/terraform-inventory/ playbooks/integrate-terraform.yml
```

## 🔐 Segurança

⚠️ **NUNCA commitar:**
- `terraform.tfvars` com valores reais
- `*.tfstate` files
- Credenciais em código

✅ **Usar:**
- Variáveis de ambiente
- HashiCorp Vault
- AWS Secrets Manager

## 📚 Documentação Completa

Ver: `docs/ESTRATEGIA_100_PERCENT_IAC.md`
