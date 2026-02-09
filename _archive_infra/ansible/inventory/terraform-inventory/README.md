# Inventory Gerado pelo Terraform

Este diretório contém inventários Ansible gerados automaticamente pelo Terraform.

## Como Funciona

1. **Terraform cria recursos** (VMs, etc.)
2. **Terraform gera inventory** via `local_file` resource
3. **Ansible usa o inventory** para configurar recursos

## Estrutura

```
terraform-inventory/
├── GNCASHPL-hosts.ini          # Cluster Oracle RAC Produção
├── GNCASHPL-DEV-hosts.ini       # Cluster Oracle RAC Dev
└── README.md                    # Este arquivo
```

## Uso

```bash
# 1. Terraform cria recursos e gera inventory
cd ../../terraform/environments/production
terraform apply

# 2. Ansible usa o inventory gerado
cd ../../ansible
ansible-playbook -i inventory/terraform-inventory/GNCASHPL-hosts.ini playbooks/provision.yml
```

## Formato do Inventory

```ini
[oracle_rac_nodes]
GNCASHPL1 ansible_host=10.23.9.6 ansible_user=oracle
GNCASHPL2 ansible_host=10.23.9.7 ansible_user=oracle

[oracle_rac_nodes:vars]
cluster_name=GNCASHPL
oracle_version=19c
environment=prod
```

## Nota Importante

⚠️ **Este diretório está no .gitignore** - os arquivos são gerados dinamicamente e não devem ser versionados.
