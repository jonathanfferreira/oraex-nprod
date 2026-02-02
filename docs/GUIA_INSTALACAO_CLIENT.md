# Guia de Instalação: Oracle Client para Testes Locais

Para rodar os scripts que dependem de `cx_Oracle` (`oracle_healthcheck.py`, `check_partitioning.py`) localmente no seu Windows, você precisa do **Oracle Instant Client**.

## 1. Validar Pré-Requisitos

* **Python**: Você está usando Python **64-bit** (Validado ✅).
* **VS C++ Redistributable**: O Windows geralmente já tem, mas se der erro de DLL, precisará do [Microsoft Visual C++ 2015-2022 Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).

## 2. Passo a Passo

### Passo A: Baixar o Instant Client

1. Acesse: [Oracle Instant Client for Windows x64](https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html)
2. Baixe o pacote **"Basic Package"** (ex: `instantclient-basic-windows.x64-19.19.0.0.0dbru.zip`).
3. **Não** precisa baixar o SDK ou SQLPlus agora, só o Basic.

### Passo B: Extrair e Configurar

1. Crie uma pasta simples na raiz, exemplo: `C:\oracle`
2. Extraia o zip lá. Vai ficar algo como: `C:\oracle\instantclient_19_19`
3. **Importante**: Adicione essa pasta ao **PATH** do Windows.
    * Abra o menu Iniciar -> Digite "Variáveis de ambiente"
    * Edite as "Variáveis de Ambiente"
    * Em "Variáveis do Sistema" -> Encontre `Path` -> Editar -> Novo
    * Cole o caminho: `C:\oracle\instantclient_19_19`
    * Dê OK em tudo.

### Passo C: Instalar a Biblioteca

No seu terminal (Powershell):

```powershell
pip install cx_Oracle
```

## 3. Testar Conexão

Crie um arquivo chamado `teste_conexao.py`:

```python
import cx_Oracle
try:
    cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_19_19")
    print("✅ Cliente Oracle encontrado e carregado!")
except Exception as e:
    print(f"❌ Erro: {e}")
```

*(Nota: O `init_oracle_client` geralmente não é necessário se o PATH estiver certo, mas ajuda a testar).*
