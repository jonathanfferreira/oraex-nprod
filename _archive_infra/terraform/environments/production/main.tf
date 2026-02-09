# ==============================================================================
# Ambiente: PRODUÇÃO
# ==============================================================================
# Configuração específica para ambiente de produção
# ==============================================================================

terraform {
  # Backend será configurado via terraform init -backend-config
  # ou variáveis de ambiente
}

# Módulo Oracle RAC - Produção
module "oracle_rac_prod" {
  source = "../../modules/oracle-rac"
  
  cluster_name = "GNCASHPL"
  node_count   = 4  # Produção: 4 nós para alta disponibilidade
  
  node_specs = {
    cpu         = 8
    memory_gb   = 32
    disk_os_gb  = 100
    disk_asm_gb = 500
  }
  
  resource_pool_id     = var.prod_resource_pool_id
  datastore_id         = var.prod_datastore_id
  shared_datastore_id  = var.prod_shared_datastore_id
  network_id           = var.prod_network_id
  
  oracle_version       = "19c"
  slo_availability     = "99.99"  # Produção: 99.99% (4.32 min/mês)
  backup_retention_days = 30      # Produção: 30 dias
  
  environment = "prod"
  
  tags = {
    Environment = "production"
    Criticality = "high"
    Backup      = "daily"
  }
}

# Outputs para consumo externo
output "production_cluster" {
  value = module.oracle_rac_prod.cluster_summary
  sensitive = false
}

output "production_node_ips" {
  value     = module.oracle_rac_prod.node_ips
  sensitive = true  # IPs podem ser sensíveis
}
