# Conceitos DBRE Aplicados ao Projeto ORAEX

**Database Reliability Engineering (DBRE)** é a aplicação de princípios de Site Reliability Engineering (SRE) especificamente para bancos de dados.

---

## 🎯 1. Service Level Objectives (SLOs)

### Definição

SLOs são **objetivos mensuráveis** de confiabilidade do serviço. No contexto de DBRE:

```yaml
# Exemplo de SLOs para Oracle RAC
slo_availability: 99.99%        # 4.32 minutos de downtime/mês
slo_rpo: 1h                      # Recovery Point Objective
slo_rto: 30min                   # Recovery Time Objective
slo_query_latency_p95: 100ms     # 95% das queries < 100ms
slo_connection_pool: 80%         # Pool nunca acima de 80%
```

### Implementação no Projeto

**Terraform:**
```hcl
# infra/terraform/modules/oracle-rac/variables.tf
variable "slo_availability" {
  description = "SLO de disponibilidade"
  type        = string
  default     = "99.95"
}

# Validação: Recursos mínimos para atingir SLO
resource "vsphere_virtual_machine" "rac_nodes" {
  count = var.node_count >= 2 ? var.node_count : 2  # Mínimo 2 nós para HA
  # ...
}
```

**Python (Monitoramento):**
```python
# automacao/monitoramento/slo_tracker.py
class SLOTracker:
    def check_availability(self):
        uptime = self.get_uptime_percentage()
        slo_target = 99.99
        
        if uptime < slo_target:
            self.alert(f"SLO Violation: Availability {uptime}% < {slo_target}%")
```

---

## 📊 2. Service Level Indicators (SLIs)

### Definição

SLIs são **métricas específicas** que alimentam os SLOs:

| SLI | Métrica | Como Medir |
|-----|---------|------------|
| **Availability** | Uptime % | `(total_time - downtime) / total_time` |
| **Latency** | Query Response Time | P50, P95, P99 percentis |
| **Error Rate** | Failed Queries | `failed_queries / total_queries` |
| **Throughput** | Transactions/sec | `total_transactions / time_window` |

### Implementação

```python
# automacao/monitoramento/sli_collector.py
import time
from typing import Dict

class SLICollector:
    def collect_metrics(self) -> Dict:
        return {
            "availability": self._get_uptime(),
            "latency_p50": self._get_latency_percentile(50),
            "latency_p95": self._get_latency_percentile(95),
            "latency_p99": self._get_latency_percentile(99),
            "error_rate": self._get_error_rate(),
            "throughput": self._get_throughput(),
        }
    
    def _get_latency_percentile(self, percentile: int) -> float:
        # Query: SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY elapsed_time)
        # FROM v$sql WHERE ...
        pass
```

**Prometheus Exporter:**
```python
# automacao/monitoramento/prometheus_exporter.py
from prometheus_client import Gauge, Histogram

# Métricas SLI
sli_availability = Gauge('oracle_availability_percent', 'Uptime percentage')
sli_latency_p95 = Histogram('oracle_query_latency_seconds', 'Query latency', buckets=[0.01, 0.05, 0.1, 0.5, 1.0])
sli_error_rate = Gauge('oracle_error_rate', 'Error rate (0-1)')
```

---

## 🔄 3. Error Budget

### Conceito

**Error Budget** = 100% - SLO

Se SLO é 99.99%, o Error Budget é 0.01% (4.32 minutos/mês).

### Política de Error Budget

- **Error Budget > 50%**: Pode fazer mudanças arriscadas
- **Error Budget < 50%**: Apenas mudanças críticas
- **Error Budget esgotado**: Freeze de mudanças até recuperar

### Implementação

```python
# automacao/monitoramento/error_budget.py
class ErrorBudget:
    def __init__(self, slo_percent: float):
        self.slo = slo_percent
        self.budget = 100.0 - slo_percent
    
    def calculate_remaining(self, current_availability: float) -> float:
        downtime_percent = 100.0 - current_availability
        remaining = self.budget - downtime_percent
        return max(0, remaining)  # Não pode ser negativo
    
    def can_deploy(self) -> bool:
        remaining = self.calculate_remaining(self.get_current_availability())
        return remaining > (self.budget * 0.5)  # > 50% do budget
```

---

## 🛠️ 4. Runbooks Automatizados

### Conceito

Transformar **runbooks manuais** em **código executável**.

### Exemplo: Failover Automatizado

**Runbook Manual (Antes):**
```
1. Verificar status do primary
2. Se primary down:
   a. Conectar no secondary
   b. Executar failover
   c. Validar conexões
   d. Notificar equipe
```

**Runbook Automatizado (Depois):**
```python
# automacao/runbooks/failover_automation.py
class FailoverRunbook:
    def execute(self, database: str):
        # 1. Pré-condições
        if not self._validate_preconditions(database):
            raise Exception("Preconditions not met")
        
        # 2. Executar failover
        self._execute_failover(database)
        
        # 3. Validar pós-condições
        if not self._validate_postconditions(database):
            self._rollback()
            raise Exception("Failover validation failed")
        
        # 4. Notificar
        self._notify_team(f"Failover completed for {database}")
        
        # 5. Registrar em CMDB
        self._update_cmdb(database, status="failed_over")
```

### Outros Runbooks

- **Incident Response**: Detecção automática + ação
- **Capacity Planning**: Análise preditiva de crescimento
- **Backup Validation**: Verificação automática de backups

