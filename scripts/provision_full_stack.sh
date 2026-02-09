#!/bin/bash
# =============================================================================
# Script: provision_full_stack.sh
# Descrição: Orquestrador Mestre (One-Click Deploy)
# =============================================================================

# 1. OS Prerequisites
echo ">>> [1/3] Applying OS Prerequisites..."
sudo bash /home/vagrant/scripts/deploy_rac_prerequisites.sh

# 2. Software Install
echo ">>> [2/3] Installing Oracle Software..."
sudo bash /home/vagrant/scripts/deploy_oracle_software.sh

# 3. Database Creation
echo ">>> [3/3] Creating Database & Profiles..."
sudo bash /home/vagrant/scripts/create_database.sh

echo ">>> ✅ FULL PROVISIONING COMPLETED!"
