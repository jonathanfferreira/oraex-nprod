# CURSO RÁPIDO DE TERRAFORM
# -------------------------
# Terraform é "Declarativo".
# Diferente de um script (faça isso, depois isso), aqui você descreve O RESULTADO FINAL.
# Você diz: "Quero 2 VMs". O Terraform se vira para calcular o que precisa criar, alterar ou destruir para chegar lá.

terraform {
  required_providers {
    # Provider: É o "plugin" que ensina o Terraform a falar com uma tecnologia (AWS, Azure, VMWare).
    vsphere = {
      source = "hashicorp/vsphere"
      version = "2.2.0"
    }
  }
}

# Configuração do Provider (Credenciais)
provider "vsphere" {
  user                 = var.vsphere_user
  password             = var.vsphere_password
  vsphere_server       = var.vsphere_server
  allow_unverified_ssl = true
}

# RESOURCE: É o bloco fundamental. Representa um objeto real na infraestrutura (VM, Disco, Rede).
# Sintaxe: resource "tipo_do_recurso" "nome_interno_do_terraform"
resource "vsphere_virtual_machine" "rac_nodes" {
  # Count: Criaia múltiplas cópias deste recurso. Aqui criamos 2 nós iguais com um bloco só.
  count            = 2
  
  # ${count.index + 1}: Isso é interpolação.
  # Na primeira cópia, index é 0 -> GNCASHPL1
  # Na segunda cópia, index é 1 -> GNCASHPL2
  name             = "GNCASHPL${count.index + 1}"
  
  resource_pool_id = data.vsphere_resource_pool.pool.id
  datastore_id     = data.vsphere_datastore.datastore.id

  num_cpus = 4
  memory   = 16384 # 16GB RAM em Megabytes
  guest_id = "rhel8_64Guest" # Identificador do SO no VMWare

  network_interface {
    network_id = data.vsphere_network.network.id
    adapter_type = "vmxnet3" # Tipo de driver de rede de alta performance
  }

  # Disco do Sistema Operacional (/)
  disk {
    label            = "disk0"
    size             = 50 # 50GB
  }

  # Discos Compartilhados para ASM (Oracle RAC)
  # Isso automatiza aquela parte chata do PDF de "Add New Hard Disk" -> "Existing Disk" -> "Multi-writer"
  disk {
     label = "asm_data01"
     size  = 100
     unit_number = 1
     datastore_id = data.vsphere_datastore.shared_ds.id
     
     # Independent Persistent: O disco não é afetado por snapshots da VM (importante para performance de DB)
     disk_mode    = "independent_persistent" 
  }
  
  # Configurações extras (Vmx options)
  extra_config = {
    "disk.locking" = "false" # Permite que duas VMs gravem no mesmo disco ao mesmo tempo (Cluster)
  }
}
