# Exemplo de Provisionamento de MongoDB Atlas (IaC)

# 1. Definição do Projeto (Ambiente Lógico)
resource "mongodbatlas_project" "oraex_project" {
  name   = var.project_name
  org_id = var.org_id
}

# 2. Cluster MongoDB (Replica Set)
resource "mongodbatlas_cluster" "oraex_cluster" {
  project_id = mongodbatlas_project.oraex_project.id
  name       = "${var.project_name}-${var.environment}-cluster"

  # Tipo de Cluster (REPLICASET ou SHARDED)
  cluster_type = "REPLICASET"
  
  # Configuração de Replicação (Ex: 3 nós para Alta Disponibilidade)
  replication_specs {
    num_shards = 1
    regions_config {
      region_name     = var.region
      electable_nodes = 3
      priority        = 7
      read_only_nodes = 0
    }
  }

  # Configuração de Hardware (Tier M10 = Padrão Startup/Dev)
  provider_name               = "AWS"
  provider_region_name        = var.region
  provider_instance_size_name = var.instance_size
  
  # Versão do MongoDB
  mongo_db_major_version = var.mongodb_version
}

# 3. Usuário de Banco de Dados (App User)
resource "mongodbatlas_database_user" "app_user" {
  username           = var.db_username
  password           = var.db_password
  project_id         = mongodbatlas_project.oraex_project.id
  auth_database_name = "admin"

  roles {
    role_name     = "readWrite"
    database_name = "oraex_db"
  }
}

# 4. Whitelist de IP (Segurança)
resource "mongodbatlas_project_ip_access_list" "test_ip" {
  project_id = mongodbatlas_project.oraex_project.id
  cidr_block = "0.0.0.0/0"
  comment    = "Permitir acesso temporário (Ajustar para VPN em PROD)"
}
