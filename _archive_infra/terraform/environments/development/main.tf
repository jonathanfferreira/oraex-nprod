# ==============================================================================
# Ambiente: DESENVOLVIMENTO
# ==============================================================================
# Configuração para ambiente de desenvolvimento (menor escala)
# ==============================================================================

# Módulo Oracle RAC - Desenvolvimento
module "oracle_rac_dev" {
  source = "../../modules/oracle-rac"
  
  cluster_name = "GNCASHPL-DEV"
  node_count   = 2  # Dev: 2 nós suficientes
  
  node_specs = {
    cpu         = 4
    memory_gb   = 16
    disk_os_gb  = 50
    disk_asm_gb = 100
  }
  
  resource_pool_id     = var.dev_resource_pool_id
  datastore_id         = var.dev_datastore_id
  shared_datastore_id  = var.dev_shared_datastore_id
  network_id           = var.dev_network_id
  
  oracle_version       = "19c"
  slo_availability     = "99.0"   # Dev: 99% aceitável
  backup_retention_days = 7       # Dev: 7 dias
  
  environment = "dev"
  
  tags = {
    Environment = "development"
    Criticality = "low"
    Backup      = "weekly"
  }
}

output "development_cluster" {
  value = module.oracle_rac_dev.cluster_summary
}
