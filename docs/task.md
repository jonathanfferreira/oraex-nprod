# Task: Projeto NProd - QA - GETNET

- [x] Check connectivity to Node 2 (ping/ssh) <!-- id: 0 -->
- [x] Install Ansible (pip) <!-- id: -1 -->
- [x] Run Ansible Playbook for Node 2 (Dry Run) <!-- id: 1 -->
- [/] Run Manual Deploy Script on Node 2 <!-- id: 2 -->
  - [x] Reload VM to fix /vagrant mount <!-- id: 2.1 -->
  - [x] Clean dirty ORACLE_HOME <!-- id: 2.1.5 -->
  - [x] Clean dirty ORACLE_HOME <!-- id: 2.1.5 -->
  - [x] Execute install script manualy (Retry 2) (Failed) <!-- id: 2.2 -->
  - [x] Manual Step-by-Step Install (Unzip Complete) <!-- id: 2.3 -->
  - [x] Execute install script manualy (Final) (Failed - OS Prereq) <!-- id: 2.2 -->
  - [x] Retry with CV_ASSUME_DISTID=OEL7.6 (Failed) <!-- id: 2.4 -->
  - [x] Manual Step-by-Step Install (Fix Inventory) <!-- id: 2.5 -->
  - [x] Fix Response File (Add OSRACDBA) <!-- id: 2.5.5 -->
  - [x] Execute install script manualy (Success with Warnings) <!-- id: 2.6 -->
- [x] Verify Oracle installation on Node 2 <!-- id: 3 -->
- [ ] Create Database (DBCA) <!-- id: 4 -->
  - [x] Prepare /u02 directories <!-- id: 4.1 -->
  - [x] Create automation script (create_database.sh) <!-- id: 4.2 -->
  - [x] Execute DBCA <!-- id: 4.3 -->
- [x] Verify DB Instance on Node 2 <!-- id: 4.4 -->
- [x] Project Evaluation & Improvement Plan <!-- id: 5 -->
  - [x] Analyze codebase structure <!-- id: 5.1 -->
  - [x] Review Python automation scripts <!-- id: 5.2 -->
  - [x] Evaluate IaC (Ansible/Terraform) <!-- id: 5.3 -->
  - [x] Generate evaluation report <!-- id: 5.4 -->
- [x] Code Improvements Phase 1 <!-- id: 6 -->
  - [x] Create centralized ConnectionConfig (utils/connection.py) <!-- id: 6.1 -->
  - [x] Refactor oracle_healthcheck.py <!-- id: 6.2 -->
  - [x] Refactor check_partitioning.py <!-- id: 6.3 -->
  - [x] Refactor check_tablespaces.py <!-- id: 6.4 -->
  - [x] Create alerting system (utils/alerting.py) <!-- id: 6.5 -->
  - [x] Commit and push to GitHub <!-- id: 6.6 -->
- [x] Execute Compliance SQL on Node 2 <!-- id: 7 -->
  - [x] Create /u02 directory structure <!-- id: 7.1 -->
  - [x] Apply FORCE_LOGGING, recyclebin, audit_trail <!-- id: 7.2 -->
  - [x] Create TS_DATA tablespace <!-- id: 7.3 -->
  - [x] Verify all parameters <!-- id: 7.4 -->
- [x] Execute Compliance SQL on Node 1 <!-- id: 8 -->
  - [x] Start VM (vagrant up) <!-- id: 8.1 -->
  - [x] Startup database instance <!-- id: 8.2 -->
  - [x] Apply configure_profiles.sql <!-- id: 8.3 -->
  - [x] Verify all parameters <!-- id: 8.4 -->
- [x] Implement Self-Healing Runbooks <!-- id: 9 -->
  - [x] Create tablespace_auto_resize.py <!-- id: 9.1 -->
  - [x] Create listener_auto_restart.py <!-- id: 9.2 -->
  - [x] Create archive_cleanup.py <!-- id: 9.3 -->
  - [x] Create runner.py (orchestrator) <!-- id: 9.4 -->
  - [x] Test imports and push to GitHub <!-- id: 9.5 -->
- [x] Implement CI/CD with GitHub Actions <!-- id: 10 -->
  - [x] Create .github/workflows/ci.yml <!-- id: 10.1 -->
  - [x] Update requirements.txt <!-- id: 10.2 -->
  - [x] Update README with CI badge <!-- id: 10.3 -->
  - [x] Push to GitHub <!-- id: 10.4 -->
