# Apresentação Técnica e Executiva (Roteiro)

> **Dica**: Utilize este markdown como base para seus slides (PowerPoint/Google Slides). Cada "##" representa um novo slide.

---

## Slide 1: Modernização do Monitoramento e Automação Oracle

**Subtítulo**: Implementação de Práticas DBRE e Compliance (Book DBA)
**Cliente**: Getnet
**Data**: Fevereiro/2026

---

## Slide 2: O Desafio

* **Legado Crítico**: Scripts em Shell (`getm_ora_*.sh`) antigos, de difícil manutenção e sem padronização.
* **Risco Operacional**:
  * Monitoramento reativo e não preditivo.
  * Verificações manuais de compliance (erro humano).
  * Hardcoded values e dependências de OS.
* **Compliance**: Necessidade de alinhar 100% da operação às normas do **"GETNET - BOOK DBA"**.

---

## Slide 3: Nossa Solução: Abordagem DBRE

* **Database Reliability Engineering (DBRE)**:
  * Tratar infraestrutura como código (python modular).
  * **Self-Healing**: Scripts que não só alertam, mas podem corrigir (ex: Auto-Restart GoldenGate).
  * **Safety First**: Validações de segurança antes de ações destrutivas.
* **Tecnologia**:
  * Python 3.x (Padrão de mercado, robusto, bibliotecas ricas).
  * Modular (Fácil de testar e evoluir).

---

## Slide 4: Arquitetura da Solução (5 Pilares)

1. **Preventivo**: Monitoramento de Particionamento (N+2 meses) e Tablespaces.
2. **Diagnóstico**: Healthcheck inteligente via Dicionário de Dados (RMAN, Locks).
3. **Sustentação**: Housekeeper (limpeza segura de homes) e Log Rotate.
4. **Configuração**: Padronização automática de SQLNet e Services.
5. **Instalação**: Validação de pré-requisitos em segundos (JSON).

---

## Slide 5: Destaque - Compliance & Segurança

> "Como garantimos conformidade com o Book DBA?"

* **Monitoramento**: Validamos `FORCE_LOGGING`, `RECYCLEBIN` e `SPFILE` a cada execução.
* **Configuração**: Ajuste automático de `SQLNET.EXPIRE_TIME` (Dead Connection) e Timeouts.
* **Padronização**: Services criados com nomenclatura `[APP]SRV[SITE]` garantem rastreabilidade.
* **Segurança**: Script Housekeeper verifica processos ativos (`ps -ef`) antes de limpar, evitando paradas acidentais.

---

## Slide 6: Qualidade e Testes

* **Cobertura de Testes**: 100% dos scripts possuem testes unitários.
* **Simulação**: Mocks simulam cenários de falha (banco fora, disco cheio) sem precisar causar erro na produção.
* **Deploy Documentation**: FAQs de deploy e mitigação de riscos (versão Python, libs).

---

## Slide 7: Resultados e Próximos Passos

* **Resultados Imediatos**:
  * Eliminação de ruído (falsos positivos em particionamento).
  * Redução de trabalho manual (checklists e limpezas automáticas).
  * Rastreabilidade total das aplicações.
* **Próximos Passos**:
  * Implantação Piloto (DEV).
  * Agendamento no Control-M.
  * Treinamento da Equipe de Operações.

---

## Slide 8: Arquitetura de Orquestração

> "Como os scripts Python se integram com a operação?"

```text
┌─────────────────────────────────────────────────────────────┐
│                     CAMADA DE ORQUESTRAÇÃO                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Control-M  │    │   Crontab   │    │   Ansible   │     │
│  │ (Agendador) │    │  (Simples)  │    │  (Deploy)   │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
└─────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     CAMADA DE AUTOMAÇÃO                     │
│                      (Python Scripts)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Healthcheck│  │ Partitioning│ │ Housekeeper │           │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 SAÍDA (Alertas / Logs / JSON)               │
│         Zabbix  │  Splunk  │  ServiceNow  │  E-mail         │
└─────────────────────────────────────────────────────────────┘
```

**Papéis:**

* **Control-M / Crontab**: Agenda e dispara os scripts.
* **Ansible**: Distribui e atualiza os scripts em +100 servidores.
* **Python**: Executa a lógica de negócio (o trabalho real).

---

## Slide 9: Frequência de Execução Recomendada

| Script | Frequência | Justificativa |
| Script | Frequência | Justificativa |
| `oracle_healthcheck.py` | **A cada 15 min** | Detectar locks e sessões problemáticas rapidamente. |
| `check_tablespaces.py` | **A cada 1 hora** | Tablespaces podem encher rápido em horário de pico. |
| `check_partitioning.py` | **1x ao dia (manhã)** | Partições são criadas mensalmente, 1x/dia é suficiente. |
| `oracle_housekeeper.py` | **1x por semana (Domingo)** | Limpeza de disk não precisa ser frequente. |
| `smart_log_rotate.py` | **1x ao dia (madrugada)** | Logs crescem diariamente, limpar à noite. |
| `autorestart_goldengate.py` | **A cada 5 min** | GGS Abended precisa de reação imediata (Self-Healing). |
| `configure_sqlnet.py` | **Sob demanda** | Só roda após instalação ou mudança de config. |

> **Nota**: Scripts de alta frequência (15 min) são candidatos a virar **Daemons** ou **Prometheus Exporters** no futuro.
