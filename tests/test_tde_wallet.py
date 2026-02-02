"""
Testes unitários para TDE Wallet Check (Mock)
"""
import unittest
from unittest.mock import MagicMock
import sys
import os

# Adiciona diretório pai
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automacao.diagnosticos.oracle_healthcheck import (
    TDEWalletChecker, CheckStatus, CheckResult
)

class TestTDEWallet(unittest.TestCase):
    
    def setUp(self):
        self.checker = TDEWalletChecker()
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

    def test_wallet_not_configured(self):
        # Setup: Query returns empty (no wallet found)
        self.mock_cursor.fetchall.return_value = []
        
        result = self.checker.run(self.mock_conn)
        
        self.assertEqual(result.status, CheckStatus.OK)
        self.assertIn("não configurado", result.message)

    def test_wallet_open_autologin(self):
        # Setup: OPEN, AUTOLOGIN
        self.mock_cursor.fetchall.return_value = [("FILE", "OPEN", "AUTOLOGIN")]
        
        result = self.checker.run(self.mock_conn)
        
        self.assertEqual(result.status, CheckStatus.OK)
        self.assertIn("Auto Login ativado", result.message)

    def test_wallet_closed(self):
        # Setup: CLOSED
        self.mock_cursor.fetchall.return_value = [("FILE", "CLOSED", "UNKNOWN")]
        
        result = self.checker.run(self.mock_conn)
        
        self.assertEqual(result.status, CheckStatus.CRITICAL)
        self.assertIn("NÃO está aberta", result.message)

    def test_wallet_no_master_key(self):
        # Setup: OPEN_NO_MASTER_KEY
        self.mock_cursor.fetchall.return_value = [("FILE", "OPEN_NO_MASTER_KEY", "PASSWORD")]
        
        result = self.checker.run(self.mock_conn)
        
        self.assertEqual(result.status, CheckStatus.WARNING)
        self.assertIn("sem Master Key", result.message)

if __name__ == '__main__':
    unittest.main()
