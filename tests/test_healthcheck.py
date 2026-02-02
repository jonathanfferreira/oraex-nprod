import unittest
import sys
from unittest.mock import MagicMock, patch

# 1. SETUP DO MOCK ANTES DO IMPORT
# Precisamos enganar o Python achando que o cx_Oracle existe e é um Mock
mock_cx_oracle = MagicMock()
sys.modules["cx_Oracle"] = mock_cx_oracle

# Configurar o Error para ser uma exception normal, senão o try/except não pega
class MockDatabaseError(Exception):
    def __init__(self, message, code=None):
        self.args = (MagicMock(code=code),) if code else ()
        self.message = message
    def __str__(self):
        return self.message
mock_cx_oracle.Error = MockDatabaseError

# Agora importamos o módulo a ser testado
# Adiciona diretório raiz ao path para encontrar o módulo 'automacao'
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from automacao.diagnosticos.oracle_healthcheck import (
    BlockingSessionsChecker, 
    CheckStatus, 
    ConnectionConfig,
    OracleHealthCheck
)

class TestBlockingSessionsChecker(unittest.TestCase):
    
    def setUp(self):
        self.checker = BlockingSessionsChecker()
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    def test_run_no_locks(self):
        """Testa cenário onde não há bloqueios (retorno vazio)."""
        # Configura o cursor para retornar lista vazia
        self.mock_cursor.fetchall.return_value = []
        
        result = self.checker.run(self.mock_connection)
        
        self.assertEqual(result.status, CheckStatus.OK)
        self.assertEqual(result.name, "Blocking Sessions")
        self.assertIn("Nenhuma sessão", result.message)

    def test_run_with_locks(self):
        """Testa cenário com bloqueios críticos."""
        # Configura cursor para retornar 1 linha de bloqueio
        # Colunas esperadas: sid, serial#, username, status, blocking_session, object_name
        self.mock_cursor.fetchall.return_value = [
            (100, 1234, 'SCOTT', 'ACTIVE', 200, 'EMP_TABLE')
        ]
        
        result = self.checker.run(self.mock_connection)
        
        self.assertEqual(result.status, CheckStatus.CRITICAL)
        self.assertIn("1 sessão(ões) bloqueada(s)", result.message)
        self.assertEqual(len(result.details['sessions']), 1)
        self.assertEqual(result.details['sessions'][0]['sid'], 100)

    def test_database_error(self):
        """Testa comportamento quando ocorre erro no banco."""
        # Configura cursor para lançar erro
        self.mock_cursor.execute.side_effect = mock_cx_oracle.Error("Falha de conexão")
        
        result = self.checker.run(self.mock_connection)
        
        self.assertEqual(result.status, CheckStatus.ERROR)
        self.assertIn("Falha de conexão", result.message)


class TestOracleHealthCheckOrchestrator(unittest.TestCase):
    
    def setUp(self):
        self.config = ConnectionConfig("user", "pass", "dsn")
        self.orchestrator = OracleHealthCheck(self.config)
    
    @patch('automacao.diagnosticos.oracle_healthcheck.cx_Oracle.connect')
    def test_run_all_checks_success(self, mock_connect):
        """Testa fluxo completo do orquestrador."""
        # Mock da conexão
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Injeta mocks para os checkers internos para não depender da implementação deles
        # Vamos substituir a lista de checkers real por mocks que retornam OK
        mock_checker = MagicMock()
        mock_checker.run.return_value = MagicMock(status=CheckStatus.OK, name="Mock Check", message="OK")
        self.orchestrator.checkers = [mock_checker]
        
        results = self.orchestrator.run_all_checks()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, CheckStatus.OK)
        # Verifica se tentou conectar
        mock_connect.assert_called_once()


if __name__ == '__main__':
    unittest.main()
