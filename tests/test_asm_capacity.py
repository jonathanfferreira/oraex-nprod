"""
Testes unitários para asm_capacity_report.py
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime
from pathlib import Path
import tempfile
import json

sys.path.insert(0, os.path.dirname(__file__))

from automacao.monitoramento.asm_capacity_report import (
    DiskGroup,
    Disk,
    ASMCapacityChecker,
    CapacityHistoryManager,
    generate_report
)


class TestDiskGroup(unittest.TestCase):
    """Testes para dataclass DiskGroup."""

    def setUp(self):
        self.dg = DiskGroup(
            name="DATA",
            total_mb=2097152,  # 2 TB
            free_mb=524288,    # 512 GB
            required_mirror_free_mb=0,
            usable_file_mb=524288,
            state="MOUNTED",
            type="EXTERN",
            disk_count=4
        )

    def test_used_mb_calculation(self):
        self.assertEqual(self.dg.used_mb, 2097152 - 524288)

    def test_used_pct_calculation(self):
        expected_pct = round(((2097152 - 524288) / 2097152) * 100, 1)
        self.assertEqual(self.dg.used_pct, expected_pct)

    def test_gb_conversions(self):
        self.assertEqual(self.dg.total_gb, round(2097152 / 1024, 2))
        self.assertEqual(self.dg.free_gb, round(524288 / 1024, 2))

    def test_to_dict(self):
        result = self.dg.to_dict()
        self.assertEqual(result["name"], "DATA")
        self.assertEqual(result["state"], "MOUNTED")
        self.assertIn("used_pct", result)


class TestDisk(unittest.TestCase):
    """Testes para dataclass Disk."""

    def test_disk_creation(self):
        disk = Disk(
            name="DATA_0001",
            path="/dev/oracleasm/disks/DATA1",
            group_name="DATA",
            total_mb=524288,
            free_mb=131072,
            state="NORMAL",
            mode_status="ONLINE"
        )
        
        self.assertEqual(disk.name, "DATA_0001")
        self.assertEqual(disk.group_name, "DATA")

    def test_disk_used_pct(self):
        disk = Disk(
            name="DATA_0001",
            path="/dev/disk1",
            group_name="DATA",
            total_mb=1000,
            free_mb=250,
            state="NORMAL",
            mode_status="ONLINE"
        )
        
        self.assertEqual(disk.used_pct, 75.0)


class TestASMCapacityChecker(unittest.TestCase):
    """Testes para ASMCapacityChecker."""

    def test_mock_data_returned_without_oracle(self):
        checker = ASMCapacityChecker("/")
        diskgroups = checker.get_diskgroups()
        
        # Deve retornar dados mock quando cx_Oracle não disponível
        self.assertIsInstance(diskgroups, list)
        if diskgroups:  # Se retornou mock
            self.assertTrue(all(isinstance(dg, DiskGroup) for dg in diskgroups))


class TestCapacityHistoryManager(unittest.TestCase):
    """Testes para CapacityHistoryManager."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = Path(self.temp_dir) / "asm_history.json"
        self.manager = CapacityHistoryManager(self.history_file)

    def test_save_snapshot(self):
        diskgroups = [
            DiskGroup("DATA", 2000, 500, 0, 500, "MOUNTED", "EXTERN", 4),
            DiskGroup("FRA", 1000, 300, 0, 300, "MOUNTED", "EXTERN", 2)
        ]
        
        self.manager.save_snapshot(diskgroups)
        
        self.assertTrue(self.history_file.exists())
        
        with open(self.history_file) as f:
            history = json.load(f)
        
        self.assertEqual(len(history), 2)

    def test_predict_with_insufficient_data(self):
        # Sem dados, deve retornar None
        result = self.manager.predict_days_until_full("DATA")
        self.assertIsNone(result)


class TestGenerateReport(unittest.TestCase):
    """Testes para função generate_report."""

    def test_report_with_alert(self):
        diskgroups = [
            DiskGroup("DATA", 1000, 100, 0, 100, "MOUNTED", "EXTERN", 4),  # 90% usado
        ]
        
        report = generate_report(diskgroups, threshold=80)
        
        self.assertEqual(len(report["alerts"]), 1)
        self.assertEqual(report["alerts"][0]["group"], "DATA")

    def test_report_without_alert(self):
        diskgroups = [
            DiskGroup("DATA", 1000, 500, 0, 500, "MOUNTED", "EXTERN", 4),  # 50% usado
        ]
        
        report = generate_report(diskgroups, threshold=80)
        
        self.assertEqual(len(report["alerts"]), 0)

    def test_report_summary(self):
        diskgroups = [
            DiskGroup("DATA", 2000, 1000, 0, 1000, "MOUNTED", "EXTERN", 4),
            DiskGroup("FRA", 1000, 500, 0, 500, "MOUNTED", "EXTERN", 2)
        ]
        
        report = generate_report(diskgroups, threshold=80)
        
        summary = report["summary"]
        self.assertEqual(summary["total_groups"], 2)
        self.assertGreater(summary["total_capacity_gb"], 0)


if __name__ == '__main__':
    unittest.main()
