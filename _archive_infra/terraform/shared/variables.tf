# ==============================================================================
# Variáveis Globais Compartilhadas
# ==============================================================================

variable "vsphere_user" {
  description = "Usuário vSphere"
  type        = string
  sensitive   = true
}

variable "vsphere_password" {
  description = "Senha vSphere"
  type        = string
  sensitive   = true
}

variable "vsphere_server" {
  description = "Endereço do vCenter"
  type        = string
}

variable "vsphere_allow_unverified_ssl" {
  description = "Permitir certificados SSL não verificados (apenas para dev)"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment deve ser: dev, staging ou prod"
  }
}

variable "project_name" {
  description = "Nome do projeto (ex: ORAEX)"
  type        = string
  default     = "ORAEX"
}

variable "tags" {
  description = "Tags padrão para recursos"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "ORAEX"
  }
}
