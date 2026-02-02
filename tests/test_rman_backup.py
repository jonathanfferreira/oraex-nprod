"""
Testes unitários para rman_backup_manager.py
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from automacao.backup.rman_backup_manager import (
    BackupType,
    BackupJob,
    BackupResult,
    RMANExecutor,
    RMANBackupManager
)


class TestBackupType(unittest.TestCase):
    """Testes para enum BackupType."""

    def test_backup_types_exist(self):
        self.assertEqual(BackupType.FULL.value, "full")
        self.assertEqual(BackupType.INCREMENTAL_L0.value, "incremental_l0")
        self.assertEqual(BackupType.INCREMENTAL_L1.value, "incremental_l1")
        self.assertEqual(BackupType.ARCHIVELOG.value, "archivelog")


class TestBackupJob(unittest.TestCase):
    """Testes para dataclass BackupJob."""

    def test_backup_job_creation(self):
        job = BackupJob(
            session_key=123,
            start_time=datetime(2026, 2, 1, 22, 0),
            end_time=datetime(2026, 2, 1, 23, 0),
            status="COMPLETED",
            input_type="DB FULL",
            output_bytes=10737418240,  # 10 GB
            elapsed_seconds=3600
        )
        
        self.assertEqual(job.session_key, 123)
        self.assertEqual(job.status, "COMPLETED")
    
    def test_backup_job_to_dict(self):
        job = BackupJob(
            session_key=1,
            start_time=datetime(2026, 2, 1, 22, 0),
            end_time=datetime(2026, 2, 1, 23, 0),
            status="COMPLETED",
            input_type="DB FULL",
            output_bytes=1073741824,  # 1 GB
            elapsed_seconds=3600
        )
        
        result = job.to_dict()
        self.assertEqual(result["output_gb"], 1.0)
        self.assertEqual(result["elapsed_minutes"], 60.0)


class TestBackupResult(unittest.TestCase):
    """Testes para dataclass BackupResult."""

    def test_successful_result(self):
        result = BackupResult(
            success=True,
            backup_type="full",
            message="Backup concluído",
            start_time=datetime.now()
        )
        
        self.assertTrue(result.success)
        self.assertIsNone(result.error)
    
    def test_failed_result(self):
        result = BackupResult(
            success=False,
            backup_type="full",
            message="Backup falhou",
            start_time=datetime.now(),
            error="ORA-12345"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "ORA-12345")


class TestRMANExecutor(unittest.TestCase):
    """Testes para RMANExecutor."""

    def test_connect_string_without_catalog(self):
        executor = RMANExecutor(
            oracle_home="/u01/app/oracle",
            oracle_sid="ORCL"
        )
        
        connect_str = executor._build_connect_string()
        self.assertEqual(connect_str, "target /")
    
    def test_connect_string_with_catalog(self):
        executor = RMANExecutor(
            oracle_home="/u01/app/oracle",
            oracle_sid="ORCL",
            catalog_conn="rman_user/pass@catalog"
        )
        
        connect_str = executor._build_connect_string()
        self.assertIn("catalog", connect_str)


class TestRMANBackupManager(unittest.TestCase):
    """Testes para RMANBackupManager."""

    def setUp(self):
        self.executor = MagicMock(spec=RMANExecutor)
        self.manager = RMANBackupManager(
            executor=self.executor,
            backup_dest="/u02/backup"
        )

    def test_run_backup_success(self):
        self.executor.execute.return_value = (True, "Backup completed successfully")
        
        result = self.manager.run_backup(BackupType.FULL)
        
        self.assertTrue(result.success)
        self.assertEqual(result.backup_type, "full")
        self.executor.execute.assert_called_once()

    def test_run_backup_failure(self):
        self.executor.execute.return_value = (False, "RMAN-00571: Error")
        
        result = self.manager.run_backup(BackupType.FULL)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)

    def test_backup_scripts_exist(self):
        # Verificar que todos os tipos têm scripts
        for backup_type in [BackupType.FULL, BackupType.INCREMENTAL_L0, 
                            BackupType.INCREMENTAL_L1, BackupType.ARCHIVELOG]:
            self.assertIn(backup_type, self.manager.BACKUP_SCRIPTS)


if __name__ == '__main__':
    unittest.main()
