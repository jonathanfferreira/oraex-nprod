# ORAEX Observability Stack

Stack de observabilidade para monitoramento de Oracle Database com Prometheus e Grafana.

## 🚀 Quick Start

### 1. Configurar variáveis de ambiente

```bash
export ORACLE_DSN=oracle-server:1521/orcl
export ORACLE_USER=system
export ORACLE_PASSWORD=your_password
```

### 2. Iniciar a stack

```bash
cd observability
docker-compose up -d
```

### 3. Acessar os serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Grafana** | <http://localhost:3000> | admin / oraex123 |
| **Prometheus** | <http://localhost:9090> | - |
| **Oracle Exporter** | <http://localhost:9161/metrics> | - |
| **AlertManager** | <http://localhost:9093> | - |

## 📊 Métricas Expostas

O Oracle Exporter coleta as seguintes métricas:

### Database Status

- `oracle_up` - Database disponibilidade (1=UP, 0=DOWN)
- `oracle_instance_uptime_minutes` - Tempo de uptime

### Tablespaces

- `oracle_tablespace_used_percent` - % de uso por tablespace
- `oracle_tablespace_size_mb` - Tamanho total em MB
- `oracle_tablespace_free_mb` - Espaço livre em MB

### Sessions

- `oracle_sessions_count` - Contagem por status (active/inactive)
- `oracle_sessions_total` - Total de sessões

### Wait Events

- `oracle_wait_time_seconds` - Tempo de espera por classe
- `oracle_wait_count` - Contagem de waits

### Flash Recovery Area

- `oracle_fra_used_percent` - % de uso da FRA
- `oracle_fra_limit_mb` - Limite configurado
- `oracle_fra_used_mb` - Espaço usado

## 🚨 Alertas Configurados

| Alerta | Threshold | Severidade |
|--------|-----------|------------|
| OracleDatabaseDown | up == 0 | 🔴 critical |
| TablespaceUsageWarning | > 85% | 🟡 warning |
| TablespaceUsageCritical | > 95% | 🔴 critical |
| FRAUsageWarning | > 80% | 🟡 warning |
| FRAUsageCritical | > 95% | 🔴 critical |
| HighSessionCount | > 200 | 🟡 warning |

## 📁 Estrutura de Arquivos

```
observability/
├── docker-compose.yml          # Stack completa
├── Dockerfile.exporter         # Container do exporter
├── README.md                   # Esta documentação
├── prometheus/
│   ├── prometheus.yml          # Config do Prometheus
│   └── rules/
│       └── oracle_alerts.yml   # Regras de alerta
├── grafana/
│   ├── dashboards/
│   │   └── oracle-overview.json  # Dashboard pré-configurado
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml
│       └── dashboards/
│           └── dashboards.yml
└── alertmanager/
    └── alertmanager.yml        # Config de notificações
```

## 🔧 Execução Local (sem Docker)

```bash
# Instalar dependências
pip install cx_Oracle

# Executar exporter
python -m automacao.observability.oracle_exporter \
    --port 9161 \
    --dsn oracle-server:1521/orcl \
    --user system \
    --password oracle
```

## 🎨 Personalizando o Dashboard

O dashboard pode ser editado diretamente no Grafana e exportado:

1. Acesse <http://localhost:3000>
2. Navegue até **Oracle > Oracle Database Overview**
3. Faça as modificações desejadas
4. Clique em ⚙️ > **JSON Model** para exportar

## 📝 Notas

- O exporter usa a biblioteca `cx_Oracle` que requer Oracle Instant Client
- O intervalo padrão de scrape é 60 segundos
- Os dados são retidos por 30 dias no Prometheus
