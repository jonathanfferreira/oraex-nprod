# ==============================================================================
# Outputs do Módulo Oracle RAC
# ==============================================================================
# Esses outputs podem ser consumidos por outros módulos ou pelo root module
# ==============================================================================

output "cluster_name" {
  description = "Nome do cluster RAC"
  value       = var.cluster_name
}

output "node_names" {
  description = "Lista de nomes dos nós"
  value       = [for node in vsphere_virtual_machine.rac_nodes : node.name]
}

output "node_ips" {
  description = "Mapa de nomes para IPs"
  value = {
    for node in vsphere_virtual_machine.rac_nodes : node.name => node.default_ip_address
  }
}

output "ansible_inventory_path" {
  description = "Caminho do inventory Ansible gerado"
  value       = "${path.module}/../../ansible/inventory/terraform-inventory/${var.cluster_name}-hosts.ini"
}

output "cluster_summary" {
  description = "Resumo do cluster para métricas"
  value = {
    node_count     = var.node_count
    total_cpu      = var.node_specs.cpu * var.node_count
    total_memory_gb = var.node_specs.memory_gb * var.node_count
    total_storage_gb = (var.node_specs.disk_os_gb + var.node_specs.disk_asm_gb) * var.node_count
    oracle_version = var.oracle_version
    slo_availability = var.slo_availability
  }
}
