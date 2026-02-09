# ==============================================================================
# Módulo: Oracle RAC - Data Sources
# ==============================================================================
# Data sources para consultar recursos vSphere existentes
# ==============================================================================

variable "datacenter_name" {
  description = "Nome do Datacenter vSphere"
  type        = string
  default     = "Datacenter"
}

data "vsphere_datacenter" "dc" {
  name = var.datacenter_name
}

data "vsphere_resource_pool" "pool" {
  name          = var.resource_pool_id
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_datastore" "os_ds" {
  name          = var.datastore_id
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_datastore" "shared_ds" {
  name          = var.shared_datastore_id
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "network" {
  name          = var.network_id
  datacenter_id = data.vsphere_datacenter.dc.id
}

# Template de VM (se usar template/clone)
# data "vsphere_virtual_machine" "template" {
#   name          = var.vm_template_name
#   datacenter_id = data.vsphere_datacenter.dc.id
# }