---

## 🔍 5. Observabilidade (Three Pillars)

### 1. Métricas (Metrics)

```python
# Prometheus Exporter
from prometheus_client import Counter, Gauge, Histogram

# Contadores
query_count = Counter('oracle_queries_total', 'Total queries')
error_count = Counter('oracle_errors_total', 'Total errors')

# Gauges
connection_pool_usage = Gauge('oracle_connections_active', 'Active connections')
tablespace_usage = Gauge('oracle_tablespace_used_percent', 'Tablespace usage', ['tablespace'])

# Histogramas
query_duration = Histogram('oracle_query_duration_seconds', 'Query duration')
```

### 2. Logs (Structured Logging)

```python
# automacao/utils/logging_config.py
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "database": getattr(record, 'database', None),
            "component": record.name,
        })
```

### 3. Traces (Distributed Tracing)

Para queries complexas ou transações distribuídas:

```python
# automacao/monitoramento/tracing.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def execute_query(query: str):
    with tracer.start_as_current_span("oracle.query") as span:
        span.set_attribute("db.query", query)
        span.set_attribute("db.system", "oracle")
        # Executar query
        result = connection.execute(query)
        span.set_attribute("db.rows", len(result))
        return result
```

---

## 🚨 6. Alerting (Alert Fatigue Prevention)

### Princípio: Alertar apenas quando necessário

**Regra de Ouro:** Alertar apenas quando **ação humana** é necessária.

### Níveis de Alerta

```python
# automacao/monitoramento/alerting.py
class AlertLevel:
    CRITICAL = "critical"  # Requer ação imediata (SLO violado)
    WARNING = "warning"   # Atenção necessária (tendência ruim)
    INFO = "info"         # Informativo (sem ação)

def should_alert(metric: str, value: float, threshold: float) -> bool:
    # Alertar apenas se:
    # 1. Valor acima do threshold
    # 2. E tendência persistente (não é spike temporário)
    if value > threshold and is_persistent(metric):
        return True
    return False
```

### Alertas Inteligentes

```python
# Evitar alert fatigue
class SmartAlerting:
    def __init__(self):
        self.alert_history = {}
        self.cooldown_minutes = 15
    
    def should_send_alert(self, alert_key: str) -> bool:
        last_alert = self.alert_history.get(alert_key)
        if last_alert:
            if (datetime.now() - last_alert).seconds < (self.cooldown_minutes * 60):
                return False  # Cooldown ativo
        
        self.alert_history[alert_key] = datetime.now()
        return True
```

---

## 📈 7. Capacity Planning Automatizado

### Análise Preditiva

```python
# automacao/monitoramento/capacity_planning.py
import pandas as pd
from sklearn.linear_model import LinearRegression

class CapacityPlanner:
    def predict_growth(self, metric: str, days_ahead: int = 30):
        # Coletar dados históricos
        history = self._get_metric_history(metric, days=90)
        
        # Modelo simples (regressão linear)
        model = LinearRegression()
        X = np.arange(len(history)).reshape(-1, 1)
        y = history.values
        
        model.fit(X, y)
        
        # Prever
        future_X = np.arange(len(history), len(history) + days_ahead).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        return predictions
    
    def check_capacity_threshold(self, metric: str, threshold: float):
        prediction = self.predict_growth(metric, days_ahead=30)
        max_predicted = max(prediction)
        
        if max_predicted > threshold:
            self.alert(f"Capacity threshold will be exceeded in 30 days: {max_predicted} > {threshold}")
```

---

## 🔐 8. Security as Code

### Compliance Automatizado

```python
# automacao/diagnosticos/compliance_checker.py
COMPLIANCE_RULES = {
    "force_logging": {
        "query": "SELECT force_logging FROM v$database",
        "expected": "YES",
        "severity": "critical"
    },
    "recyclebin": {
        "query": "SELECT value FROM v$parameter WHERE name = 'recyclebin'",
        "expected": "ON",
        "severity": "high"
    },
    "tde_wallet": {
        "query": "SELECT status FROM v$encryption_wallet",
        "expected": "OPEN",
        "severity": "critical"
    }
}

def validate_compliance(connection):
    violations = []
    for rule_name, rule in COMPLIANCE_RULES.items():
        result = execute_query(connection, rule["query"])
        if result != rule["expected"]:
            violations.append({
                "rule": rule_name,
                "expected": rule["expected"],
                "actual": result,
                "severity": rule["severity"]
            })
    return violations
```

---

## 📚 Referências

- **Site Reliability Engineering (SRE) Book** - Google
- **Database Reliability Engineering** - Laine Campbell & Charity Majors
- **The Site Reliability Workbook** - Google

---

## ✅ Checklist de Maturidade DBRE

### Nível 1: Básico
- [ ] SLOs definidos e documentados
- [ ] Métricas básicas coletadas
- [ ] Alertas configurados

### Nível 2: Intermediário
- [ ] SLIs implementados
- [ ] Error Budget tracking
- [ ] Runbooks automatizados (pelo menos 1)

### Nível 3: Avançado
- [ ] Observabilidade completa (métricas, logs, traces)
- [ ] Capacity planning automatizado
- [ ] Compliance automatizado
- [ ] Self-healing básico

### Nível 4: Enterprise (Meta Getnet)
- [ ] Chaos engineering
- [ ] Auto-scaling baseado em SLOs
- [ ] Incident response automatizado
- [ ] Post-mortem automatizado
