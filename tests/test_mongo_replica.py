import unittest
import sys
import os
import json
import logging
from unittest.mock import MagicMock, patch
from io import StringIO

# Ajusta path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo antes de importar o script, pois o script tenta importar no top-level/try-except
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from automacao.mongodb.monitoramento import check_replica_set

class TestMongoReplicaSet(unittest.TestCase):
    
    def setUp(self):
        # Captura Logs
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.INFO)

    def tearDown(self):
        logging.getLogger().removeHandler(self.handler)

    @patch("automacao.mongodb.monitoramento.check_replica_set.pymongo.MongoClient")
    def test_healthy_replica_set(self, mock_client_cls):
        """Testa cluster saudável (1 Primary, 1 Secondary)."""
        # Mock Client e Command Response
        mock_client = MagicMock()
        mock_db = mock_client.admin
        
        # Resposta do replSetGetStatus
        mock_db.command.return_value = {
            "set": "rs0",
            "members": [
                {"name": "mongo1", "stateStr": "PRIMARY", "health": 1},
                {"name": "mongo2", "stateStr": "SECONDARY", "health": 1}
            ]
        }
        mock_client_cls.return_value = mock_client
        
        # Executa a função de checagem direta
        healthy = check_replica_set.check_replica_set(mock_client)
        
        # Validação
        self.assertTrue(healthy)
        output = self.log_capture.getvalue()
        self.assertIn("mongo1 -> [PRIMARY] (Health: 1)", output)
        self.assertIn("mongo2 -> [SECONDARY] (Health: 1)", output)

    @patch("automacao.mongodb.monitoramento.check_replica_set.pymongo.MongoClient")
    def test_no_primary(self, mock_client_cls):
        """Testa cluster crítico (Sem Primary)."""
        mock_client = MagicMock()
        mock_db = mock_client.admin
        
        mock_db.command.return_value = {
            "set": "rs0",
            "members": [
                {"name": "mongo1", "stateStr": "SECONDARY", "health": 1},
                {"name": "mongo2", "stateStr": "SECONDARY", "health": 1}
            ]
        }
        mock_client_cls.return_value = mock_client
        
        healthy = check_replica_set.check_replica_set(mock_client)
        
        self.assertFalse(healthy)
        output = self.log_capture.getvalue()
        self.assertIn("NENHUM PRIMARY ENCONTRADO", output)

if __name__ == "__main__":
    unittest.main()
