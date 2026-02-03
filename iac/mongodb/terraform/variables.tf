variable "project_name" {
  type        = string
  description = "Nome do Projeto (Getnet NPROD)"
  default     = "oraex-nprod"
}

variable "environment" {
  type        = string
  description = "Ambiente (dev, homol, prod)"
  default     = "dev"
}

variable "org_id" {
  type        = string
  description = "ID da Organização MongoDB Atlas"
}

variable "region" {
  type        = string
  description = "Região Cloud Provider (AWS)"
  default     = "US_EAST_1"
}

variable "instance_size" {
  type        = string
  description = "Tamanho da Instância (M10, M20, M30...)"
  default     = "M10"
}

variable "mongodb_version" {
  type        = string
  description = "Versão do MongoDB"
  default     = "6.0"
}

variable "db_username" {
  type        = string
  description = "Usuário da Aplicação"
  default     = "app_user"
}

variable "db_password" {
  type        = string
  description = "Senha da Aplicação"
  sensitive   = true
}
