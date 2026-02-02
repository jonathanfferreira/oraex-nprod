# Análise de Novas Documentações (ITGlue)

## Visão Geral

Foram processados 42 arquivos PDF. Identificamos documentações críticas que contêm roteiros manuais e scripts legados (Bash) que podem ser modernizados.

## 🚀 Oportunidades de Automação Identificadas

### 1. Modernização do Monitoramento (`GETNET - Configurar Monitoria`)

**Estado Atual:** Scripts Shell (`getm_ora_*.sh`) monolíticos, com hardcodes e lógica de grep simples.
**Funcionalidades Encontradas:**

* Verificação de Instância e Listener.
* Monitoramento de Wallet (tabelas criptografadas).
* **Backup RMAN** (Full e Arch) - Grep em logs.
* **Logs (Alert, CRS, ASM)** - Busca por strings "ORA-", "CRS-".
* **Datafiles e Tablespaces** Offline.
* **Particionamento**: Lógica complexa para verificar se partições futuras (Mês+1, Mês+2) existem.
* **GoldenGate**: Checagem de status e abend.

**Proposta:** Migrar lógica para Python/Prometheus Exporter.

* Substituir greps frágeis por queries SQL via `cx_Oracle` ou parsing estruturado.
* Criar módulo específico para **Validação de Particionamento** (ponto crítico mencionado em incidentes).

### 2. Automação de Patching (`ROTEIRO DE AUTOMATIZAÇÃO DE PSU - 19C`)

**Estado Atual:** Documento com comandos para parada, aplicação de OPatch, DataPatch e startup.
**Proposta:** Integrar ao nosso playbook Ansible `apply_oracle_psu.yml`.

* O documento já fornece os comandos exatos validados pela Getnet.

### 3. Manutenção de Espaço (`LIMPEZA DE HOMES` / `ADICAO DE DISCO`)

**Estado Atual:** Procedimentos manuais para limpar binários antigos e adicionar discos.
**Proposta:**

* Automação de limpeza de `$ORACLE_HOME/.patch_storage` e logs antigos (expandir `smart_log_rotate.py`).

### 4. Instalação e Upgrade (`Install RAC 19c`, `Upgrade 12c to 19c`)

**Estado Atual:** PDFs gigantes (100k+ chars) com prints e passos manuais.
**Proposta:**

* Longo prazo: Terraform para infra + Ansible para config.
* Focar primeiro nas tarefas repetitivas (ex: pré-requisitos de SO).

## Próximos Passos Sugeridos

1. **Portar Monitoramento de Particionamento & Backup** para Python.
2. **Validar Playbook de PSU** contra o roteiro oficial extraído.
3. **Criar Script de Limpeza de Homes** (baseado no doc de limpeza).
