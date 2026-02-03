# ORAEX - Modernização do Monitoramento Oracle (Getnet)

[![CI](https://github.com/jonathanfferreira/oraex-nprod/actions/workflows/ci.yml/badge.svg)](https://github.com/jonathanfferreira/oraex-nprod/actions/workflows/ci.yml)

## 📌 Visão Geral

Projeto de automação e sustentação de bancos de dados Oracle, substituindo scripts Shell legados por Python modular e aderente às práticas de **DBRE** (Database Reliability Engineering) e **Compliance** (Book DBA).

**Objetivo Getnet:** Transformar toda infraestrutura em **100% Infrastructure as Code (IaC)** e Automação Inteligente.

---

## 📊 Status Atual (03/02/2026)

### ✅ Entregas Recentes

- **Oracle Database 19c (Node 2)**: Instalação bem-sucedida em modo Standalone.
  - **Compliance**: Estrutura de diretórios `/u01` (Binários) e `/u02` (Dados) implementada.
  - **Automação**: Scripts de deploy silencioso (`db_install.rsp`, `dbca_create.rsp`) validados.
  - **Bypass**: Solução de contorno para instalação em Oracle Linux 8 aplicada.

- **Stack de Automação Python**:
  - `oracle_healthcheck.py`: Diagnóstico completo.
  - `check_terms.py`: Compliance de particionamento.

### 🚧 Em Andamento

- Configuração de monitoramento no Node 2.
- Planejamento de infraestrutura para RAC Real (Discos Compartilhados).

---

## 📂 Estrutura do Projeto

```
nprod/
├── automacao/                  # 🤖 Scripts Python de Automação
│   ├── diagnosticos/           # Healthcheck e Compliance
│   ├── monitoramento/          # Particionamento, Tablespaces
│   ├── runbooks/               # 🆕 Self-Healing Automation
│   │   ├── runner.py           # Orquestrador de runbooks
│   │   ├── tablespace_auto_resize.py
│   │   ├── listener_auto_restart.py
│   │   └── archive_cleanup.py
│   ├── utils/                  # 🆕 Utilitários centralizados
│   │   ├── connection.py       # ConnectionConfig
│   │   └── alerting.py         # Sistema de alertas
│   └── sustentacao/            # Housekeeper, Log Rotate
├── docs/                       # 📚 Documentação
│   ├── referencias/            # Documentos Oficiais (Getnet/Oracle)
│   ├── RELATORIO_ENTREGA_NODE2.md # 🆕 Detalhes da entrega do Node 2
│   └── ...
├── infra/                      # 🏗️ Infraestrutura (IaC)
│   ├── ansible/                # Playbooks de Configuração
│   └── terraform/              # Provisionamento
├── scripts/                    # 🛠️ Scripts Shell Auxiliares
│   ├── deploy_oracle_software.sh # Instalação de Binários
│   ├── create_database.sh        # Criação de Banco (DBCA)
│   └── verify_db.sh              # Validação de Instância
└── Vagrantfile                 # Definição de Ambiente Local
```

---

## 🚀 Como Executar (Ambiente Local)

### 1. Iniciar VMs

```bash
vagrant up oracle-rac-node1 oracle-rac-node2
```

### 2. Acessar Ambiente (Node 2)

```bash
vagrant ssh oracle-rac-node2
```

### 3. Verificar Banco de Dados

```bash
sudo -u oracle bash /vagrant/scripts/verify_db.sh
```

---

## 🛠️ Principais Módulos Python

| Script | Função | Status |
|--------|--------|--------|
| `oracle_healthcheck.py` | Diagnóstico completo + Compliance | ✅ Prod |
| `check_partitioning.py` | Validação preditiva de partições | ✅ Prod |
| `check_tablespaces.py` | Monitoramento de tablespaces | ✅ Prod |
| `asm_capacity_report.py` | Auditoria ASM + Predição | ✅ Prod |

---

## 📖 Referências

Os PDFs de documentação e relatórios detalhados estão em `docs/`.
