# Guia de Testes e Validação (Dry-Run)

Como estamos lidando com infraestrutura crítica (Banco de Dados), a Regra de Ouro é: **Nunca rode em produção sem testar antes.**

Aqui estão os comandos para validar nossos scripts de forma segura.

## 1. Python (Diagnóstico)

Como não temos um Oracle instalado aqui, criamos um "Mock" (Simulador).
Ele cria um banco de mentirinha na memória e testa se o robô sabe identificar problemas.

**Comando para rodar o teste:**

```bash
python test_healthcheck_mock.py
```

**O que esperar:**
Você deve ver logs simulados dizendo "ALERTA: Sessão bloqueada" e confirmando que o robô tentou matar a sessão (`ALTER SYSTEM KILL...`).

## 2. Ansible (Patching)

Ansible tem um modo incrível chamado **Check Mode** (Dry Run). Ele conecta no servidor, verifica tudo que faria, mas **NÃO ALTERA NADA**.

**Comando de Simulação:**

```bash
# --check: Modo simulação (não faz nada real)
# --diff: Mostra a diferença (o que mudaria nos arquivos)
ansible-playbook automacao/patching/apply_oracle_psu.yml --check --diff
```

**Validação de Sintaxe (Roda em qualquer lugar):**
Se você não tem acesso aos servidores ainda, pode validar se o YAML está escrito certo:

```bash
ansible-playbook automacao/patching/apply_oracle_psu.yml --syntax-check
```

## 3. Terraform (Infraestrutura)

Terraform tem o comando `plan`. Ele compara o seu código com o que existe na nuvem (ou VMWare) e diz exatamente o que vai criar, alterar ou destruir.

**Comando de Planejamento:**

```bash
cd infra/terraform
terraform init  # Baixa os plugins (só na 1ª vez)
terraform plan  # Mostra o plano de voo
```

**Regra:** NUNCA rode `terraform apply` sem ler o resultado do `plan` antes. Se o `plan` disser "Destroy: 1", pare e respire!
