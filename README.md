# Projeto NProd - QA - GETNET Stack

[![CI](https://github.com/jonathanfferreira/oraex-nprod/actions/workflows/ci.yml/badge.svg)](https://github.com/jonathanfferreira/oraex-nprod/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> 🚀 **Automação inteligente para Oracle Database com Self-Healing e Observabilidade**

## 📌 Visão Geral

Solução completa de automação e auto-remediação para bancos de dados Oracle 19c, desenvolvida para a **Getnet**. Substitui scripts Shell legados por Python modular, aderente às práticas de **DBRE** (Database Reliability Engineering) e **Compliance** Getnet.

**🔗 Links:**

- [📊 Apresentação do Projeto](https://jonathanfferreira.github.io/oraex-nprod/)
- [📋 Relatório Final](docs/FINAL_REPORT.md)

---

## ✅ Status do Projeto (04/02/2026)

| Componente | Status |
|------------|--------|
| Infraestrutura (2 VMs Oracle 19c) | ✅ 100% |
| Automação Python (15+ scripts) | ✅ 100% |
| Self-Healing (4 runbooks) | ✅ 100% |
| Observabilidade (Prometheus + Grafana) | ✅ 100% |
| CI/CD (GitHub Actions) | ✅ 100% |
| Packaging (Docker + PyInstaller) | ✅ 100% |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    ORAEX Self-Healing Stack                  │
├─────────────────────────────────────────────────────────────┤
│  Prometheus → Alertmanager → Webhook → Runner → Oracle VM  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura do Projeto

```
oraex-nprod/
├── automacao/
│   ├── monitoramento/      # Healthcheck, Tablespaces
│   ├── runbooks/           # Self-Healing Automation
│   │   ├── runner.py       # Orquestrador
│   │   ├── tablespace_auto_resize.py
│   │   ├── listener_auto_restart.py
│   │   └── archive_cleanup.py
│   └── utils/              # Connection, Alerting
├── observability/
│   ├── prometheus/         # Configs + Alert Rules
│   ├── grafana/            # Dashboards
│   └── alertmanager/       # Alerting Routes
├── infra/
│   ├── ansible/            # Playbooks
│   └── Vagrantfile         # VMs locais
├── docs/                   # Documentação
├── Dockerfile              # Container Python
├── oraex.spec              # PyInstaller
└── webhook_receiver.py     # Flask Webhook
```

---

## 🚀 Quick Start

### Opção 1: Docker Compose

```bash
cd observability/
docker-compose up -d
# Acesse: Grafana http://localhost:3000 (admin/oraex123)
```

### Opção 2: Execução Local

```bash
pip install -r requirements.txt
python webhook_receiver.py  # Terminal 1
python test_alert_simulator.py --runbook tablespace  # Terminal 2
```

### Opção 3: VMs Vagrant

```bash
cd infra/
vagrant up oracle-rac-node1
vagrant ssh oracle-rac-node1
```

---

## 🛠️ Self-Healing Runbooks

| Runbook | Trigger | Ação |
|---------|---------|------|
| `tablespace_auto_resize` | TS > 85% | Adiciona datafile |
| `listener_auto_restart` | Listener Down | Restart automático |
| `archive_cleanup` | FRA > 80% | Limpa archive logs |

**Executar runbook manualmente:**

```bash
python -m automacao.runbooks.runner --runbook tablespace --dry-run
```

---

## 📊 Observabilidade

| Componente | URL | Credenciais |
|------------|-----|-------------|
| Grafana | <http://localhost:3000> | admin / oraex123 |
| Prometheus | <http://localhost:9090> | - |
| Alertmanager | <http://localhost:9093> | - |

---

## 📦 Packaging

```bash
# Build Docker
python build.py docker

# Build Executáveis Standalone
python build.py pyinstaller
```

---

## 📖 Documentação

- [Guia de Deploy Getnet](docs/deployment_guide_getnet.md)
- [Relatório Final](docs/FINAL_REPORT.md)

---

## 👤 Autor

**Jonathan Ferreira**  
Projeto: ORAEX-NPROD  
Cliente: Getnet

---

## 📜 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
