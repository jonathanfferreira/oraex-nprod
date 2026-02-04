# Guia de Implementação e Perguntas Frequentes (FAQ)

Este documento reúne respostas para as dúvidas sobre a implantação dos scripts de monitoramento na infraestrutura da Getnet e explica o papel do Parasoft.

## 1. Desafios e Riscos na Implementação (Getnet)

Ao levar esses scripts do nosso ambiente de desenvolvimento para os servidores reais (On-Premises ou Cloud) da Getnet, você pode encontrar os seguintes obstáculos:

### A. Versão do Python

* **Risco**: Servidores Oracle antigos (RHEL 6/7, AIX, Solaris) muitas vezes têm apenas **Python 2.6 ou 2.7** instalado por padrão. Nossos scripts foram escritos em **Python 3**.
* **Solução**: Verificar a versão instalada (`python --version` ou `python3 --version`). Se não tiver Python 3, pode ser necessário solicitar a instalação via RPM ou usar uma versão portátil (Miniconda) se houver permissão.

### B. Dependência `cx_Oracle`

* **Risco**: O `cx_Oracle` precisa das bibliotecas do *Oracle Client* ou *Instant Client*. Nos servidores de banco, o Oracle Home já existe, mas configurar as variáveis de ambiente (`LD_LIBRARY_PATH`, `ORACLE_HOME`) para o Python enxergar corretamente pode ser chato.
* **Solução**: Garantir que o usuário que executa o script (ex: `oracle`) tenha as variáveis carregadas (`.bash_profile`).

### C. Permissões de Rede e Firewall

* **Risco**: Se você rodar o script de um servidor de monitoramento dedicado (e não do próprio DB Server), pode haver bloqueio de firewall na porta 1521.
* **Solução**: Validar conectividade via `sqlplus` ou `tnsping` antes de culpar o script Python.

### D. Variáveis Hardcoded vs. Argumentos

* **Alteração Necessária**: Nossos scripts usam `argparse` para receber usuário/senha, mas alguns caminhos de log podem precisar de ajuste se a estrutura de diretórios `/u01/app/...` for diferente em algums servidores (embora o BOOK DBA padronize isso, a realidade pode variar).

---

## 2. O que alterar no código para Deploy?

Idealmente, **NADA** na lógica. O código foi feito para ser agnóstico. O que você vai alterar é **COMO** você chama o código:

1. **Connection Strings (DSN)**:
    * No teste usamos mocks. Na produção, você passará o DSN real no comando:
    * `python oracle_healthcheck.py --dsn "10.23.9.6:1521/FINLACSRVPRD" ...`
2. **Agendamento (Crontab/Control-M)**:
    * Os scripts não rodam sozinhos. Você precisará criar as entradas no Crontab ou Jobs no Control-M (como mencionado no Item 17 do Book DBA).

---

## 3. O que é Parasoft?

A Getnet informou que usará o **Parasoft**. A Parasoft é uma empresa famosa por ferramentas de **Qualidade e Teste de Software**. No contexto de um projeto "NPROD" (Novos Produtos/Projetos), eles provavelmente estão usando uma destas duas ferramentas:

1. **Parasoft Jtest / C++test (Static Analysis)**:
    * **O que faz**: "Lê" o código (Java, C, Python) procurando vulnerabilidades de segurança (OWASP), bugs potenciais e "code smells".
    * **Impacto pra você**: Eles podem rodar isso nos seus scripts e reclamar se houver senhas hardcoded (não temos), tratamento de exceção genérico (`except Exception:`), ou falta de comentários. Nossos scripts estão bem estruturados, mas podem apontar "falsos positivos".

2. **Parasoft Virtualize / SOAtest**:
    * **O que faz**: Criação de ambientes virtuais de teste (Service Virtualization). Se o "NPROD" envolve APIs integrando com o Oracle, eles podem usar o Parasoft para simular chamadas ao banco ou simular o próprio banco para testar a aplicação.
    * **Impacto pra você**: Pode ser que usem o Parasoft para validar se seus scripts de monitoramento estão gerando os alertas corretos sem precisar derrubar o banco real (similar aos nossos Mocks, mas "Enterprise").

**Resumo**: Não se preocupe. Se for análise estática, ajustamos o código conforme o relatório deles. Se for virtualização, apenas ajuda a validar seu trabalho.
