"""
SCRIPT DE TESTE (SIMULAÇÃO)
---------------------------
Este código cria um "Banco de Mentirinha" (Mock) para testarmos o nosso robô
sem precisar instalar o Oracle de verdade agora.
"""
import sys
from unittest.mock import MagicMock

# 1. CRIANDO O MOCK (O "DUBLÊ" DO BANCO)
# Estamos criando uma biblioteca cx_Oracle falsa.
# Quando o script principal tentar usar 'cx_Oracle', ele vai usar essa nossa versão.
mock_cx_oracle = MagicMock()
sys.modules["cx_Oracle"] = mock_cx_oracle

# Agora podemos importar o script principal sem dar erro!
# (Nota: Precisamos adicionar o diretório ao path para importar corretamente)
sys.path.append('.')
from automacao.diagnosticos.oracle_healthcheck import OracleHealthCheck

# 2. DEFININDO O CENÁRIO DE TESTE
def testar_cenario_com_locks():
    print("\n>>> INICIANDO TESTE: CENÁRIO COM BLOQUEIO (LOCK) <<<\n")

    # Criamos um "Cursor" falso (o cara que busca os dados)
    mock_cursor = MagicMock()
    
    # Configurando o que o cursor vai responder quando perguntarem sobre Locks:
    # Retorna uma lista com uma sessão travada (SID 100 sendo bloqueada pela SID 200)
    mock_cursor.fetchall.side_effect = [
        # Primeira query: check_blocking_sessions (Retorna 1 lock)
        [(100, 1234, 'USUARIO_VITIMA', 'ACTIVE', 200, 'TABELA_FINANCEIRA')], 
        
        # Segunda query: check_flashback_compliance (Retorna tabela ok)
        [('HR', 'EMPLOYEES', 'FB_ARCHIVE_1', 30)],
        
        # Terceira query: check_ash_top_waits (Retorna evento de espera)
        [('enq: TX - row lock contention', 50)]
    ]

    # Configurando o que ele responde quando pedimos detalhes do bloqueador (SID 200)
    # Retorna: SID, Serial, User, Program, Status, SQL_ID
    mock_cursor.fetchone.return_value = (200, 9999, 'USUARIO_TRAVADO', 'sqlplus.exe', 'INACTIVE', 'abc12345')

    # Ensinando a conexão falsa a retornar o nosso cursor falso
    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_cx_oracle.connect.return_value = mock_connection

    # 3. RODANDO O ROBÔ
    print("1. Criando o Robô...")
    robo = OracleHealthCheck("system", "senha", "localhost/orcl")
    
    print("2. Mandando conectar (Fake)...")
    robo.connect()
    
    print("3. Verificando Locks...")
    # Aqui o robô vai achar que tem lock e vai tentar "matar" ou avisar, dependendo da config.
    # Vamos rodar com auto_kill=True para ver se ele tenta matar.
    robo.check_blocking_sessions(auto_kill=True)
    
    # 4. VERIFICANDO O RESULTADO
    # Vamos perguntar pro Mock: "O método execute foi chamado com o comando KILL?"
    calls = mock_cursor.execute.call_args_list
    
    kill_command_found = False
    for call in calls:
        # call.args[0] é o SQL executado
        if "ALTER SYSTEM KILL SESSION" in str(call.args):
            print(f"\n[SUCESSO] O Robô tentou matar a sessão! Comando: {call.args[0]}")
            kill_command_found = True
    
    if not kill_command_found:
        print("\n[FALHA] O Robô NÃO tentou matar a sessão.")

if __name__ == "__main__":
    testar_cenario_com_locks()
