"""
Testes unitários para oracle_housekeeper.py (versão refatorada com classes).
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from automacao.sustentacao.oracle_housekeeper import (
    OracleHome,
    ProcessChecker,
    InventoryParser,
    OracleHousekeeper
)


class TestOracleHome(unittest.TestCase):
    """Testes para a dataclass OracleHome."""

    def test_oracle_home_creation(self):
        home = OracleHome(
            name="OraDB19Home1",
            location=Path("/u01/app/oracle/product/19.0.0/dbhome_1"),
            is_removed=False
        )
        self.assertEqual(home.name, "OraDB19Home1")
        self.assertFalse(home.is_removed)

    def test_oracle_home_display_name(self):
        home = OracleHome(
            name="OraDB19Home1",
            location=Path("/u01/app/oracle"),
            is_removed=False
        )
        self.assertIn("OraDB19Home1", home.display_name)
        self.assertIn("oracle", home.display_name)


class TestProcessChecker(unittest.TestCase):
    """Testes para ProcessChecker."""

    @patch("subprocess.run")
    def test_has_active_processes_true(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"oracle 1234 1 0 10:00 ? 00:00:00 /u01/home/bin/oracle"
        mock_run.return_value = mock_result

        result = ProcessChecker.has_active_processes(Path("/u01/home"))
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_has_active_processes_false(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_run.return_value = mock_result

        result = ProcessChecker.has_active_processes(Path("/u01/home"))
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_has_active_processes_error_returns_true(self, mock_run):
        mock_run.side_effect = Exception("Command failed")

        result = ProcessChecker.has_active_processes(Path("/u01/home"))
        self.assertTrue(result)  # Fail-safe: assume há processos


class TestInventoryParser(unittest.TestCase):
    """Testes para InventoryParser."""

    @patch("xml.etree.ElementTree.parse")
    @patch.object(Path, 'exists', return_value=True)
    def test_parse_inventory(self, mock_exists, mock_parse):
        root = MagicMock()
        home1 = MagicMock()
        home1.get.side_effect = lambda k, d=None: {
            "NAME": "OraDB19Home1",
            "LOC": "/u01/app/oracle/product/19.0.0/dbhome_1",
            "REMOVED": "F"
        }.get(k, d)

        home2 = MagicMock()
        home2.get.side_effect = lambda k, d=None: {
            "NAME": "OraDB12Home1",
            "LOC": "/u01/app/oracle/product/12.1.0/dbhome_1",
            "REMOVED": "T"
        }.get(k, d)

        root.findall.return_value = [home1, home2]
        mock_parse.return_value.getroot.return_value = root

        homes = InventoryParser.parse(Path("/fake/inventory.xml"))

        self.assertEqual(len(homes), 2)
        self.assertFalse(homes[0].is_removed)
        self.assertTrue(homes[1].is_removed)

    @patch.object(Path, 'exists', return_value=False)
    def test_parse_inventory_file_not_found(self, mock_exists):
        homes = InventoryParser.parse(Path("/fake/inventory.xml"))
        self.assertEqual(homes, [])


class TestOracleHousekeeper(unittest.TestCase):
    """Testes para OracleHousekeeper."""

    def setUp(self):
        self.housekeeper = OracleHousekeeper(
            inventory_path=Path("/fake/inventory.xml"),
            dry_run=True
        )

    def test_get_detached_homes(self):
        self.housekeeper.homes = [
            OracleHome("Home1", Path("/u01/home1"), is_removed=False),
            OracleHome("Home2", Path("/u01/home2"), is_removed=True),
            OracleHome("Home3", Path("/u01/home3"), is_removed=True),
        ]
        detached = self.housekeeper.get_detached_homes()
        self.assertEqual(len(detached), 2)

    @patch("shutil.rmtree")
    @patch.object(ProcessChecker, 'has_active_processes', return_value=False)
    @patch.object(Path, 'exists', return_value=True)
    def test_cleanup_home_dry_run(self, mock_exists, mock_check, mock_rm):
        home = OracleHome("TestHome", Path("/u01/test"), is_removed=True)

        with self.assertLogs(level='INFO') as cm:
            result = self.housekeeper.cleanup_home(home)

        self.assertFalse(result)  # Dry-run não remove
        self.assertTrue(any("DRY-RUN" in log for log in cm.output))
        mock_rm.assert_not_called()

    @patch("shutil.rmtree")
    @patch.object(ProcessChecker, 'has_active_processes', return_value=False)
    @patch.object(Path, 'exists', return_value=True)
    def test_cleanup_home_real(self, mock_exists, mock_check, mock_rm):
        housekeeper = OracleHousekeeper(
            inventory_path=Path("/fake/inventory.xml"),
            dry_run=False  # Modo real
        )
        home = OracleHome("TestHome", Path("/u01/test"), is_removed=True)

        with self.assertLogs(level='INFO') as cm:
            result = housekeeper.cleanup_home(home)

        self.assertTrue(result)
        self.assertTrue(any("DELETE" in log for log in cm.output))
        mock_rm.assert_called_once()

    @patch("shutil.rmtree")
    @patch.object(ProcessChecker, 'has_active_processes', return_value=True)
    @patch.object(Path, 'exists', return_value=True)
    def test_cleanup_home_aborts_with_active_processes(self, mock_exists, mock_check, mock_rm):
        housekeeper = OracleHousekeeper(
            inventory_path=Path("/fake/inventory.xml"),
            dry_run=False
        )
        home = OracleHome("TestHome", Path("/u01/test"), is_removed=True)

        with self.assertLogs(level='ERROR') as cm:
            result = housekeeper.cleanup_home(home)

        self.assertFalse(result)
        self.assertTrue(any("ABORT" in log for log in cm.output))
        mock_rm.assert_not_called()


if __name__ == '__main__':
    unittest.main()
