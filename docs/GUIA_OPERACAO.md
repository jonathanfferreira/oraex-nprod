# Guia de Operação ORAEX

## 1. Visão Geral

Este guia descreve os procedimentos operacionais para a suíte de automação ORAEX na Getnet.

## 2. Monitoramento Diário (N1)

### Dashboard

Acesse o dashboard em: `http://<servidor>:8000/`

**O que verificar:**

- **System Health**: Deve estar `OK`. Se `WARNING` ou `CRITICAL`, verifique os detalhes.
- **Backups**: Confirmar se o backup da noite anterior (FULL ou INCREMENTAL) está `COMPLETED`.
- **Capacity**: Verificar se algum diskgroup (FRA, DATA) está "vermelho" (>90%).

### Alertas Comuns

| Alerta | Causa Provável | Ação N1 |
|--------|----------------|---------|
| `TDE Wallet WARNING` | Wallet aberta sem Master Key | Escalonar para DBA N3 |
| `Tablespace CRITICAL` | Tablespace > 95% cheio | Verificar se autoextend está ligado ou adicionar datafile |
| `Partition WARNING` | Menos de 3 partições futuras | Rodar script de particionamento manual |
| `RMAN Failed` | Falha no backup | Verificar logs em `/var/log/oraex/rman_backup.log` |

## 3. Procedimentos de Execução Manual

### Rodar Healthcheck

```bash
python automacao/diagnosticos/oracle_healthcheck.py --user system
```

### Rodar Backup RMAN (Sob Demand)

```bash
# Backup Full
python automacao/backup/rman_backup_manager.py --type full

# Backup Archivelog
python automacao/backup/rman_backup_manager.py --type archivelog
```

### Verificar Capacidade ASM

```bash
python automacao/monitoramento/asm_capacity_report.py
```

## 4. Integração Dashboard

Para alimentar o Dashboard com dados reais, configure o script de coleta no Crontab:

```bash
# Rodar a cada 10 minutos
*/10 * * * * python /opt/oraex/automacao/run_dashboard_data.py
```

Isso gerará os JSONs em `logs/` que a API consome.

## 5. Modo Manutenção (GMUD) 🛑

Para evitar alertas falsos ou restart automático durante janelas de manutenção, ative o **Modo Manutenção**.

**Ativar (Antes da GMUD):**

```bash
python automacao/utils/maintenance.py on "GMUD-1234: Update de Kernel"
```

*Isso cria um arquivo de bloqueio que suspende todos os scripts de automação.*

**Desativar (Fim da GMUD):**

```bash
python automacao/utils/maintenance.py off
```

**Verificar Status:**

```bash
python automacao/utils/maintenance.py status
```

## 6. Integração com Zabbix/Prometheus

### Endpoint Prometheus

Métricas disponíveis em `http://<servidor>:9100` (se habilitado) ou via arquivo de texto em `/var/log/oraex/metrics.prom`.

---
**Suporte:** Equipe DBA Database Reliability Engineering (DBRE)
