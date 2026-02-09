# Role: oracle-install

Role Ansible para instalação completa Oracle 19c, incluindo suporte a RAC.

## Descrição

Esta role automatiza:
- Preparação do sistema (pacotes, usuários, diretórios, kernel)
- Instalação Oracle 19c (silent mode)
- Configuração RAC (opcional)
- Validação pós-instalação

## Uso

### Instalação Básica (Standalone)

```yaml
- hosts: oracle_servers
  roles:
    - role: oracle-install
      vars:
        oracle_sid: orcl
        oracle_home: /u01/app/oracle/product/19.0.0/dbhome_1
```

### Instalação RAC

```yaml
- hosts: rac_nodes
  roles:
    - role: oracle-install
      vars:
        is_rac: true
        configure_rac: true
        cluster_name: GNCASHPL
        rac_nodes:
          - host: rac-node1.getnet.local
          - host: rac-node2.getnet.local
```

## Variáveis Principais

Ver `defaults/main.yml` para lista completa.

### Obrigatórias
- `oracle_user`: Usuário Oracle (padrão: oracle)
- `oracle_home`: Oracle Home path
- `oracle_base`: Oracle Base path

### Opcionais
- `is_rac`: Habilitar RAC (padrão: false)
- `configure_asm`: Configurar ASM (padrão: false)
- `oracle_installer_path`: Caminho do instalador Oracle

## Tags

- `prepare`: Preparação do sistema
- `install`: Instalação Oracle
- `rac`: Configuração RAC
- `validate`: Validação
- `oracle-install`: Todas as tasks

## Exemplo Completo

```yaml
- name: Instalar Oracle 19c RAC
  hosts: rac_nodes
  become: yes
  roles:
    - role: oracle-install
      vars:
        is_rac: true
        configure_rac: true
        cluster_name: GNCASHPL
        oracle_installer_path: /u02/oracle/installer
        oracle_password: "{{ vault_oracle_password }}"
  tags: [oracle-install]
```

## Notas

- O instalador Oracle deve estar disponível em `oracle_installer_path`
- Para RAC, configurar `is_rac: true` e `configure_rac: true`
- Senhas devem ser gerenciadas via Ansible Vault

## Dependências

- Role `oraex_base` (preparação básica)
- Pacote `oracle-database-preinstall-19c`
