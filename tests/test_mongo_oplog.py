import unittest
import sys
import os
import logging
from unittest.mock import MagicMock, patch
from io import StringIO
from datetime import datetime, timedelta

# Setup path para importar módulos da raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
from automacao.mongodb.monitoramento import check_oplog_lag

class TestMongoOplogLag(unittest.TestCase):
    
    def setUp(self):
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.INFO)

    def tearDown(self):
        logging.getLogger().removeHandler(self.handler)

    @patch("automacao.mongodb.monitoramento.check_oplog_lag.pymongo.MongoClient")
    def test_high_lag_detection(self, mock_client_cls):
        """Testa detecção de Lag Alto."""
        mock_client = MagicMock()
        mock_db = mock_client.admin
        
        now = datetime.utcnow()
        past = now - timedelta(seconds=100) # 100s lag
        
        mock_db.command.return_value = {
            "members": [
                {"name": "primary", "stateStr": "PRIMARY", "optimeDate": now},
                {"name": "secondary", "stateStr": "SECONDARY", "optimeDate": past}
            ]
        }
        mock_client_cls.return_value = mock_client
        
        # Oplog window ok (evita erro no teste de lag)
        # Mock do client.local.oplog.rs.find_one
        mock_oplog = mock_client.local.oplog.rs
        ts_mock = MagicMock()
        ts_mock.__getitem__.return_value.time = 0
        mock_oplog.find_one.return_value = ts_mock # Retorna 0 diff, mas ok.
        
        # Limite 10s -> Deve falhar (100s lag)
        result = check_oplog_lag.check_lag_and_oplog("uri", 10, 24)
        
        self.assertFalse(result)
        self.assertIn("HIGH LAG", self.log_capture.getvalue())

    @patch("automacao.mongodb.monitoramento.check_oplog_lag.pymongo.MongoClient")
    def test_short_oplog_window(self, mock_client_cls):
        """Testa detecção de Janela de Oplog Curta."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {
            "members": [{"stateStr": "PRIMARY", "optimeDate": datetime.utcnow()}]
        }
        mock_client_cls.return_value = mock_client
        
        # Mudar comportamento do get_oplog_window (mockar a helper ou os finds)
        # Vamos mockar os retornos do find_one
        oplog_coll = mock_client.local.oplog.rs
        
        # T1 (First) = 10:00, T2 (Last) = 11:00 -> 1h Window
        t1 = MagicMock()
        t1.time = 10000
        first_doc = {'ts': t1}
        
        t2 = MagicMock()
        t2.time = 13600 # 3600s = 1h depois
        last_doc = {'ts': t2}
        
        # find_one chamado duas vezes: sort 1 (first), sort -1 (last)
        oplog_coll.find_one.side_effect = [first_doc, last_doc]

        # Min 24h -> Deve falhar (1h window)
        result = check_oplog_lag.check_lag_and_oplog("uri", 10, 24)
        
        self.assertFalse(result)
        self.assertIn("SHORT OPLOG", self.log_capture.getvalue())
        self.assertIn("1.0h", self.log_capture.getvalue())

if __name__ == "__main__":
    unittest.main()
