# ORAEX - Modernização do Monitoramento Oracle (Getnet)

## 📌 Visão Geral

Projeto de automação e sustentação de bancos de dados Oracle, substituindo scripts Shell legados por Python modular e aderente às práticas de **DBRE** e **Compliance** (Book DBA).

---

## 📂 Estrutura do Projeto

```
nprod/
├── automacao/                  # 🤖 Scripts Python de Automação
│   ├── backup/                 # Gerenciamento RMAN
│   ├── configuracao/           # Tuning de Rede e Services
│   ├── diagnosticos/           # Healthcheck e Compliance
│   ├── instalacao/             # Pré-requisitos 19c
│   ├── monitoramento/          # Particionamento, Tablespaces, ASM
│   ├── patching/               # Aplicação de Patches
│   ├── relatorios/             # Geração de Reports
│   └── sustentacao/            # Housekeeper, Log Rotate, GoldenGate
├── docs/                       # 📚 Documentação
│   ├── referencias/            # PDFs da Getnet (Book DBA, Instalação, etc.)
│   ├── RELATORIO_ENTREGA_GETNET.md
│   ├── APRESENTACAO_TECNICA.md
│   └── FAQ_PERGUNTAS_DIFICEIS.md
├── infra/                      # 🏗️ Infraestrutura
│   ├── ansible/                # Playbooks e Roles Ansible
│   │   ├── inventory/          # Inventários (prod, dev)
│   │   ├── group_vars/         # Variáveis por grupo
│   │   ├── roles/              # Roles reutilizáveis
│   │   └── playbooks/          # Playbooks de deploy
│   └── terraform/              # IaC (futuro)
├── tests/                      # 🧪 Testes Automatizados
│   ├── test_*.py               # Testes unitários
│   └── run_all_tests.py        # Suite completa
├── README.md                   # Este arquivo
└── deployment_guide_and_faq.md # Guia de Deploy
```

---

## 🚀 Como Começar

### 1. Executar Testes

```bash
cd tests
python run_all_tests.py
```

### 2. Deploy com Ansible

```bash
cd infra/ansible

# Verificar sintaxe
ansible-playbook playbooks/deploy_all.yml --syntax-check

# Dry-run
ansible-playbook playbooks/deploy_all.yml -i inventory/development.ini --check --diff

# Deploy real
ansible-playbook playbooks/deploy_all.yml -i inventory/production.ini
```

### 3. Documentação para Cliente

- **[Apresentação Técnica](docs/APRESENTACAO_TECNICA.md)**: Visão executiva
- **[Relatório de Entrega](docs/RELATORIO_ENTREGA_GETNET.md)**: Detalhes técnicos

---

## 🛠️ Principais Módulos

| Script | Função | Frequência |
|--------|--------|------------|
| `oracle_healthcheck.py` | Diagnóstico completo + Compliance | A cada 15 min |
| `check_partitioning.py` | Validação preditiva de partições | Diário |
| `check_tablespaces.py` | Monitoramento de tablespaces | A cada 1 hora |
| `asm_capacity_report.py` | Auditoria ASM + Predição | Diário |
| `rman_backup_manager.py` | Gerenciamento de backups RMAN | Configurável |
| `oracle_housekeeper.py` | Limpeza segura de homes antigas | Semanal |
| `autorestart_goldengate.py` | Self-healing GoldenGate | A cada 5 min |

---

## 📊 Status

- **Testes**: 48 passando ✅
- **Cobertura**: Monitoramento, Diagnóstico, Sustentação, Backup
- **Ansible**: Estrutura completa com 5 roles

---

## 📖 Referências

Os PDFs de documentação da Getnet estão em `docs/referencias/`:

- GETNET - BOOK DBA
- Install Oracle RAC 19c
- Roteiro PSU
- E mais...
