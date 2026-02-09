# ==============================================================================
# Módulo: Oracle RAC
# ==============================================================================
# Módulo reutilizável para provisionar cluster Oracle RAC completo
# ==============================================================================

variable "cluster_name" {
  description = "Nome do cluster RAC (ex: GNCASHPL)"
  type        = string
}

variable "node_count" {
  description = "Número de nós do RAC"
  type        = number
  default     = 2
  validation {
    condition     = var.node_count >= 2 && var.node_count <= 8
    error_message = "RAC requer entre 2 e 8 nós"
  }
}

variable "node_specs" {
  description = "Especificações de cada nó"
  type = object({
    cpu        = number
    memory_gb  = number
    disk_os_gb = number
    disk_asm_gb = number
  })
  default = {
    cpu         = 4
    memory_gb   = 16
    disk_os_gb  = 50
    disk_asm_gb = 100
  }
}

variable "resource_pool_id" {
  description = "ID do Resource Pool vSphere"
  type        = string
}

variable "datastore_id" {
  description = "ID do Datastore para disco OS"
  type        = string
}

variable "shared_datastore_id" {
  description = "ID do Datastore compartilhado para ASM"
  type        = string
}

variable "network_id" {
  description = "ID da rede vSphere"
  type        = string
}

variable "oracle_version" {
  description = "Versão do Oracle (ex: 19c)"
  type        = string
  default     = "19c"
}

variable "slo_availability" {
  description = "SLO de disponibilidade (ex: 99.95)"
  type        = string
  default     = "99.95"
}

variable "backup_retention_days" {
  description = "Dias de retenção de backup"
  type        = number
  default     = 7
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Tags adicionais"
  type        = map(string)
  default     = {}
}

variable "datacenter_name" {
  description = "Nome do Datacenter vSphere"
  type        = string
  default     = "Datacenter"
}

variable "vm_template_name" {
  description = "Nome do template VM para clonar (opcional)"
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Nome do domínio para VMs"
  type        = string
  default     = "getnet.local"
}

variable "static_ips" {
  description = "Lista de IPs estáticos (opcional, se usar DHCP deixar null)"
  type        = list(string)
  default     = null
}

variable "gateway" {
  description = "Gateway padrão (necessário se usar static_ips)"
  type        = string
  default     = null
}
