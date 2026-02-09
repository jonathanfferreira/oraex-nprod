# ==============================================================================
# Configuração de Providers
# ==============================================================================
# Centraliza configuração de todos os providers usados no projeto
# ==============================================================================

# Provider vSphere (VMware)
provider "vsphere" {
  user                 = var.vsphere_user
  password             = var.vsphere_password
  vsphere_server       = var.vsphere_server
  allow_unverified_ssl = var.vsphere_allow_unverified_ssl
  
  # Timeout para operações longas (ex: criação de VMs)
  timeout = 30
}

# Provider AWS (se usar RDS, S3 para backups, etc.)
# provider "aws" {
#   region = var.aws_region
#   
#   default_tags {
#     tags = {
#       Project     = "ORAEX"
#       Environment = terraform.workspace
#       ManagedBy   = "Terraform"
#       Team        = "DBRE"
#     }
#   }
# }

# Provider MongoDB Atlas (se usar Atlas)
# provider "mongodbatlas" {
#   public_key  = var.mongodb_atlas_public_key
#   private_key = var.mongodb_atlas_private_key
# }
