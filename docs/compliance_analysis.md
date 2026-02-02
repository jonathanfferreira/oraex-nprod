# Análise de Conformidade: GETNET BOOK DBA

## Visão Geral

O documento [BOOK DBA] define os padrões obrigatórios para ambientes Oracle na Getnet. Abaixo comparo as automações que criamos com os padrões exigidos.

### 1. Rotação de Logs (Item 16 e 31)

**Padrão Exigido:**

* Expurgo de Auditoria e Logs Grid/Oracle via CRONTAB.
* Scripts citados: `delete_logs_grid.sh` e `delete_logs_oracle.sh`.
* ADRCI Retention Policy: `SHORTP_POLICY=720` (30 dias), `LONGP_POLICY=720` (30 dias).
* **Clear Archives (Standby)**: Rotina específica para limpar archives aplicados em Standby (Item 31).

**Nossa Automação (`smart_log_rotate.py`):**

* ✅ Já implementamos limpeza de Trace, Audit e Listener XML.
* ⚠️ **Ajuste Necessário**: Validar se estamos respeitando a política de 30 dias (720 horas) do ADRCI. O script atual usa `RETENTION_DAYS_LOG = 30`. **Status: OK**.
* ❌ **Faltante**: Limpeza de Archives em Standby (Item 31). O script atual não toca em archives, pois isso é crítico para o RMAN. O documento sugere um script específico `rman_bkparch` gerenciado pelo RMAN, não "rm" manual.
* **Ação**: Adicionar verificação de políticas do ADRCI no `oracle_healthcheck.py`.

### 2. Monitoramento (Item 15 - GetMonitor)

**Padrão Exigido:**
Lista de itens obrigatórios para monitoramento:

1. Instance UP / Listener UP
2. **Wallet Chave TDE** (Tabela Dummy `SYSTEM.GETWALLET`)
3. Erro Logs (Backup Full, Transacional, Cluster, DB, ASM)
4. Capacidade Tablespaces / Diskgroups
5. Status Datafiles / Índices
6. **Server Parameter File (SPFILE)**
7. **Job Agents (Control-M / SNMP)**

**Nossa Automação (`oracle_healthcheck.py` e `check_tablespaces.py`):**

* ✅ Instance, Listener, Capacidade Tablespace.
* ✅ Logs (Backup/Alert) - Migramos grep para Views.
* ⚠️ **Ajuste Necessário**: Adicionar verificação de **Wallet TDE** (Item 15.2). O método de verificar tabela dummy `SYSTEM.GETWALLET` é bem específico da Getnet. Devemos implementar isso?
* ⚠️ **Ajuste Necessário**: Verificação de **SPFILE** (garantir que iniciou com spfile correto).

### 3. Parâmetros de Banco (Item 9)

**Padrão Exigido:**

* `recyclebin = off`
* `force_logging = on`
* `sec_case_sensitive_logon = false` (Cuidado em 12c/19c)
* `db_recovery_file_dest` vazio (Desabilita Flashback Database default?) -> *Conflita com PDF de Flashback que vimos antes?* (Verificar Item 9.8).
  * Item 9.8 diz `alter database flashback off`. Mas o Item 16 fala em `snapshot controlfile`.
  * *Nota*: Isso parece ser padrão para ambientes não-DataGuard ou padrão antigo. O PDF de Flashback analisado anteriormente era para um caso específico (PNR SQA).

**Ação:** Criar um módulo de **Compliance Check** no `oracle_healthcheck.py` para validar esses parâmetros.

### 4. Particionamento (Item 11)

**Padrão Exigido:**

* Obrigatório para plataformas transacionais.
* Uso de `INTERVAL PARTITIONING` automático é recomendado (`numtodsinterval`).
* Script: `SELECT owner,table_name,interval FROM DBA_part_tables`.

**Nossa Automação (`check_partitioning.py`):**

* ✅ Nosso script já verifica isso.
* Podemos melhorar o script para sugerir `ALTER TABLE ... SET INTERVAL` se encontrar tabelas Range sem Interval.

## Conclusão e Próximos Passos

O "BOOK DBA" confirma que estamos no caminho certo, mas adiciona requisitos específicos de "Compliance" que ainda não cobrimos.

**Prioridades:**

1. **Compliance Check**: Adicionar validação dos parâmetros obrigatórios (`Recyclebin`, `Force Logging`) no Healthcheck.
2. **Wallet TDE Check**: Adicionar verificação da tabela `SYSTEM.GETWALLET` se o cliente usa TDE (criptografia).
3. **Standby Archivelog**: O "Book" menciona limpeza de archives em Standby. Precisamos ver se o RMAN já faz isso (política de deleção) ou se precisamos de script.
