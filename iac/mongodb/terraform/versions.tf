terraform {
  required_providers {
    mongodbatlas = {
      source = "mongodb/mongodbatlas"
      version = "~> 1.10"
    }
  }
  required_version = ">= 1.0"
}

# Configuração via ENV VARS é recomendada:
# MONGODB_ATLAS_PUBLIC_KEY
# MONGODB_ATLAS_PRIVATE_KEY
provider "mongodbatlas" {}
