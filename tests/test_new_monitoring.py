"""
ORAEX - Test Suite
------------------
Testes unitários para os scripts de automação Oracle.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path

# Import classes refatoradas
from automacao.diagnosticos.oracle_healthcheck import (
    CheckStatus, CheckResult, BlockingSessionsChecker, 
    RMANStatusChecker, ComplianceChecker
)
from automacao.monitoramento.check_partitioning import (
    PartitionInfo, PartitionChecker
)
from automacao.monitoramento.check_tablespaces import (
    TablespaceInfo, TablespaceChecker
)
from automacao.sustentacao.oracle_housekeeper import (
    OracleHome, InventoryParser
)
from automacao.configuracao.create_application_service import (
    generate_service_name
)


class TestCheckStatus(unittest.TestCase):
    """Testes para enum CheckStatus."""
    
    def test_status_values(self):
        self.assertEqual(CheckStatus.OK.value, "OK")
        self.assertEqual(CheckStatus.CRITICAL.value, "CRITICAL")


class TestCheckResult(unittest.TestCase):
    """Testes para dataclass CheckResult."""
    
    def test_create_result(self):
        result = CheckResult(
            name="Test",
            status=CheckStatus.OK,
            message="All good"
        )
        self.assertEqual(result.name, "Test")
        self.assertEqual(result.status, CheckStatus.OK)


class TestBlockingSessionsChecker(unittest.TestCase):
    """Testes para BlockingSessionsChecker."""
    
    def test_no_locks_returns_ok(self):
        checker = BlockingSessionsChecker()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        result = checker.run(mock_conn)
        
        self.assertEqual(result.status, CheckStatus.OK)
        self.assertIn("Nenhuma", result.message)

    def test_locks_found_returns_critical(self):
        checker = BlockingSessionsChecker()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (100, 12345, "USER1", "ACTIVE", 99, "HR.EMPLOYEES")
        ]
        
        result = checker.run(mock_conn)
        
        self.assertEqual(result.status, CheckStatus.CRITICAL)
        self.assertIn("1 sessão", result.message)


class TestRMANStatusChecker(unittest.TestCase):
    """Testes para RMANStatusChecker."""
    
    def test_no_backups_returns_warning(self):
        checker = RMANStatusChecker()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        result = checker.run(mock_conn)
        
        self.assertEqual(result.status, CheckStatus.WARNING)


class TestTablespaceInfo(unittest.TestCase):
    """Testes para dataclass TablespaceInfo."""
    
    def test_critical_threshold(self):
        ts = TablespaceInfo(
            name="USERS", total_mb=1000, used_mb=960,
            free_mb=40, pct_used=96.0, file_name="/u01/data.dbf"
        )
        self.assertTrue(ts.is_critical)
        self.assertFalse(ts.is_warning)

    def test_warning_threshold(self):
        ts = TablespaceInfo(
            name="USERS", total_mb=1000, used_mb=900,
            free_mb=100, pct_used=90.0, file_name="/u01/data.dbf"
        )
        self.assertFalse(ts.is_critical)
        self.assertTrue(ts.is_warning)

    def test_resize_command(self):
        ts = TablespaceInfo(
            name="USERS", total_mb=1000, used_mb=900,
            free_mb=100, pct_used=90.0, file_name="/u01/data.dbf"
        )
        cmd = ts.get_resize_command(add_mb=1024)
        self.assertIn("ALTER DATABASE DATAFILE", cmd)
        self.assertIn("2024M", cmd)


class TestPartitionInfo(unittest.TestCase):
    """Testes para dataclass PartitionInfo."""
    
    def test_create_partition_info(self):
        info = PartitionInfo(
            owner="HR",
            table_name="EMPLOYEES",
            high_value_date=datetime(2026, 6, 1),
            is_interval=False,
            days_ahead=120
        )
        self.assertEqual(info.owner, "HR")
        self.assertEqual(info.days_ahead, 120)


class TestPartitionChecker(unittest.TestCase):
    """Testes para PartitionChecker."""
    
    def test_parse_high_value_iso_datetime(self):
        result = PartitionChecker.parse_high_value(
            "TO_DATE(' 2026-06-01 00:00:00', 'SYYYY-MM-DD HH24:MI:SS')"
        )
        self.assertEqual(result, datetime(2026, 6, 1, 0, 0, 0))

    def test_parse_high_value_iso_date(self):
        result = PartitionChecker.parse_high_value(
            "TO_DATE(' 2026-06-01', 'SYYYY-MM-DD')"
        )
        self.assertEqual(result, datetime(2026, 6, 1))

    def test_parse_high_value_invalid(self):
        result = PartitionChecker.parse_high_value("MAXVALUE")
        self.assertIsNone(result)


class TestOracleHome(unittest.TestCase):
    """Testes para dataclass OracleHome."""
    
    def test_display_name(self):
        home = OracleHome(
            name="OraDB19Home1",
            location=Path("/u01/app/oracle/product/19c"),
            is_removed=False
        )
        self.assertIn("OraDB19Home1", home.display_name)
        # Path pode usar \\ ou / dependendo do OS
        self.assertTrue("u01" in home.display_name or "19c" in home.display_name)


class TestServiceNameGenerator(unittest.TestCase):
    """Testes para generate_service_name."""
    
    def test_standard_format(self):
        result = generate_service_name("PIX", "PRD")
        self.assertEqual(result, "PIXSRVPRD")

    def test_lowercase_input(self):
        result = generate_service_name("api", "hg")
        self.assertEqual(result, "APISRVHG")


if __name__ == "__main__":
    unittest.main(verbosity=2)
