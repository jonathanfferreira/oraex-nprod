# ==============================================================================
# Backend Remoto - State Management
# ==============================================================================
# O State do Terraform contém informações sensíveis sobre a infraestrutura.
# NUNCA commitar state files no Git!
#
# Opções de Backend:
# 1. S3 + DynamoDB (AWS) - Recomendado
# 2. Terraform Cloud (HashiCorp)
# 3. Azure Storage Account (Azure)
# 4. GCS (Google Cloud)
# ==============================================================================

terraform {
  backend "s3" {
    # Configurar via variáveis de ambiente ou terraform init -backend-config
    # bucket         = "getnet-terraform-state"
    # key            = "oraex/terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "terraform-state-lock"
    # encrypt        = true
  }
  
  # Alternativa: Terraform Cloud (se preferir)
  # backend "remote" {
  #   organization = "getnet"
  #   workspaces {
  #     name = "oraex-prod"
  #   }
  # }
}

# ==============================================================================
# Versões de Providers
# ==============================================================================

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    vsphere = {
      source  = "hashicorp/vsphere"
      version = "~> 2.2"
    }
    # Adicionar outros providers conforme necessário
    # aws = {
    #   source  = "hashicorp/aws"
    #   version = "~> 5.0"
    # }
    # mongodbatlas = {
    #   source  = "mongodb/mongodbatlas"
    #   version = "~> 1.0"
    # }
  }
}
