# Guia de Deploy e Estratégia de Migração (Getnet)

## 1. Desafios do Ambiente Corporativo

Ao levar este projeto para a Getnet, prepare-se para os seguintes cenários comuns em grandes instituições financeiras:

### 🐍 Versão do Python

* **Desafio**: Servidores Oracle antigos (RHEL 6/7) podem ter Python 3.6 ou inferior.
* **Solução**: **O código foi refatorado para ser 100% compatível com Python 3.6+**.
  * Removemos dependências de `dataclasses` (3.7+) e `futures`.
  * Basta garantir que exista um binário `python3` (versão 3.6.8 é o padrão do RHEL 7/8 e funcionará perfeitamente).

### 📦 Dependências e Acesso à Internet

* **Desafio**: Servidores de produção **não têm acesso à internet**. `pip install` vai falhar.
* **Solução**: "Vendorizar" as dependências.
    1. Baixe os pacotes na sua máquina: `pip download -d packages -r requirements.txt`
    2. Copie a pasta `packages` junto com o projeto.
    3. Instale offline: `pip install --no-index --find-links=packages -r requirements.txt`

### 🛡️ Permissões e Usuários

* **Desafio**: Você provavelmente não terá `root` direto.
* **Solução**:
  * Todo o projeto deve rodar com o usuário **oracle** (ou `oinstall`/`dba`).
  * Diretório sugerido: `/opt/oraex` ou `/u01/app/oraex`.
  * Garanta que o usuário `oracle` tenha permissão de escrita em `/var/log/oraex` (ou use um diretório de logs dentro da própria estrutura, ex: `/opt/oraex/logs`).

---

## 2. O Que Você Vai Precisar

1. **Solicitação de Mudança (GMUD)**: Aprovação para implantar novos scripts.
2. **Jumpserver / Bastion**: Acesso SSH via Cyberark ou VPN.
3. **Service Account**: Se for usar Ansible, precisará de uma chave SSH ou usuário de serviço com `sudo` (limitado ao usuário oracle).
4. **Liberação de Rede (Firewall)**:
    * Porta **8000** (Dashboard) - Liberar para IPs da equipe de monitoramento/DBAs.
    * Porta **22** (SSH) - Já deve estar liberada.

---

## 3. Quais Arquivos Levar?

Use o script de empacotamento (`run_packaging.py`) que preparamos. Ele gera um `.zip` limpo.

O pacote contem:

* `automacao/`: O core da solução.
* `dashboard/`: O monitoramento visual.
* `requirements.txt`: Lista de libs.
* `docs/`: Documentação para o time de sustentação.
* `infra/ansible/`: Playbooks (opcional, se for usar Ansible Tower/AWX).

**O que NÃO levar:**

* `tests/`: Não é necessário em PROD.
* `__pycache__`: Lixo gerado pelo Python.
* Arquivos `.git`: Metadados de versão.

---

## 4. Como Enviar (Opções)

### Opção A: Manual (SCP/SFTP) - Mais Provável

1. Gere o pacote: `python run_packaging.py`
2. Envie para o servidor via SCP (WinSCP ou terminal):

   ```bash
   scp dist/oraex_deploy_getnet_YYYYMMDD.zip user@server:/tmp
   ```

3. Descompacte no servidor:

   ```bash
   sudo su - oracle
   mkdir -p /opt/oraex
   unzip /tmp/oraex_deploy_getnet_*.zip -d /opt/oraex
   ```

### Opção B: Via Ansible (Automatizado)

Se você tiver acesso a rodar Ansible **contra** o ambiente:

1. Edite `infra/ansible/inventory/production.ini` com os IPs.
2. Rode: `ansible-playbook infra/ansible/playbooks/deploy_all.yml`

---

## 5. Instalação (Passo a Passo)

### Passo 1: Dependências Offline

Se não tiver internet:

```bash
# Na pasta onde copiou os .whl (packages)
pip install --user --no-index --find-links=packages -r requirements.txt
```

*Nota: `--user` instala no home do oracle (`~/.local`), evitando precisar de root.*

### Passo 2: Configurar Crontab

```bash
crontab -e
```

Adicione:

```cron
# ORAEX Automation
*/5 * * * * python /opt/oraex/automacao/run_dashboard_data.py >> /var/log/oraex/dashboard_collect.log 2>&1
00 23 * * * python /opt/oraex/automacao/sustentacao/oracle_housekeeper.py >> /var/log/oraex/housekeeper.log 2>&1
```

### Passo 3: Rodar o Dashboard (Opcional)

Se for manter o dashboard ativo:

```bash
nohup python -m uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8000 &
```

---

## 6. Onde Armazenar os Códigos?

* **Servidor de Banco (On-Premise)**:
  * Caminho Padrão: `/opt/oraex` (Padrão Linux FHS)
  * Alternativa Oracle: `/u01/app/oraex` (Se `/opt` tiver pouco espaço)
* **Repositório de Código (Git)**:
  * A Getnet deve ter um GitLab/Bitbucket interno. Crie um repo `oraex-automation` lá e dê push desse código. Isso é vital para versionamento.

---

## 7. Validação Manual (Sem Scripts) 🛠️

Se você **não puder rodar scripts** (.py) devido a restrições de Change, execute estes comandos manuais no terminal Linux para validar o terreno:

### 1. Checar Python

```bash
# Verifique se existe python3 (Ideal: 3.6+)
python3 --version || python --version

# Verifique se cx_Oracle ou oracledb já existem (raro, mas possível)
pip list 2>/dev/null | grep -i oracle
```

### 2. Checar Variáveis de Ambiente

```bash
# O script depende dessas variáveis estarem setadas no usuário oracle
echo "ORACLE_HOME: $ORACLE_HOME"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
```

### 3. Checar Caminhos Críticos

```bash
# Onde fica o GoldenGate? (Valide se é /ggs mesmo)
ls -ld /ggs || echo "GoldenGate não está em /ggs"

# Temos permissão de escrita em logs?
touch /var/log/oraex_test && rm /var/log/oraex_test
# Se der "Permission denied", precisaremos mudar o LOG_DIR nos scripts.
```

### 4. Checar Banco de Dados (SQLPlus)

```sql
-- Rode com o usuário que será usado na automação (ex: system)
SELECT * FROM v$version;
SELECT status FROM v$instance;
-- Teste de permissão na view crítica do GGS
SELECT count(*) FROM v$session;
```
