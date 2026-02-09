# -*- mode: ruby -*-
# vi: set ft=ruby :

# ==============================================================================
# Vagrantfile - Ambiente de Testes Local ORAEX
# ==============================================================================
# Cria VMs locais para testar automações Oracle sem precisar do ambiente Getnet
# ==============================================================================

# Configurar para usar disco D
ENV['VAGRANT_HOME'] ||= 'D:/vagrant'

Vagrant.configure("2") do |config|
  
  # ============================================================================
  # 1. Single Instance (Standalone)
  # ============================================================================
  config.vm.define "standalone" do |node|
    node.vm.box = "generic/oracle8"
    node.vm.hostname = "oracle-db-01.oraex.local"
    node.vm.network "private_network", ip: "192.168.56.10" # IP Dedicado Single
    
    node.vm.provider "virtualbox" do |vb|
      vb.name = "ORAEX-Standalone-DB01"
      vb.memory = 6144 # 6GB (Suficiente para Single)
      vb.cpus = 2
      vb.check_guest_additions = false # Otimização
      vb.customize ["modifyvm", :id, "--ioapic", "on"]
      # Forçar criação no disco D
      vb.customize ["setproperty", "machinefolder", "D:/VirtualBox VMs"]
      # Discos Locais (Simulados via arquivo no futuro se precisar de ASM, ou FS direto)
    end
    # Forçar sincronização de pasta para evitar erros de mount
    node.vm.synced_folder ".", "/vagrant", type: "virtualbox", owner: "vagrant", group: "vagrant"
  end

  # ============================================================================
  # 2. Oracle RAC Cluster (2 Nodes)
  # ============================================================================
  (1..2).each do |i|
    config.vm.define "rac-node#{i}" do |node|
      node.vm.box = "generic/oracle8"
      node.vm.hostname = "rac-node#{i}.oraex.local"
      
      # Public IP: 192.168.56.11, .12
      node.vm.network "private_network", ip: "192.168.56.#{10 + i}"
      
      # Private Interconnect (eth2): 192.168.10.11, .12
      node.vm.network "private_network", ip: "192.168.10.#{10 + i}", virtualbox__intnet: "rac_priv"
      
      node.vm.provider "virtualbox" do |vb|
        vb.name = "ORAEX-RAC-Node#{i}"
        vb.memory = 8192  # 8GB
        vb.cpus = 2
        vb.check_guest_additions = false # Otimização
        vb.customize ["modifyvm", :id, "--ioapic", "on"]
        # Forçar criação no disco D
        vb.customize ["setproperty", "machinefolder", "D:/VirtualBox VMs"]
        
        # Criação de discos compartilhados (apenas no Node 1 para evitar duplicação, mas anexar em ambos)
        # Caminho dos discos
        disk_path = "D:/VirtualBox VMs/SharedDisks"
        
        # Criar pasta se não existir (via powershell no host)
        # Nota: Vagrant roda no host, mas o Ruby aqui não tem acesso direto fácil ao FS do host windows de forma limpa.
        # Vamos assumir que a pasta existe ou o VirtualBox cria.
        
        if i == 1
           # Comandos para criar os discos apenas uma vez (se não existirem)
           # Workaround: Usar system call do ruby para criar pasta
           system("mkdir \"#{disk_path}\"") rescue nil
           
           DISK_CONFIG = [
             { name: "asm_ocr", size: 10240 }, # 10GB
             { name: "asm_data", size: 20480 }, # 20GB
             { name: "asm_fra", size: 10240 }   # 10GB
           ]
           
           DISK_CONFIG.each do |disk|
             file_path = "#{disk_path}/#{disk[:name]}.vdi"
             unless File.exist?(file_path)
               # Criar disco via VBoxManage (acessível via path no Windows)
               # Precisamos usar o comando raw do VB
               # 'createhd' é deprecado, usar 'createmedium'
               puts "Criando disco compartilhado: #{disk[:name]}..."
               system("VBoxManage createmedium disk --filename \"#{file_path}\" --size #{disk[:size]} --format VDI --variant Fixed")
             end
           end
        end

        # Anexar os discos em AMBOS os nós
        # Controladora SATA deve existir
        DISK_ATTACH_CONFIG = [
             { name: "asm_ocr", port: 1 },
             { name: "asm_data", port: 2 },
             { name: "asm_fra", port: 3 }
        ]
        

      
        # Shared Storage Logic - DISABLED TEMPORARILY
        # Solução Definitiva: Criar Controlador SCSI Dedicado
        # vb.customize ["storagectl", :id, "--name", "SCSI_ASM", "--add", "scsi", "--controller", "LSILogic", "--portcount", 16]
        
        # DISK_ATTACH_CONFIG.each do |disk|
        #      file_path = "D:/VirtualBox VMs/SharedDisks/#{disk[:name]}.vdi"
        #      # Attach to SCSI_ASM
        #      vb.customize ["storageattach", :id, "--storagectl", "SCSI_ASM", "--port", disk[:port], "--device", 0, "--type", "hdd", "--medium", file_path, "--mtype", "shareable"]
        # end
      end

      # Forçar sincronização de pasta para evitar erros de mount
      node.vm.synced_folder ".", "/vagrant", type: "virtualbox", owner: "vagrant", group: "vagrant"
      
      # Scripts de bootstrap removidos para simulação Bare Metal.
      # A configuração do SO será feita via Ansible (Phase 2 OS Bootstrap).

    end
  end
  
  # VM para MongoDB (opcional)
  # VM para MongoDB (opcional) - DESABILITADO PARA ECONOMIZAR RECURSOS
  # config.vm.define "mongodb-node" do |mongo|
  #   mongo.vm.box = "generic/ubuntu2004"
  #   mongo.vm.hostname = "mongodb.oraex.local"
  #   mongo.vm.network "private_network", ip: "192.168.56.20"
  #   
  #   mongo.vm.provider "virtualbox" do |vb|
  #     vb.name = "ORAEX-MongoDB"
  #     vb.memory = 2048
  #     vb.cpus = 2
  #   end
  #   
  #   mongo.vm.provision "shell", inline: <<-SHELL
  #     # Instalar MongoDB (Community)
  #     # curl -fsSL https://www.mongodb.org/static/pgp/server-6.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
  #     # echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
  #     # sudo apt-get update
  #     # sudo apt-get install -y mongodb-org
  #     # sudo systemctl start mongod
  #     # sudo systemctl enable mongod
  #   SHELL
  # end
  
  # VM para testes de automação Python
  # VM para testes de automação Python - DESABILITADO
  # config.vm.define "test-node" do |test|
  #   test.vm.box = "generic/rhel8"
  #   test.vm.hostname = "test.oraex.local"
  #   test.vm.network "private_network", ip: "192.168.56.30"
  #   
  #   test.vm.provider "virtualbox" do |vb|
  #     vb.name = "ORAEX-Test"
  #     vb.memory = 2048
  #     vb.cpus = 2
  #   end
  #   
  #   test.vm.provision "shell", inline: <<-SHELL
  #     # Instalar Python e dependências
  #     # sudo dnf install -y python3 python3-pip python3-devel gcc
  #     # sudo pip3 install cx_Oracle pymongo pytest
  #     
  #     # Sincronizar código do projeto
  #     # (Vagrant faz isso automaticamente via synced_folder)
  #   SHELL
  # end
end
