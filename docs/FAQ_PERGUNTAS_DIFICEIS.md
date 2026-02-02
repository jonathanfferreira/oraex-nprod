# FAQ - Perguntas Difíceis da Reunião

> Este documento prepara você para responder perguntas técnicas e de gestão que podem surgir na apresentação do projeto.

---

## 🔴 Categoria: Risco e Segurança

### "E se o script derrubar a produção?"

**Resposta Técnica:**
> "Todos os scripts foram desenvolvidos com o princípio **Safety-First**. Nenhum script destrutivo roda sem flags explícitas de confirmação. Por exemplo:
>
> - `oracle_housekeeper.py` **não apaga nada** por padrão. É preciso passar `--force --confirm-delete`.
> - `autorestart_goldengate.py` apenas **reinicia** processos já mortos, não interfere em processos saudáveis.
> - O `--dry-run` está disponível em todos os scripts para simular sem executar."

**Prova:**

```bash
# Isso NÃO apaga nada, apenas mostra o que faria:
python oracle_housekeeper.py --inventory /u01/app/oraInventory/ContentsXML/inventory.xml
# Output: [DRY-RUN] Removeria: /u01/app/oracle/product/12.1.0
```

---

### "E se a senha do banco estiver errada ou o banco estiver fora?"

**Resposta Técnica:**
> "Os scripts usam **tratamento de exceção** (`try/except`). Se a conexão falhar, o script termina com código de erro (exit code 1) e gera um log claro. Não há risco de 'travar' ou corromper dados."

**Prova:**

```python
except cx_Oracle.Error as error:
    logging.error(f"Erro ao conectar: {error}")
    sys.exit(1)  # Sai com código de erro
```

---

### "Como vocês garantem que não vão matar uma sessão importante?"

**Resposta Técnica:**
> "O script `oracle_healthcheck.py` tem lógica de proteção. Antes de sugerir ou matar uma sessão, ele verifica:
>
> 1. Se o usuário é `NULL` (processo de sistema Oracle).
> 2. Se o programa contém 'oracle' no nome (background process).
> Se qualquer condição for verdadeira, o script **não mata** e emite um warning."

**Prova:**

```python
if b_user is None or "oracle" in b_prog.lower():
    logging.warning("O bloqueador parece ser um processo de sistema. NÃO VOU MATAR.")
```

---

## 🟡 Categoria: Operação e Manutenção

### "Como agendamos isso no Control-M?"

**Resposta Técnica:**
> "O Control-M executa comandos shell. Basta configurar um job que chame o Python:
>
> ```bash
> /usr/bin/python3 /opt/oraex/automation/oracle_healthcheck.py --user SYS --dsn prod:1521/ORCL >> /var/log/oraex/healthcheck.log 2>&1
> ```
>
> O exit code (0 = sucesso, 1 = falha) pode ser usado para alertas no Control-M."

**Frequência Recomendada:**

| Script | Frequência |
| Script | Frequência |
| `oracle_healthcheck.py` | A cada 15 min |
| `check_tablespaces.py` | A cada 1 hora |
| `check_partitioning.py` | 1x ao dia (manhã) |
| `oracle_housekeeper.py` | 1x por semana |

---

### "Como atualizamos os scripts em 100+ servidores?"

**Resposta Técnica:**
> "Usamos **Ansible** para distribuição. O playbook `ansible_deploy_example.yml` já está pronto e faz:
>
> 1. Cria os diretórios necessários.
> 2. Copia os scripts Python.
> 3. Instala dependências (`cx_Oracle`).
> 4. Configura o crontab automaticamente."

---

### "E se precisarmos mudar uma regra de compliance?"

**Resposta Técnica:**
> "As regras estão centralizadas no método `check_compliance()` do `oracle_healthcheck.py`. Para adicionar um novo parâmetro, basta editar o dicionário `params_to_check`:
>
> ```python
> params_to_check = {
>     'recyclebin': 'OFF',
>     'nova_regra': 'VALOR_ESPERADO'  # Adiciona aqui
> }
> ```
>
> Depois, redistribui com Ansible."

---

## 🟢 Categoria: Benefícios e ROI

### "Qual o benefício real disso? Já temos scripts funcionando."

**Resposta Executiva:**
> "Os scripts legados funcionam, mas apresentam riscos operacionais:
>
> 1. **Falsos Positivos**: O grep de particionamento gera alertas errados. Nosso script faz parsing real da data.
> 2. **Dependência de Conhecimento**: Só quem escreveu o script sabe como ele funciona. Python modular é auto-documentado.
> 3. **Integração**: Saídas em JSON permitem integrar com Zabbix, Splunk e ServiceNow sem ajustes."

**ROI Estimado:**

| Problema | Tempo Atual | Tempo com Automação |
| Problema | Tempo Atual | Tempo com Automação |
| Analisar falso alerta de partição | 30 min | 0 (eliminado) |
| Verificar compliance manualmente | 1h por banco | 0 (automatizado) |
| Limpar homes antigas | 2h (com medo) | 5 min (script seguro) |

---

### "Isso funciona com Oracle 11g ou só 19c?"

**Resposta Técnica:**
> "Os scripts são compatíveis com Oracle 11g, 12c, 18c e 19c. Algumas features específicas (como `v$encryption_wallet`) só existem a partir do 12c, mas o código trata isso graciosamente com `try/except`."

---

### "Vocês têm testes? Como sabemos que funciona?"

**Resposta Técnica:**
> "Sim, temos uma suíte de testes unitários em `test_new_monitoring.py`. Usamos **mocks** para simular respostas do banco. Isso significa que podemos testar cenários de erro (banco fora, disco cheio) sem causar problemas reais."

**Prova:**

```bash
python run_all_tests.py
# Output: ✅ TODOS OS 9 TESTES PASSARAM!
```

---

## 💡 Dica Final

Se perguntarem algo que você não sabe:
> "Essa é uma excelente pergunta. Preciso validar esse cenário específico no ambiente de vocês antes de responder com precisão. Posso retornar com a resposta até [data]?"

**Nunca chute.** É melhor admitir que vai verificar do que dar uma resposta errada.
