import unittest
import sys
import os
import shutil
import tempfile
import time
import logging
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, patch

# Path Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock de dependencias externas (CLI e Drivers)
# Precisamos mockar submodulos ANTES de importar os scripts
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from automacao.mongodb.diagnosticos import check_health
from automacao.mongodb.monitoramento import analyze_indexes
from automacao.mongodb.backup import mongo_backup_manager

class TestMongoIntegration(unittest.TestCase):
    
    def setUp(self):
        # Temp dir para backup
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("automacao.mongodb.diagnosticos.check_health.setup_logging")
    @patch("automacao.mongodb.monitoramento.check_oplog_lag.get_oplog_window")
    @patch("automacao.mongodb.diagnosticos.check_health.check_replica_set")
    def test_healthcheck_consolidated(self, mock_rs_check, mock_get_window, mock_setup_log):
        """Testa o Healthcheck consolidado."""
        # Setup Global Mock
        mock_pymongo_client = sys.modules["pymongo"].MongoClient
        
        # Instance 1: Healthcheck Client
        mock_health_instance = MagicMock()
        mock_health_instance.admin.command.side_effect = [
            {"ok": 1}, # Ping
            {"connections": {"current": 10, "available": 100}}, # ServerStatus
        ]
        # Profile hack
        mock_health_instance.get_database.return_value.command.return_value = {"was": 0, "slowms": 100}

        # Instance 2: Oplog Client
        mock_oplog_instance = MagicMock()
        mock_oplog_instance.admin.command.return_value = {
            "members": [{"stateStr": "PRIMARY", "name": "p", "optimeDate": datetime(2023,1,2,12,0,0)}]
        }

        # Set Side Effect
        mock_pymongo_client.side_effect = [mock_health_instance, mock_oplog_instance]
        
        # Mocks Logic
        mock_rs_check.return_value = True 
        mock_get_window.return_value = 25.0
        
        # Capture Logs
        # Como check_health.main() chama sys.exit, testaremos as funções individuais ou faremos um patch no sys.exit
        
        # Capture Logs
        with patch("sys.exit") as mock_exit:
            # Mock Logging
            with patch("sys.stderr", new=tempfile.TemporaryFile(mode='w+t')) as fake_stderr:
                with patch("sys.argv", ["check_health.py", "--uri", "mongo://uri"]):
                    # Setup basic logging to capture to string
                    logger = logging.getLogger()
                    capture = StringIO()
                    handler = logging.StreamHandler(capture)
                    logger.addHandler(handler)
                    
                    try:
                        check_health.main()
                    finally:
                        logger.removeHandler(handler)
                    
                    logs = capture.getvalue()
                    with open("tests/debug_logs.txt", "w", encoding="utf-8") as f:
                        f.write(logs)
                    
                    # Check Calls
                    mock_rs_check.assert_called()
                    mock_exit.assert_called_with(0)

    @patch("automacao.mongodb.monitoramento.analyze_indexes.pymongo.MongoClient")
    def test_analyze_indexes_unused(self, mock_client_cls):
        """Testa alerta de Índices Não Usados."""
        mock_client = mock_client_cls.return_value
        mock_client.list_database_names.return_value = ["app_db"]
        mock_db = mock_client["app_db"]
        mock_db.list_collection_names.return_value = ["users"]
        
        # Pipeline result with 0 ops
        mock_db["users"].aggregate.return_value = [
            {"name": "idx_unused", "accesses": {"ops": 0, "since": "2023"}}
        ]
        
        result = analyze_indexes.analyze_indexes("uri")
        self.assertFalse(result) # False = Encontrou problemas

    @patch("subprocess.run")
    def test_backup_manager_success(self, mock_run):
        """Testa o comando de backup e limpeza."""
        mock_run.return_value.returncode = 0
        
        # Cria um backup "antigo" no diretório
        old_backup = os.path.join(self.test_dir, "backup_20200101_000000")
        os.makedirs(old_backup)
        
        # Volta o relógio do arquivo para 8 dias atrás
        eight_days_ago = time.time() - (8 * 86400)
        os.utime(old_backup, (eight_days_ago, eight_days_ago))
        
        # Executa Manager
        mongo_backup_manager.main = lambda: None # Bypass main argparsing logic, testing functions directly?
        # Better: Test run_backup and clean_old_backups
        
        success = mongo_backup_manager.run_backup("uri", self.test_dir)
        self.assertTrue(success)
        mock_run.assert_called()
        
        mongo_backup_manager.clean_old_backups(self.test_dir, 7)
        
        # Verifica se o antigo sumiu
        self.assertFalse(os.path.exists(old_backup))

if __name__ == "__main__":
    unittest.main()
