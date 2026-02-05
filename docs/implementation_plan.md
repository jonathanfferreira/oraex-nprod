# Oracle Infrastructure & Automation Roadmap

**Projeto:** Projeto NProd - QA - GETNET  
**Cliente:** Getnet  
**Período:** Fev/2026+

---

## 📊 Visão Geral das Fases

| Fase | Foco | Tempo Est. | Prioridade |
|------|------|------------|------------|
| ✅ 1-6 | Single Instance + Self-Healing | Concluído | - |
| 🆕 7 | Grid Infrastructure | 2 dias | Alta |
| 🆕 8 | Oracle RAC Database | 1.5 dias | Alta |
| 🆕 9 | PSU/RU Automation | 1 dia | Alta |
| 🆕 10 | RMAN Backup Automation | 1 dia | Média |
| 🆕 11 | DataGuard Standby | 2 dias | Média |

**Tempo Total Estimado:** ~7.5 dias

---

## Phase 7: Grid Infrastructure (2 dias)

### 7.1 Storage Compartilhado

- [ ] Atualizar Vagrantfile com 3 discos ASM compartilhados
- [ ] Configurar udev rules para persistência

### 7.2 Network RAC

- [ ] Private interconnect (eth2)
- [ ] VIPs e SCAN (3 IPs)
- [ ] Update /etc/hosts

### 7.3 Ansible Playbooks

- [ ] `grid_prereqs.yml` - Pacotes, limites, kernel
- [ ] `grid_users.yml` - grid user, grupos asm*
- [ ] `grid_ssh.yml` - SSH equivalence
- [ ] `grid_install.yml` - Silent install
- [ ] `grid_asm.yml` - Diskgroups (+DATA, +FRA, +OCR)

---

## Phase 8: Oracle RAC Database (1.5 dias)

### 8.1 Ansible Playbooks

- [ ] `rac_prereqs.yml`
- [ ] `rac_install.yml` - Oracle Home
- [ ] `rac_database.yml` - DBCA RAC

### 8.2 Response Files

- [ ] `create_rac_db.rsp`

### 8.3 Scripts

- [ ] `verify_rac.sh`
- [ ] `rac_status.py`

### 8.4 Testes

- [ ] Failover de instância
- [ ] Load balancing

---

## Phase 9: PSU/RU Automation (1 dia)

### 9.1 Scripts de Patch

- [ ] `download_patch.py` - Download via MOS API
- [ ] `patch_conflict_check.sh` - OPatch analyze
- [ ] `apply_patch.sh` - Aplicação de patch
- [ ] `rollback_patch.sh` - Rollback em caso de falha

### 9.2 Ansible Playbooks

- [ ] `psu_prereqs.yml` - Pré-checks
- [ ] `psu_apply.yml` - Aplicação
- [ ] `psu_verify.yml` - Validação pós-patch

### 9.3 Self-Healing

- [ ] `patch_status_runbook.py` - Verificação de patches

---

## Phase 10: RMAN Backup Automation (1 dia)

### 10.1 Scripts RMAN

- [ ] `rman_full_backup.sh` - Backup full
- [ ] `rman_incremental.sh` - Backup incremental L0/L1
- [ ] `rman_archivelog.sh` - Backup de archives
- [ ] `rman_restore.sh` - Restore/Recovery

### 10.2 Ansible Playbooks

- [ ] `backup_config.yml` - Configuração RMAN
- [ ] `backup_schedule.yml` - Cron jobs

### 10.3 Monitoramento

- [ ] `backup_status.py` - Status de backups
- [ ] Alertas Prometheus para falhas

---

## Phase 11: DataGuard Standby (2 dias)

### 11.1 Infraestrutura

- [ ] Configurar VM standby
- [ ] Network entre primary e standby

### 11.2 Scripts

- [ ] `create_standby.sh` - Criação do standby
- [ ] `dgmgrl_config.sh` - Configuração Broker
- [ ] `switchover.sh` - Switchover
- [ ] `failover.sh` - Failover

### 11.3 Ansible Playbooks

- [ ] `dataguard_primary.yml`
- [ ] `dataguard_standby.yml`
- [ ] `dataguard_broker.yml`

### 11.4 Monitoramento

- [ ] `dataguard_status.py` - Status de sync
- [ ] Alertas para lag de aplicação

---

## Próximos Passos Imediatos

1. **Amanhã/Sexta:** Começar Phase 7 (Grid Infrastructure)
2. **Baixar Grid Infrastructure 19c** do Oracle (se não tiver)
3. **Ajustar Vagrantfile** para 8GB RAM por VM

---

## Arquitetura Final (Pós Phase 11)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Oracle RAC + DataGuard                        │
├─────────────────────────────────────────────────────────────────┤
│  PRIMARY SITE                    │  STANDBY SITE                │
│  ┌───────────┐  ┌───────────┐   │  ┌───────────────────────┐   │
│  │  Node 1   │  │  Node 2   │   │  │   Standby Database    │   │
│  │  (orcl1)  │  │  (orcl2)  │   │  │       (orcl)          │   │
│  └─────┬─────┘  └─────┬─────┘   │  └───────────┬───────────┘   │
│        │              │         │              │               │
│  ┌─────┴──────────────┴─────┐   │  ┌───────────┴───────────┐   │
│  │   ASM (+DATA, +FRA)      │   │  │   ASM (+DATA, +FRA)   │   │
│  └──────────────────────────┘   │  └───────────────────────┘   │
├─────────────────────────────────┴───────────────────────────────┤
│              DataGuard Redo Transport (ASYNC/SYNC)              │
└─────────────────────────────────────────────────────────────────┘
```