- [x] Implement Observability Stack <!-- id: 11 -->
  - [x] Create Prometheus Oracle exporter <!-- id: 11.1 -->
  - [x] Create docker-compose.yml (Prometheus + Grafana) <!-- id: 11.2 -->
  - [x] Create Grafana dashboard JSON <!-- id: 11.3 -->
  - [x] Test and push to GitHub <!-- id: 11.4 -->
  - [x] Test exporter locally with Oracle VM <!-- id: 11.5 -->
  - [x] Install Prometheus standalone (Windows) <!-- id: 11.6 -->
  - [x] Install Grafana standalone (Windows) <!-- id: 11.7 -->
  - [x] Connect dashboard to Oracle exporter <!-- id: 11.8 -->
- [x] Dashboard & Alerting Enhancements <!-- id: 12 -->
  - [x] Export Grafana dashboard to Git <!-- id: 12.1 -->
  - [x] Configure Grafana alerts (tablespace > 90%) <!-- id: 12.2 -->
- [x] Test Self-Healing Runbook <!-- id: 13 -->
  - [x] Execute tablespace_auto_resize on SYSTEM <!-- id: 13.1 -->
  - [x] Verify tablespace expansion <!-- id: 13.2 -->
- [x] Implement Production Guardrails <!-- id: 14 -->
  - [x] Add disk space check before resize <!-- id: 14.1 -->
  - [x] Add execution frequency limit <!-- id: 14.2 -->
  - [x] Add DBA escalation logic <!-- id: 14.3 -->
  - [x] Test listener_auto_restart runbook <!-- id: 14.4 -->
  - [x] Test `archive_cleanup.py`
- [x] Create Deployment Guide for Getnet
- [x] Update Presentation Website with Progress Log

## Phase 5: Alertmanager Integration ✅

- [x] Implement `webhook_receiver.py` (Flask)
- [x] Configure `alertmanager.yml` routes
- [x] Add `runbook` labels to Prometheus alerts (`oracle_alerts.yml`)
- [x] Test End-to-End flow documentation

## Phase 6: Packaging & Delivery (Getnet Ready) ✅

- [x] Create `Dockerfile` for Monitoring Stack (Python + Prometheus)
- [x] Create `PyInstaller` spec for standalone executables (Windows/Linux)
- [x] Add webhook-receiver to `docker-compose.yml`
- [x] Create `build.py` helper script
- [x] Final Validation: Run packaged solution on clean VM ✅ (Fluxo validado, SSH pendente)
- [x] Submit Final Project Report

## Phase 7: Grid Infrastructure Automation 🆕

- [ ] Configure shared storage in Vagrantfile (3 ASM disks)
- [ ] Configure private interconnect network
- [ ] Configure VIPs and SCAN
- [ ] Create `grid_prereqs.yml` Ansible playbook
- [ ] Create `grid_users.yml` Ansible playbook
- [ ] Create `grid_ssh.yml` (SSH equivalence)
- [ ] Create `grid_install.yml` (Silent install)
- [ ] Create `grid_asm.yml` (Diskgroups)

## Phase 8: Oracle RAC Database Automation 🆕

- [ ] Create `rac_prereqs.yml` Ansible playbook
- [ ] Create `rac_install.yml` (Oracle Home)
- [ ] Create `rac_database.yml` (DBCA RAC)
- [ ] Create `create_rac_db.rsp` response file
- [ ] Create `verify_rac.sh` validation script
- [ ] Test failover and load balancing

## Phase 9: PSU/RU Automation 🆕

- [ ] Create `download_patch.py` (MOS API)
- [ ] Create `patch_conflict_check.sh` (OPatch analyze)
- [ ] Create `apply_patch.sh` (Aplicação)
- [ ] Create `rollback_patch.sh` (Rollback)
- [ ] Create `psu_prereqs.yml` Ansible playbook
- [ ] Create `psu_apply.yml` Ansible playbook
- [ ] Create `psu_verify.yml` Ansible playbook

## Phase 10: RMAN Backup Automation 🆕

- [ ] Create `rman_full_backup.sh`
- [ ] Create `rman_incremental.sh` (L0/L1)
- [ ] Create `rman_archivelog.sh`
- [ ] Create `rman_restore.sh`
- [ ] Create `backup_config.yml` Ansible playbook
- [ ] Create `backup_status.py` (Monitoramento)
- [ ] Add Prometheus alerts for backup failures

## Phase 11: DataGuard Standby 🆕

- [ ] Configure standby VM
- [ ] Create `create_standby.sh`
- [ ] Create `dgmgrl_config.sh` (Broker)
- [ ] Create `switchover.sh`
- [ ] Create `failover.sh`
- [ ] Create `dataguard_primary.yml` Ansible playbook
- [ ] Create `dataguard_standby.yml` Ansible playbook
- [ ] Create `dataguard_status.py` (Monitoramento)
