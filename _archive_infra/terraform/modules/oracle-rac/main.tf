# ==============================================================================
# Módulo: Oracle RAC - Recursos Principais
# ==============================================================================
# Data sources estão em data.tf

# Criação dos nós RAC
resource "vsphere_virtual_machine" "rac_nodes" {
  count            = var.node_count
  name             = "${var.cluster_name}${count.index + 1}"
  resource_pool_id = data.vsphere_resource_pool.pool.id
  datastore_id     = data.vsphere_datastore.os_ds.id

  num_cpus = var.node_specs.cpu
  memory   = var.node_specs.memory_gb * 1024 # Converter GB para MB
  guest_id = "rhel8_64Guest"

  # Interface de rede
  network_interface {
    network_id   = data.vsphere_network.network.id
    adapter_type = "vmxnet3"
  }

  # Disco do Sistema Operacional
  disk {
    label            = "disk0"
    size             = var.node_specs.disk_os_gb
    eagerly_scrub    = false
    thin_provisioned = true
  }

  # Discos Compartilhados para ASM (Oracle RAC)
  disk {
    label            = "asm_data01"
    size             = var.node_specs.disk_asm_gb
    unit_number      = 1
    datastore_id     = data.vsphere_datastore.shared_ds.id
    disk_mode        = "independent_persistent"
    eagerly_scrub    = false
    thin_provisioned = false # Para performance de DB
  }

  # Configurações extras para RAC
  extra_config = {
    "disk.locking" = "false" # Permite acesso compartilhado ao disco
    "scsi0.sharedBus" = "virtual" # Compartilhamento de bus SCSI
  }
  
  # Clonar de template (se especificado)
  # clone {
  #   template_uuid = data.vsphere_virtual_machine.template.id
  #   customize {
  #     linux_options {
  #       host_name = "${var.cluster_name}${count.index + 1}"
  #       domain    = var.domain_name
  #     }
  #     network_interface {
  #       ipv4_address = var.static_ips[count.index]
  #       ipv4_netmask = 24
  #     }
  #     ipv4_gateway = var.gateway
  #   }
  # }

  # Tags para organização
  tags = merge(
    var.tags,
    {
      Name        = "${var.cluster_name}${count.index + 1}"
      Cluster     = var.cluster_name
      Node        = count.index + 1
      Environment = var.environment
      Oracle      = var.oracle_version
    }
  )
}

# Output: Lista de IPs dos nós (para Ansible inventory)
resource "local_file" "ansible_inventory" {
  count    = var.node_count
  content  = <<-EOT
    [oracle_rac_nodes]
    %{ for i, node in vsphere_virtual_machine.rac_nodes ~}
    ${node.name} ansible_host=${node.default_ip_address} ansible_user=oracle
    %{ endfor ~}
    
    [oracle_rac_nodes:vars]
    cluster_name=${var.cluster_name}
    oracle_version=${var.oracle_version}
    environment=${var.environment}
  EOT
  filename = "${path.module}/../../ansible/inventory/terraform-inventory/${var.cluster_name}-hosts.ini"
}
