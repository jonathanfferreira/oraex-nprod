# Guia Estratégico de Automação e IaC para Bancos de Dados Heterogêneos (Getnet - NPROD)

## 1. Introdução

Este documento visa estender a abordagem de Database Reliability Engineering (DBRE) e Infraestrutura como Código (IaC), já aplicada com sucesso aos bancos de dados Oracle no projeto NPROD da Getnet, para outras tecnologias de banco de dados presentes no ambiente: MongoDB, MySQL, PostgreSQL e SQL Server. O objetivo é padronizar e automatizar a gestão dessas plataformas, garantindo eficiência, segurança e conformidade.

## 2. Pilares de Automação e IaC

Os pilares de automação e IaC para bancos de dados heterogêneos seguirão a mesma lógica do projeto Oracle, adaptando-se às particularidades de cada tecnologia:

### 2.1. Provisionamento de Infraestrutura (IaC - Terraform)

O Terraform será a ferramenta central para o provisionamento de recursos de infraestrutura para cada banco de dados.

- **Objetivo**: Garantir que a infraestrutura subjacente seja definida, versionada e provisionada de forma consistente.
- **Recursos**: VMs, discos de armazenamento, grupos de segurança, instâncias gerenciadas (RDS, Cloud SQL).

### 2.2. Configuração e Gerenciamento (Ansible)

Utilizado para a configuração pós-provisionamento e gerenciamento contínuo.

- **Objetivo**: Automatizar a configuração (my.cnf, postgresql.conf), tuning de parâmetros e hardening de segurança.
- **Tarefas**: Instalação de pacotes, criação de usuários e roles, aplicação de patches.

### 2.3. Automação de Operações (Python)

Scripts Python modulares para automação de tarefas diárias e lógicas DBRE.

- **Objetivo**: Reduzir intervenção manual, auto-healing e compliance.
- **Exemplos**: Monitoramento de espaço, verificação de replicação, auto-restart.

### 2.4. Versionamento de Esquema (Flyway/Liquibase)

Integração via CI/CD para gerenciar alterações de DDL de forma auditável.

- **Objetivo**: Consistência de schema entre ambientes (Dev/Homol/Prod) e capacidade de rollback.

### 2.5. Observabilidade (Prometheus/Grafana)

Implementação de exporters específicos para cada tecnologia.

- **Objetivo**: Visibilidade em tempo real sobre saúde e performance.
- **Métricas**: CPU, IOPS, latência, conexões, replication lag.

## 3. Recomendações por Tecnologia

### 3.1. MongoDB

- **Terraform**: Provisionamento de Atlas/VMs e Sharding.
- **Ansible**: Configuração de mongod.conf (auth, storage engine).
- **Python**: Monitoramento de Replica Sets e Sharding status.
- **Schema**: Validações customizadas (MongoDB Atlas CLI).

### 3.2. MySQL

- **Terraform**: RDS ou VMs.
- **Ansible**: Tuning my.cnf, gestão de usuários.
- **Python**: Monitoramento de replicação Master-Slave/Group Replication.
- **Schema**: Flyway ou Liquibase.

### 3.3. PostgreSQL

- **Terraform**: RDS ou Cloud SQL.
- **Ansible**: Tuning postgresql.conf, extensão PostGIS.
- **Python**: Monitoramento de bloat, conexões e streaming replication.
- **Schema**: Sqitch (workflow Git-like) ou Flyway.

### 3.4. SQL Server

- **Terraform**: Azure SQL ou VMs Windows.
- **Ansible**: Instalação de features, tuning tempdb, DSC (PowerShell).
- **Python/PowerShell**: Monitoramento de AlwaysOn, jobs do Agent.
- **Schema**: SSDT (SQL Server Data Tools).

## 4. Padrões Técnicos Globais

- **Linguagem**: Python (pymongo, psycopg2, pyodbc).
- **Configuração**: Ansible.
- **Infra**: Terraform.
- **Segredos**: HashiCorp Vault ou Cloud Secrets Manager (Sem hardcoding!).
- **CI/CD**: GitHub Actions / GitLab CI.
- **Observabilidade**: Logs JSON + Exporters Prometheus.

## 5. Roadmap Sugerido

1. **Priorização**: Identificar banco de maior risco/ganho.
2. **POC**: Prova de Conceito focada em um pilar (ex: Monitoramento).
3. **Desenvolvimento Iterativo**: Ciclos curtos com testes.
4. **Capacitação**: Treinamento da equipe DBRE.
5. **Rollout**: Deploy gradual partindo de ambientes não-críticos.
