# Plano de Implementação: Maturidade MongoDB Enterprise (Sprint 2)

## 🎯 Objetivo

Elevar o nível de automação do módulo MongoDB para 'Enterprise Grade', paridade com o módulo Oracle. O foco é criar um conjunto robusto de ferramentas para diagnóstico, performance, backup e auditoria de segurança.

## 👥 User Review Required
>
> [!IMPORTANT]
> **Backup Strategy**: O `backup_manager.py` será um wrapper para `mongodump`/`mongorestore`. Para Atlas, recomenda-se configurar e monitorar snapshots via API, mas faremos o wrapper local por ser agnóstico.
> **Index Analysis**: Utilizaremos `$indexStats` para identificar índices pouco utilizados. Isso pode ser custoso em clusters muito grandes, recomenda-se rodar em janelas de manutenção.

## 🏗️ Proposed Changes

### 1. Diagnóstico Consolidado

Assim como `oracle_healthcheck.py`, precisamos de um "One Script to Rule Them All".

#### [NEW] `automacao/mongodb/diagnosticos/check_health.py`

- Agrega check de Replica Set & Oplog.
- Adiciona métricas de Conexões (current vs available).
- Adiciona verificação de Slow Queries (Profiling Level).

### 2. Performance (DBRE)

Identificação de ineficiências.

#### [NEW] `automacao/mongodb/monitoramento/analyze_indexes.py`

- Lista todos os índices por collection.
- Cruza com estatísticas de acesso (`$indexStats`).
- **Output**: Alerta índices com 0 acessos (Candidatos a remoção).

### 3. Backup & Recovery

Automação de DRP.

#### [NEW] `automacao/mongodb/backup/mongo_backup_manager.py`

- CLI com `argparse`.
- Suporte a compressão (`gzip`).
- Lógica de retenção local (ex: manter últimos 7 dias).

### 4. Testes e Qualidade

#### [NEW] `tests/test_mongo_integration.py`

- Teste integrado similar ao Oracle, validando o fluxo completo com mocks mais complexos para simular falhas de backup e indexes não usados.

## 🧪 Verification Plan

### Automated Tests

- **tests/test_mongo_integration.py**: Simulará um cluster onde o Backup falha e há índices não utilizados.

### Manual Verification

- Rodar `check_health.py --json` e verificar output unificado.
- Rodar `analyze_indexes.py` contra um banco de lab.
